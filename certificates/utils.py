import os
import textwrap
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
from django.conf import settings

logger = logging.getLogger(__name__)

def generate_certificate_image(student, course_name, issue_date, certificate_number, skills=None):
    """
    Dynamically generate a styled certificate image and save it to MEDIA_ROOT/certificates/.
    Straight, uppercase gold-gradient name text. Pillow 10+ compatible. No cropping guaranteed.
    """
    try:
        # ✅ Paths
        template_path = os.path.join(settings.MEDIA_ROOT, "certificate_templates", "certificate_template.jpg")
        output_dir = os.path.join(settings.MEDIA_ROOT, "certificates")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Certificate template not found at {template_path}")
        os.makedirs(output_dir, exist_ok=True)

        # ✅ Load template
        img = Image.open(template_path).convert("RGBA")
        draw = ImageDraw.Draw(img)
        img_width, img_height = img.size

        # ✅ Font setup
        font_path = os.path.join(settings.BASE_DIR, "static", "fonts", "Montserrat-Bold.ttf")
        try:
            name_font = ImageFont.truetype(font_path, 150)
            skills_font = ImageFont.truetype(font_path, 100)
            course_font = ImageFont.truetype(font_path, 90)
            details_font = ImageFont.truetype(font_path, 80)
        except OSError:
            logger.warning("Custom font not found, using default system font.")
            name_font = skills_font = course_font = details_font = ImageFont.load_default()

        # ✅ Helper to center text
        def center_text(text, font, y, multiline=False):
            if multiline:
                bbox = draw.multiline_textbbox((0, 0), text, font=font, align="center")
            else:
                bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (img_width - text_width) / 2
            return x, y

        # ✅ Gradient text helper (with proper padding + baseline)
                # ✅ Gradient text helper (NO CROPPING, works with Montserrat)
        def draw_gradient_text(text, font, y, gradient_colors):
            """Draw centered gradient-filled text without cropping issues (Montserrat-safe)."""
            ascent, descent = font.getmetrics()
            (text_width, text_height) = font.getmask(text).size

            # Add generous padding around the text to avoid cropping
            pad_x = int(text_width * 0.1)
            pad_y = int(text_height * 0.4)
            canvas_width = text_width + pad_x * 2
            canvas_height = text_height + pad_y * 2

            # Create mask and draw text
            mask = Image.new("L", (canvas_width, canvas_height), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.text((pad_x, pad_y), text, font=font, fill=255)

            # Create gradient background
            gradient = Image.linear_gradient("L").resize((canvas_width, canvas_height))
            gradient = ImageOps.colorize(gradient, gradient_colors[0], gradient_colors[1])

            # Center horizontally on certificate
            x = (img_width - text_width) / 2

            # Paste gradient text (using mask)
            img.paste(gradient, (int(x - pad_x / 2), int(y - pad_y / 2)), mask)


        # ✅ Prepare text
        name_text = (student.name or student.username).upper()
        date_text = issue_date.strftime("%B %d, %Y")
        cert_text = f"Certificate No: {certificate_number}"

        wrapped_course_text = textwrap.fill(
            f"For successfully completing the {course_name} training, using ",
            width=75
        )

        wrapped_skills_text = None
        if skills:
            wrapped_skills_text = textwrap.fill(f"{skills}", width=95)

        # 🟡 Gradient name (straight + gold, no cropping)
        draw_gradient_text(
            name_text,
            name_font,
            1750,  # visually balanced for most templates
            gradient_colors=("#000000", "#000000"),
        )

        # 🟢 Optional skills
        if wrapped_skills_text:
            draw.multiline_text(
                center_text(wrapped_skills_text, skills_font, 2250, multiline=True),
                wrapped_skills_text,
                fill="#000000",
                font=skills_font,
                align="center"
            )

        # 🟦 Course text with gold & shadow
        course_x, course_y = center_text(wrapped_course_text, course_font, 2100, multiline=True)
        draw.multiline_text(
            (course_x + 2, course_y + 2),
            wrapped_course_text,
            fill="#333333",
            font=course_font,
            align="center"
        )
        draw.multiline_text(
            (course_x, course_y),
            wrapped_course_text,
            fill="#333333",
            font=course_font,
            align="center"
        )

        # 🔢 Certificate number
        draw.text(center_text(cert_text, details_font, 2750), cert_text, fill="#6b7280", font=details_font)

        # 🕓 Issue date
        date_x, date_y = 1150, 3100
        draw.text((date_x, date_y), date_text, fill="black", font=details_font)

        # ✅ Save output
        filename = f"{student.username}_certificate_{certificate_number}.png"
        output_path = os.path.join(output_dir, filename)
        img.save(output_path)

        logger.info(f"Certificate generated for {student.username}: {output_path}")
        return f"certificates/{filename}"

    except Exception as e:
        logger.error(f"Failed to generate certificate for {getattr(student, 'username', 'unknown')}: {e}")
        raise
