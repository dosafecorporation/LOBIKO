import requests
from lobikohealth import settings
import logging

logger = logging.getLogger(__name__)

# Configuration
VERIFY_TOKEN = settings.VERIFY_TOKEN
ACCESS_TOKEN = settings.ACCESS_TOKEN
PHONE_NUMBER_ID = settings.PHONE_NUMBER_ID

def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message}
    }
    try:
        resp = requests.post(url, json=data, headers=headers)
        resp.raise_for_status()
        logger.info(f"Message envoyé à {to}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur envoi message: {str(e)}")