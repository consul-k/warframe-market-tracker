import requests
import os
import logging

# Получаем токен из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN не задан в окружении")

API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# Настраиваем логирование (полезно для VPS)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_telegram_message(chat_id: int, text: str):
    """
    Отправляет сообщение пользователю Telegram.
    Использует parse_mode='HTML', чтобы можно было выделять текст <b>жирным</b>.
    """
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,  # чтобы ссылки не раздували сообщение
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"✅ Telegram message sent to {chat_id}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"⚠️ Ошибка при отправке сообщения Telegram: {e}")
        return None
