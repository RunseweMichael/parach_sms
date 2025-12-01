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

    # Top banner
    BANNER_HEIGHT = 2 * inch
    p.setFillColor(colors.HexColor("#FFFFFF"))
    p.rect(0, height - BANNER_HEIGHT, width, BANNER_HEIGHT, fill=True, stroke=False)

    # Define address configuration first
    p.setFont("Helvetica", 11)
    address_lines = [
        "Parach ICT Academy,",
        "Beside Odusote Bookshop,",
        "Samonda, Ibadan,",
        "Oyo State, Nigeria.",
        "+234 705 524 7562",
        "www.parachictacademy.com.ng"
    ]
    
    line_height = 13
    # Calculate total height of address block
    total_address_height = len(address_lines) * line_height
    
    # Position address to start vertically centered in banner
    address_x = 5.5 * inch  # Position for address text
    address_y = height - BANNER_HEIGHT + (BANNER_HEIGHT + total_address_height) / 2 - line_height

    # Left: Logo - aligned with first line of address
    try:
        logo_path = os.path.join(settings.MEDIA_ROOT, "logo.jpeg")
        if os.path.exists(logo_path):
            logo_image = ImageReader(logo_path)
            LOGO_WIDTH = 1.5 * inch
            LOGO_HEIGHT = 1.5 * inch
            
            # Position logo so its vertical center aligns with "Parach ICT Academy" text
            logo_x = 0.9 * inch
            # Align logo center with the first line of address (Parach ICT Academy)
            logo_y = address_y - (LOGO_HEIGHT / 2) + (line_height / 2)
            
            p.drawImage(
                logo_image,
                logo_x,
                logo_y,
                width=LOGO_WIDTH,
                height=LOGO_HEIGHT,
                preserveAspectRatio=True,
                mask='auto'
            )
        else:
            print("⚠️ Logo not found:", logo_path)
    except Exception as e:
        print("Error loading logo:", repr(e))

    # Draw address lines
    p.setFillColor(colors.black)
    for line in address_lines:
        p.drawString(address_x, address_y, line)
        address_y -= line_height

    # =====================================================================
    #  UNDERLINE TITLE (with increased spacing from banner)
    # =====================================================================
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 16)
    title_y = height - BANNER_HEIGHT - 0.1 * inch  # Increased space below banner
    p.drawString(1 * inch, title_y, "Internship Offer Letter")
    p.setStrokeColor(colors.lightgrey)
    p.setLineWidth(1)
    p.line(1 * inch, title_y - 0.05 * inch, width - 1 * inch, title_y - 0.05 * inch)

    # =====================================================================
    #  DATE & RECIPIENT
    # =====================================================================
    today = datetime.date.today().strftime("%B %d, %Y")
    p.setFont("Helvetica", 12)
    p.drawString(1 * inch, title_y - 0.5 * inch, f"Date: {today}")

    p.drawString(1 * inch, title_y - 1 * inch, f"To: {request_obj.student_name}")
    p.drawString(1 * inch, title_y - 1.3 * inch, f"Email: {request_obj.student_email}")

    # =====================================================================
    #  BODY CONTENT
    # =====================================================================
    body_y = title_y - 2 * inch
    line_spacing = 16

    intro = [
        f"Dear {request_obj.student_name},",
        "",
        "We are pleased to extend this official internship offer to you from Parach ICT Academy.",
        f"Your internship will begin on {request_obj.preferred_start_date} and run for a duration of {request_obj.duration}.",
        "This program will expose you to hands-on experience in productivity tools,",
        "team collaboration, and other essential IT skills.",
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
        "   1. The internship is unpaid.",
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
        "Busayo,",
        "Manager.",
    ]

    # ---- Write body text ----
    p.setFont("Helvetica", 12)
    y = body_y

    for section in [intro, expectations, policies, closing]:
        for line in section:
            p.drawString(1 * inch, y, line)
            y -= line_spacing
        y -= line_spacing

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer.getvalue()