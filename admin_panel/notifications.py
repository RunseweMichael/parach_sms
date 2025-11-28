from django.conf import settings
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

