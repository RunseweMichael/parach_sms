from django.conf import settings
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

def format_phone_number(number):
    """Convert Nigerian numbers like 09077781075 to +2349077781075"""
    number = number.strip()
    if number.startswith("0"):
        number = "+234" + number[1:]
    elif not number.startswith("+"):
        number = "+" + number
    return number

def send_whatsapp_message(to_number, message):
    """
    Send a WhatsApp message using Twilio API.
    `to_number` should include country code, e.g., '+1234567890'
    """
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    try:
        msg = client.messages.create(
            body=message,
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_number}"
        )
        logger.info(f"WhatsApp sent to {to_number}: SID {msg.sid}")
        return True, msg.sid
    except Exception as e:
        logger.error(f"WhatsApp failed for {to_number}: {e}")
        return False, str(e)