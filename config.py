from scrapers.stores import StandardScraper, SplitPriceScraper, AriaPriceScraper

HISTORY_FILE = "prices_history.json"

# --- Selector notes (updated after live DOM inspection) -------------------
# X-Kom & Neonet run the same storefront platform (identical hashed class
#   names), so they share the same selector strategy: a hidden screen-reader
#   span with the full price as plain text in its `aria-label`.
# Morele: the product id changed from #product_price_brutto -> #product_price.
#   It also exposes a clean numeric `data-price` attribute, which we use
#   instead of parsing the visible text.
# Komputronik: price now lives in a node tagged data-price-type="final"
#   (there are decoy price blocks for color-variant cards elsewhere on the
#   page, so we deliberately scope to this attribute rather than a class).
# MediaExpert: the page legitimately renders the price TWICE (main block +
#   a duplicate, e.g. sticky bar). We keep SplitPriceScraper but the class
#   now grabs the first match explicitly via .first in the scraper itself.
# MediaMarkt: now uses `data-test` attributes (QA-oriented, more stable than
#   the hashed `mms-ui-*` / `sc-*` CSS classes) for whole/decimal price parts.
# Euro RTV AGD: NOT a selector problem. The site's WAF hard-blocks GitHub
#   Actions' IP range outright ("Twoje żądanie zostało zablokowane") before
#   any page content loads. No selector will fix this — see README/notes
#   for mitigation options (proxy, alternate runner, or drop this store).
# ---------------------------------------------------------------------------

PRODUCTS_CONFIG = {
    "X-Kom": {
        "class": AriaPriceScraper,
        "url": "https://www.x-kom.pl/p/1362361-smartfon-telefon-apple-iphone-17-pro-512gb-srebrny.html",
        "args": {"selector": "[data-name='productPrice'] span[aria-label^='Cena:']"}
    },
    "Morele": {
        "class": StandardScraper,
        "url": "https://www.morele.net/smartfon-apple-iphone-17-pro-5g-12-512gb-srebrny-mg8k4ql-a-15662750/",
        "args": {"selector": "#product_price"}
    },
    "Komputronik": {
        "class": StandardScraper,
        "url": "https://www.komputronik.pl/product/983042/telefon-apple-iphone-17-pro-512gb-srebrny.html",
        "args": {"selector": "div[data-price-type='final']"}
    },
    "Neonet": {
        "class": AriaPriceScraper,
        "url": "https://www.neonet.pl/p/1362361-smartfon-apple-iphone-17-pro-512gb-srebrny.html",
        "args": {"selector": "[data-name='productPrice'] span[aria-label^='Cena:']"}
    },
    "MediaExpert": {
        "class": SplitPriceScraper,
        "url": "https://www.mediaexpert.pl/smartfony-i-zegarki/smartfony/smartfon-apple-iphone-17-pro-5g-silver-512gb",
        "args": {"main_selector": "div.main-price[aria-label] span.whole", "cents_selector": "div.main-price[aria-label] span.cents"}
    },
    "Euro RTV AGD": {
        "class": SplitPriceScraper,
        "url": "https://www.euro.com.pl/telefony-komorkowe/apple-iphone-17-pro-512gb-srebrny.bhtml",
        "args": {"main_selector": "div.price-normal__value", "cents_selector": "sup.price-normal__rest"}
        # Selector left as-is: site is WAF-blocking the CI runner's IP before
        # any HTML is served, so there's currently nothing for a selector to
        # match. Revisit once a network-level fix is in place.
    },
    "MediaMarkt": {
        "class": SplitPriceScraper,
        "url": "https://mediamarkt.pl/pl/product/_smartfon-apple-iphone-17-pro-5g-512-gb-srebrny-mg8k4hxa-1498053.html",
        "args": {"main_selector": "span[data-test='branded-price-whole-value']", "cents_selector": "span[data-test='branded-price-decimal-value']"}
    }
}