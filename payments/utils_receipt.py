import os
import json
from decimal import Decimal
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from django.conf import settings
from .models import PaymentReceipt


def generate_receipt_pdf(transaction):
    """
    Generate a premium PDF receipt including discount info (if applied).
    """
    receipt_dir = os.path.join(settings.MEDIA_ROOT, "receipts")
    os.makedirs(receipt_dir, exist_ok=True)

    file_path = os.path.join(receipt_dir, f"{transaction.reference}.pdf")
    relative_path = f"receipts/{transaction.reference}.pdf"

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    # -------------------
    # Company Logo
    # -------------------
    logo_path = os.path.join(settings.MEDIA_ROOT, "images", "parach.jpg")
    if os.path.exists(logo_path):
        try:
            logo = ImageReader(logo_path)
            c.drawImage(
                logo,
                width - 150,
                height - 100,
                width=100,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception as e:
            print(f"⚠️ Could not add logo: {e}")

    # -------------------
    # Title
    # -------------------
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 120, "Payment Receipt")

    # -------------------
    # Transaction Details
    # -------------------
    c.setFont("Helvetica", 14)
    y = height - 160
    line_gap = 25

    # ✅ Safely parse metadata (handles both string or dict)
    metadata = transaction.metadata
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}
    elif not isinstance(metadata, dict):
        metadata = {}

    discount_applied = Decimal(str(metadata.get("discount_applied", 0))) if metadata else Decimal("0.00")
    coupon_code = metadata.get("coupon_code") if metadata else None

    # Main details
    details = [
        ("Reference", transaction.reference),
        ("Name", getattr(transaction.user, "name", "N/A")),
        ("Email", getattr(transaction.user, "email", "N/A")),
        ("Course", getattr(getattr(transaction.user, "course", None), "course_name", "N/A")),
        ("Amount Paid", f"₦{float(transaction.amount):,.2f}"),
        ("Date", (transaction.paid_at or transaction.created_at).strftime("%Y-%m-%d %H:%M")),
        ("Status", getattr(transaction, "status", "Success").capitalize()),
    ]

    # Draw details
    for label, value in details:
        c.drawString(70, y, f"{label}: {value}")
        y -= line_gap

    # ✅ Add discount info if applicable
    if discount_applied > 0:
        c.drawString(70, y, f"Discount Applied: ₦{float(discount_applied):,.2f}")
        y -= line_gap

    if coupon_code:
        c.drawString(70, y, f"Coupon Code: {coupon_code}")
        y -= line_gap

    # -------------------
    # Footer
    # -------------------
    c.setFont("Helvetica-Oblique", 12)
    c.drawCentredString(width / 2, 80, "Thank you for choosing Parach ICT Academy!")

    # -------------------
    # Save PDF
    # -------------------
    c.showPage()
    c.save()

    # Save or update receipt record in DB
    PaymentReceipt.objects.update_or_create(
        transaction=transaction, defaults={"pdf_file": relative_path}
    )

    return relative_path
