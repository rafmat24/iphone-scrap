import asyncio
import json
import os
import random
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import configuration from a separate file
from config import PRODUCTS_CONFIG, HISTORY_FILE


def parse_selected_product_names():
    if len(sys.argv) > 1:
        requested = [arg.strip() for arg in sys.argv[1:] if arg.strip()]
        if any(arg.lower() == "all" for arg in requested):
            return list(PRODUCTS_CONFIG.keys())
        return requested

    env_products = os.getenv("PRODUCTS")
    if env_products:
        requested = [name.strip() for name in env_products.split(",") if name.strip()]
        if any(name.lower() == "all" for name in requested):
            return list(PRODUCTS_CONFIG.keys())
        return requested

    return list(PRODUCTS_CONFIG.keys())


def resolve_product_names(requested_products):
    available = {name.lower(): name for name in PRODUCTS_CONFIG}
    selected = []

    for requested in requested_products:
        key = requested.lower()
        if key in available:
            selected.append(available[key])
            continue

        matches = [name for name in PRODUCTS_CONFIG if key in name.lower()]
        if len(matches) == 1:
            selected.append(matches[0])
        elif len(matches) == 0:
            raise ValueError(
                f"No product found matching '{requested}'. "
                f"Available products: {', '.join(PRODUCTS_CONFIG.keys())}"
            )
        else:
            raise ValueError(
                f"Name '{requested}' matches multiple products: {', '.join(matches)}. "
                "Use the full product name."
            )

    return selected


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_history(current_prices):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(current_prices, f, indent=4, ensure_ascii=False)


def send_email_report(current_prices, previous_prices, selected_products):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 465))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")

    if not all([smtp_server, smtp_user, smtp_password, recipient_email]):
        print("[EMAIL] Missing SMTP config in GitHub Secrets. Skipping email.")
        return

    subject = "📊 Price report"
    if len(selected_products) == 1:
        subject = f"📊 Price report: {selected_products[0]}"
    else:
        subject = f"📊 Price report: {', '.join(selected_products)}"

    html_content = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>Daily price report</h2>
    """

    any_changes = False
    for product in selected_products:
        html_content += f"<h3>{product}</h3>"
        html_content += """
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; max-width: 600px;">
            <tr style="background-color: #f2f2f2;">
                <th align="left">Store</th>
                <th align="left">Current price</th>
                <th align="left">Status / Change</th>
                <th align="left">Link</th>
            </tr>
        """

        product_prices = current_prices.get(product, {})
        previous_product_prices = previous_prices.get(product, {}) if isinstance(previous_prices.get(product), dict) else {}

        for store, info in PRODUCTS_CONFIG[product].items():
            price = product_prices.get(store)
            prev_price = previous_product_prices.get(store)
            store_url = info.get("url", "")

            if price is None:
                price_text = "Fetch error"
                status_text = "<span style='color: gray;'>-</span>"
            else:
                price_text = f"{price:.2f} PLN"
                if prev_price is None:
                    status_text = "<span style='color: blue;'>First check</span>"
                elif price < prev_price:
                    any_changes = True
                    diff = prev_price - price
                    status_text = f"<span style='color: green; font-weight: bold;'>DROP (↓ {diff:.2f} PLN)</span>"
                elif price > prev_price:
                    any_changes = True
                    diff = price - prev_price
                    status_text = f"<span style='color: red;'>RISE (↑ {diff:.2f} PLN)</span>"
                else:
                    status_text = "<span style='color: #666;'>No change</span>"

            if store_url:
                link_text = f"<a href='{store_url}' target='_blank' rel='noopener noreferrer'>View offer</a>"
            else:
                link_text = "-"

            html_content += f"""
            <tr>
                <td><strong>{store}</strong></td>
                <td>{price_text}</td>
                <td>{status_text}</td>
                <td>{link_text}</td>
            </tr>
            """

        html_content += "</table><br>"

    if any_changes:
        html_content += "<p style='color: #d9534f; font-weight: bold;'>⚠️ Price change detected in at least one store!</p>"
    else:
        html_content += "<p style='color: #5cb85c;'>All prices stable since last check.</p>"

    html_content += """
        <p style="font-size: 11px; color: #999;">Message generated automatically by GitHub Actions.</p>
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
        print("[EMAIL] Email report sent successfully!")
    except Exception as e:
        print(f"[EMAIL] Email sending error: {e}")


async def main():
    print("Starting price check...")
    requested_products = parse_selected_product_names()
    try:
        selected_products = resolve_product_names(requested_products)
    except ValueError as error:
        print(error)
        sys.exit(1)

    print(f"Selected products: {', '.join(selected_products)}")

    previous_prices = load_history()
    current_prices = {product: {} for product in selected_products}

    for product in selected_products:
        print(f"\n=== Product: {product} ===")
        for store, info in PRODUCTS_CONFIG[product].items():
            if "PASTE_HERE" in info["url"]:
                print(f"Skipped {store} - URL not configured.")
                continue

            print(f"Checking {store}...")
            scraper = info["class"](store, info["url"], **info.get("args", {}))
            price = await scraper.scrape_price()

            if price:
                current_prices[product][store] = price

            wait_time = random.uniform(4.0, 8.0)
            await asyncio.sleep(wait_time)

    save_history(current_prices)
    send_email_report(current_prices, previous_prices, selected_products)


if __name__ == "__main__":
    asyncio.run(main())
