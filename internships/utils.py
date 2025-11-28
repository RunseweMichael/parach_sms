from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from django.conf import settings
import io
import datetime
import os

def generate_internship_pdf(request_obj):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # =====================================================================
    #  TOP BANNER
    # =====================================================================
    p.setFillColor(colors.HexColor("#0B3D91"))
    p.rect(0, height - 0.8 * inch, width, 0.8 * inch, fill=True, stroke=False)

    # =====================================================================
    #  LOGO IN BANNER
    # =====================================================================
    try:
        logo_path = os.path.join(settings.BASE_DIR, "static/images/parach.png")

        if os.path.exists(logo_path):
            logo_image = ImageReader(logo_path)

            LOGO_WIDTH = 0.55 * inch
            LOGO_HEIGHT = 0.55 * inch

            logo_y = height - 0.8 * inch + (0.8 * inch - LOGO_HEIGHT) / 2

            p.drawImage(
                logo_image,
                0.4 * inch,
                logo_y,
                width=LOGO_WIDTH,
                height=LOGO_HEIGHT,
                preserveAspectRatio=True,
                mask="auto",
            )
    except Exception as e:
        print("Error loading logo:", repr(e))

    # =====================================================================
    #  HEADER TEXT
    # =====================================================================
    p.setFont("Helvetica-Bold", 20)
    p.setFillColor(colors.white)
    p.drawString(1.45 * inch, height - 0.52 * inch, "Parach ICT Academy")

    # =====================================================================
    #  UNDERLINE TITLE
    # =====================================================================
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(1 * inch, height - 1.5 * inch, "Internship Offer Letter")
    p.setStrokeColor(colors.lightgrey)
    p.setLineWidth(1)
    p.line(1 * inch, height - 1.55 * inch, width - 1 * inch, height - 1.55 * inch)

    # =====================================================================
    #  DATE & RECIPIENT
    # =====================================================================
    today = datetime.date.today().strftime("%B %d, %Y")
    p.setFont("Helvetica", 12)
    p.drawString(1 * inch, height - 2 * inch, f"Date: {today}")

    p.drawString(1 * inch, height - 2.5 * inch, f"To: {request_obj.student_name}")
    p.drawString(1 * inch, height - 2.8 * inch, f"Email: {request_obj.student_email}")

    # =====================================================================
    #  BODY CONTENT
    # =====================================================================
    body_y = height - 3.5 * inch
    line_spacing = 16

    intro = [
        f"Dear {request_obj.student_name},",
        "",
        "We are pleased to extend this official internship offer to you from Parach ICT Academy.",
        f"Your internship will begin on {request_obj.preferred_start_date} and run for a duration of {request_obj.duration}.",
        "This program will expose you to hands-on experience in software development,",
        "productivity tools, team collaboration, and other essential IT skills.",
    ]

    expectations = [
        "",
        "Internship Expectations:",
        "   • Receive mentorship from experienced professionals.",
        "   • Work on meaningful, skill-building real-world projects.",
        "   • Participate in weekly reviews and team meetings.",
        "   • Access training resources and development tools.",
    ]

    policies = [
        "",
        "Key Guidelines:",
        "   1. The internship may be unpaid or stipended, as discussed.",
        "   2. Professional conduct and adherence to academy policies are required.",
        "   3. Timely submission of tasks and weekly reports is expected.",
    ]

    closing = [
        "",
        "We are confident that your commitment and passion will make you a valuable member",
        "of our growing tech community. We look forward to supporting your learning and",
        "professional development throughout this internship experience.",
        "",
        "Warm regards,",
        "",
        "Parach ICT Academy Team",
        "Website: www.parachictacademy.com.ng",
        "Phone: +234 705 524 7562",
    ]

    # ---- Write body text ----
    p.setFont("Helvetica", 12)
    y = body_y

    for section in [intro, expectations, policies, closing]:
        for line in section:
            p.drawString(1 * inch, y, line)
            y -= line_spacing
        y -= line_spacing

    # =====================================================================
    #  FOOTER BAR
    # =====================================================================
    p.setFillColor(colors.HexColor("#0B3D91"))
    p.rect(0, 0, width, 0.5 * inch, fill=True, stroke=False)

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.white)
    p.drawCentredString(
        width / 2,
        0.2 * inch,
        "Parach ICT Academy • Empowering the Next Generation of Tech Innovators"
    )

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer.getvalue()
