import requests
from bs4 import BeautifulSoup

url = "https://t.me/s/sirena_dp"

response = requests.get(url)

print("Статус:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

messages = soup.find_all("div", class_="tgme_widget_message_text")

if messages:
    text = messages[-1].text
    print(text)

    if "ВІДБІЙ" in text:
        print("СТАН: Немає тривоги")

    elif "ТРИВОГА" in text:
        print("СТАН: Є ТРИВОГА")

    else:
        print("СТАН: Не зрозуміло")