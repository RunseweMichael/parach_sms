import os
import json
from decimal import Decimal
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from django.conf import settings
from .models import PaymentReceipt
from django.utils import timezone
import requests

# -----------------------------
# Register Unicode-friendly font
# -----------------------------
font_path = os.path.join(settings.BASE_DIR, 'fonts', 'DejaVuSans.ttf')
pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

# -----------------------------
# Custom SimpleDocTemplate for background color
# -----------------------------
class ColoredBackgroundDocTemplate(SimpleDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        self.page_background_color = colors.HexColor("#001F5B")  # deep blue  ##001F5B

    def beforePage(self):
        c: canvas.Canvas = self.canv
        c.saveState()
        c.setFillColor(self.page_background_color)
        c.rect(0, 0, self.pagesize[0], self.pagesize[1], fill=1, stroke=0)
        c.restoreState()

def generate_receipt_pdf(transaction):
    receipt_dir = os.path.join(settings.MEDIA_ROOT, "receipts")
    os.makedirs(receipt_dir, exist_ok=True)
    file_path = os.path.join(receipt_dir, f"{transaction.reference}.pdf")
    relative_path = f"receipts/{transaction.reference}.pdf"

    # -----------------------------
    # Styles
    # -----------------------------
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Heading1"], alignment=0, fontSize=40,
                                 textColor=colors.white, fontName="DejaVuSans", spaceAfter=5)
    subtitle_style = ParagraphStyle("subtitle", parent=styles["Heading2"], alignment=0, fontSize=20,
                                    textColor=colors.white, fontName="DejaVuSans", spaceAfter=10)
    section_header_style = ParagraphStyle("section_header", parent=styles["Heading2"], fontSize=12,
                                          textColor=colors.white, fontName="DejaVuSans",
                                          spaceBefore=12, spaceAfter=8)
    label_style = ParagraphStyle("label", parent=styles["Normal"], fontName="DejaVuSans", fontSize=11,
                                 textColor=colors.white, spaceAfter=4)
    footer_style = ParagraphStyle("footer", parent=styles["Normal"], alignment=1, fontName="DejaVuSans",
                                  fontSize=10, textColor=colors.white, spaceBefore=25)

    # -----------------------------
    # Document
    # -----------------------------
    doc = ColoredBackgroundDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=60,
        leftMargin=60,
        topMargin=60,
        bottomMargin=60,
    )

    elements = []

    # -----------------------------
    # Download logo
    # -----------------------------
    logo_url = "https://parachictacademy.com.ng/wp-content/uploads/2019/08/Parach-computers-ibadan-logo-1-e1565984209812.png"

    try:
        response = requests.get(logo_url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            logo_path = os.path.join(settings.MEDIA_ROOT, "logo_temp.png")
            with open(logo_path, "wb") as f:
                f.write(response.content)

            # -----------------------------
            # Logo + ICT Academy
            # -----------------------------
            logo_img = Image(logo_path, width=200, height=80)
            logo_text_table = Table(
                [
                    [logo_img],  # row 0: logo
                    [Paragraph("ICT Academy", subtitle_style)]  # row 1: ICT Academy directly under
                ],
                colWidths=[200],
                hAlign='LEFT'
            )
            logo_text_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#001F5B"))
            ]))
            elements.append(logo_text_table)
            elements.append(Spacer(1, 15))
        else:
            print("Logo download failed:", response.status_code)
    except Exception as e:
        print("Logo download error:", e)

    # -----------------------------
    # Header Text
    # -----------------------------
    elements.append(HRFlowable(width="80%", thickness=1, color=colors.white, spaceBefore=8, spaceAfter=25))
    elements.append(Paragraph("<b>OFFICIAL PAYMENT RECEIPT</b>", section_header_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        "This document confirms that the payment below has been successfully received. "
        "Please keep this receipt for your records.", label_style
    ))
    elements.append(Spacer(1, 12))

    # -----------------------------
    # Transaction Metadata
    # -----------------------------
    metadata = transaction.metadata
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except:
            metadata = {}

    discount = Decimal(str(metadata.get("discount_applied", 0)))
    coupon = metadata.get("coupon_code")

    data = [
        ["Student Name:", getattr(transaction.user, "name", "N/A")],
        ["Course:", getattr(getattr(transaction.user, "course", None), "course_name", "N/A")],
        ["Transaction Reference:", transaction.reference],
        ["Amount Paid:", f"₦{Decimal(transaction.amount):,.2f}"],
        ["Payment Status:", str(transaction.status).title()],
        ["Date & Time:", (transaction.paid_at or timezone.now()).strftime("%d/%m/%Y, %H:%M:%S")],
    ]

    if getattr(transaction.user, "next_due_date", None):
        data.append(["Next Due Date:", transaction.user.next_due_date.strftime("%d/%m/%Y")])

    if discount > 0:
        data.append(["Discount Applied:", f"₦{discount:,.2f}"])
    if coupon:
        data.append(["Coupon Code:", coupon])

    table = Table(data, colWidths=[180, 320], hAlign='CENTER')
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3954")),  # Student Name row blue
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#AAAAAA")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDDDDD")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 25))

    # -----------------------------
    # Thank You Note
    # -----------------------------
    elements.append(Paragraph(
        "We sincerely thank you for your commitment to learning with Parach ICT Academy. "
        "Your investment in your education helps us continue to provide top-quality digital training across Africa.",
        label_style
    ))
    elements.append(Spacer(1, 15))

    # -----------------------------
    # Footer
    # -----------------------------
    footer_text = """
    <b>Parach ICT Academy</b><br/>
    www.parachictacademy.com.ng<br/>
    """
    elements.append(HRFlowable(width="80%", thickness=0.5, color=colors.white, spaceBefore=12, spaceAfter=12))
    elements.append(Paragraph(footer_text, footer_style))

    # -----------------------------
    # Build PDF
    # -----------------------------
    doc.build(elements)

    # -----------------------------
    # Save to DB
    # -----------------------------
    PaymentReceipt.objects.update_or_create(
        transaction=transaction,
        defaults={"pdf_file": relative_path},
    )

    print("🔥 PREMIUM RECEIPT GENERATED WITH LOGO")
    return relative_path
