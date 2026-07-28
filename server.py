from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

app = Flask(__name__)

CHANNEL_URL = "https://t.me/s/sirena_dp"


def parse_alert(text):
    if "ВІДБІЙ ТРИВОГИ" in text:
        return False

    if "Оголошено тривогу" in text:
        return True

    return None


def get_alert_time(text):
    match = re.search(r"(\d{1,2}:\d{2})", text)

    if match:
        return match.group(1)

    return None


def get_alert_status():

    try:
        response = requests.get(
            CHANNEL_URL,
            timeout=10
        )

        response.raise_for_status()

    except requests.exceptions.Timeout:
        return {
            "alert": None,
            "online": False,
            "error": "Час очікування Telegram вичерпано",
            "updated": datetime.now().strftime("%H:%M:%S")
        }

    except requests.exceptions.RequestException:
        return {
            "alert": None,
            "online": False,
            "error": "Немає з'єднання з Telegram",
            "updated": datetime.now().strftime("%H:%M:%S")
        }


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    messages = soup.find_all(
        "div",
        class_="tgme_widget_message_text"
    )


    if not messages:
        return {
            "alert": None,
            "online": False,
            "error": "Повідомлення не знайдені",
            "updated": datetime.now().strftime("%H:%M:%S")
        }


    text = messages[-1].text.strip()


    return {
        "alert": parse_alert(text),
        "message": text,
        "alert_time": get_alert_time(text),
        "updated": datetime.now().strftime("%H:%M:%S"),
        "online": True,
        "error": None
    }

@app.route("/")
def home():
    return "Air Alert Server is running"

@app.route("/status")
def status():
    return jsonify(get_alert_status())


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )