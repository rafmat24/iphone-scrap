import asyncio
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Importujemy konfigurację z osobnego pliku
from config import PRODUCTS_CONFIG, HISTORY_FILE

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(current_prices):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(current_prices, f, indent=4, ensure_ascii=False)

def send_email_report(current_prices, previous_prices):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 465))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")

    if not all([smtp_server, smtp_user, smtp_password, recipient_email]):
        print("[EMAIL] Brak konfiguracji SMTP w GitHub Secrets. Pomijam wysyłkę.")
        return

    subject = "📊 Raport cen: iPhone 17 Pro 512GB Silver"
    
    html_content = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>Dzienny raport cenowy</h2>
        <p>Oto aktualne ceny dla modelu <strong>iPhone 17 Pro Silver 512GB</strong>:</p>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; max-width: 600px;">
            <tr style="background-color: #f2f2f2;">
                <th align="left">Sklep</th>
                <th align="left">Aktualna cena</th>
                <th align="left">Status / Zmiana</th>
            </tr>
    """

    any_changes = False

    for store in PRODUCTS_CONFIG.keys():
        price = current_prices.get(store)
        prev_price = previous_prices.get(store)

        if price is None:
            price_text = "Błąd pobierania"
            status_text = "<span style='color: gray;'>-</span>"
        else:
            price_text = f"{price:.2f} PLN"
            
            if prev_price is None:
                status_text = "<span style='color: blue;'>Pierwszy pomiar</span>"
            elif price < prev_price:
                any_changes = True
                diff = prev_price - price
                status_text = f"<span style='color: green; font-weight: bold;'>SPADEK (↓ {diff:.2f} PLN)</span>"
            elif price > prev_price:
                any_changes = True
                diff = price - prev_price
                status_text = f"<span style='color: red;'>WZROST (↑ {diff:.2f} PLN)</span>"
            else:
                status_text = "<span style='color: #666;'>Bez zmian</span>"

        html_content += f"""
            <tr>
                <td><strong>{store}</strong></td>
                <td>{price_text}</td>
                <td>{status_text}</td>
            </tr>
        """

    html_content += "</table><br>"

    if any_changes:
        subject = "🔔 [ZMIANA CENY] " + subject
        html_content += "<p style='color: #d9534f; font-weight: bold;'>⚠️ Wykryto zmianę ceny w co najmniej jednym sklepie!</p>"
    else:
        html_content += "<p style='color: #5cb85c;'>Wszystkie ceny stabilne od wczoraj.</p>"

    html_content += """
        <p style="font-size: 11px; color: #999;">Wiadomość wygenerowana automatycznie przez GitHub Actions.</p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipient_email, msg.as_string())
        print("[EMAIL] Raport wysłany pomyślnie!")
    except Exception as e:
        print(f"[EMAIL] Błąd podczas wysyłania: {e}")

async def main():
    print("Rozpoczęcie sprawdzania cen...")
    previous_prices = load_history()
    current_prices = {}

    for store, info in PRODUCTS_CONFIG.items():
        if "TUTAJ_WKLEJ" in info["url"]:
            print(f"Pominięto {store} - brak skonfigurowanego URL.")
            continue

        print(f"Sprawdzam {store}...")
        scraper = info["class"](store, info["url"], **info["args"])
        price = await scraper.scrape_price()
        
        if price:
            current_prices[store] = price
            
        await asyncio.sleep(3) 

    save_history(current_prices)
    send_email_report(current_prices, previous_prices)

if __name__ == "__main__":
    asyncio.run(main())