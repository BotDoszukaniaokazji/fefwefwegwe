
import requests
import time
import json
import os
from bs4 import BeautifulSoup

# Wczytaj cennik z pliku
with open('cennik.json', 'r', encoding='utf-8') as f:
    cennik = json.load(f)

WEBHOOK_OKAZJE = os.getenv('WEBHOOK_OKAZJE')
WEBHOOK_STRATA = os.getenv('WEBHOOK_STRATA')

# Funkcja pomocnicza do wysyłania webhooka
def send_webhook(url, embed):
    data = {"embeds": [embed]}
    response = requests.post(url, json=data)
    if response.status_code != 204:
        print(f'Błąd webhooka: {response.status_code} - {response.text}')

# Funkcja parsująca ogłoszenie z OLX
def parse_listing(listing_url):
    try:
        response = requests.get(listing_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Przykład parsowania (dostosować do aktualnego OLX)
        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else "Brak tytułu"
        
        price_tag = soup.find('h3', class_='css-12vqlj3')
        price = int(price_tag.text.replace('zł','').replace(' ', '').strip()) if price_tag else 0

        location_tag = soup.find('p', class_='css-7xdcwc')
        location = location_tag.text.strip() if location_tag else "Brak lokalizacji"

        # Dopasowanie ceny z cennika
        recommended_price = 0
        for model in cennik:
            if model.lower() in title.lower():
                recommended_price = cennik[model]
                break

        zysk = recommended_price - price
        kolor = 0x00FF00 if zysk > 0 else 0xFF0000
        status = "OKAZJA!" if zysk > 0 else "STRATA"

        embed = {
            "title": title,
            "url": listing_url,
            "color": kolor,
            "fields": [
                {"name": "Cena w ogłoszeniu", "value": f"{price} zł", "inline": True},
                {"name": "Rekomendowana cena", "value": f"{recommended_price} zł", "inline": True},
                {"name": "Status", "value": f"{status} {abs(zysk)} zł", "inline": False},
                {"name": "Lokalizacja", "value": location, "inline": True}
            ]
        }

        if zysk > 0:
            send_webhook(WEBHOOK_OKAZJE, embed)
        else:
            send_webhook(WEBHOOK_STRATA, embed)

    except Exception as e:
        print(f'Błąd podczas parsowania {listing_url}: {e}')

# Główna pętla bota
def main():
    print("Bot wystartował!")
    seen_links = set()

    while True:
        try:
            url = 'https://www.olx.pl/elektronika/telefony/smartfony-telefony-komorkowe/q-Iphone/?courier=1&search%5Border%5D=created_at:desc'
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Znajdź wszystkie linki do ogłoszeń (przykład - dopasować do aktualnego OLX)
            listings = soup.find_all('a', class_='css-rc5s2u')

            for listing in listings:
                listing_url = listing['href']
                if not listing_url.startswith('https'):
                    listing_url = 'https://www.olx.pl' + listing_url

                if listing_url not in seen_links:
                    seen_links.add(listing_url)
                    parse_listing(listing_url)

            time.sleep(1)

        except Exception as e:
            print(f'Błąd głównej pętli: {e}')
            time.sleep(5)

if __name__ == '__main__':
    main()
