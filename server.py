from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
import re
import threading
import time

import firebase_admin
from firebase_admin import credentials, messaging

app = Flask(__name__)

import os
import json

firebase_key = json.loads(
    os.environ["FIREBASE_KEY"]
)

cred = credentials.Certificate(firebase_key)

firebase_admin.initialize_app(cred)

CHANNEL_URL = "https://t.me/s/sirena_dp"

FCM_TOKEN = "dwBDUMhOTt6dmMOGUe6shM:APA91bF-M3Mz-eW4rLx5SPgaSCX824fJy6whZx3H5v9c8FJWCQPsFI7StZMeB86gwFDzzVoWIvERiycXznitsMTEIr53DoT9r5XUw-va4kDt5c7I-Wf9ems"

last_alert = None


def send_push(token, title, body):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
    )

    response = messaging.send(message)
    print(response)


def kyiv_time():
    return datetime.now(ZoneInfo("Europe/Kyiv")).strftime("%H:%M:%S")


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
            "updated": kyiv_time()
        }

    except requests.exceptions.RequestException:
        return {
            "alert": None,
            "online": False,
            "error": "Немає з'єднання з Telegram",
            "updated": kyiv_time()
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
            "updated": kyiv_time()
        }

    text = messages[-1].text.strip()

    return {
        "alert": parse_alert(text),
        "message": text,
        "alert_time": get_alert_time(text),
        "updated": kyiv_time(),
        "online": True,
        "error": None
    }


def monitor_alerts():

    global last_alert

    while True:

        start = time.time()

        data = get_alert_status()

        print(f"[{kyiv_time()}] alert = {data['alert']}")

        if data["online"] and data["alert"] is not None:

            current = data["alert"]

            if last_alert is None:
                last_alert = current

            elif current != last_alert:

                if current:

                    send_push(
                        FCM_TOKEN,
                        "🚨 Повітряна тривога",
                        "У Дніпрі оголошено повітряну тривогу"
                    )

                else:

                    send_push(
                        FCM_TOKEN,
                        "✅ Відбій",
                        "У Дніпрі відбій повітряної тривоги"
                    )

                last_alert = current

        elapsed = time.time() - start
        time.sleep(max(0, 10 - elapsed))


@app.route("/test_push")
def test_push():

    send_push(
        FCM_TOKEN,
        "🚨 Повітряна тривога",
        "Тестове повідомлення"
    )

    return "Push sent"

@app.route("/")
def home():
    return "Air Alert Server is running"


@app.route("/status")
def status():
    return jsonify(get_alert_status())

if __name__ == "__main__":

    threading.Thread(
        target=monitor_alerts,
        daemon=True
    ).start()

    app.run(
        host="0.0.0.0",
        port=5000
    )