from scrapers.stores import StandardScraper, SplitPriceScraper

HISTORY_FILE = "prices_history.json"

PRODUCTS_CONFIG = {
    "X-Kom": {
        "class": StandardScraper, 
        "url": "https://www.x-kom.pl/p/1362361-smartfon-telefon-apple-iphone-17-pro-512gb-srebrny.html", 
        "args": {"selector": "div.u-html-text, .price__value"} 
    },
    "Morele": {
        "class": StandardScraper, 
        "url": "https://www.morele.net/smartfon-apple-iphone-17-pro-5g-12-512gb-srebrny-mg8k4ql-a-15662750/", 
        "args": {"selector": "#product_price_brutto"}
    },
    "Komputronik": {
        "class": StandardScraper, 
        "url": "https://www.komputronik.pl/product/983042/telefon-apple-iphone-17-pro-512gb-srebrny.html", 
        "args": {"selector": "span.text-3xl.font-bold, .price span"} 
    },
    "Neonet": {
        "class": StandardScraper, 
        "url": "https://www.neonet.pl/p/1362361-smartfon-apple-iphone-17-pro-512gb-srebrny.html", 
        "args": {"selector": "div[class*='price'] font, span[class*='price']"}
    },
    "MediaExpert": {
        "class": SplitPriceScraper, 
        "url": "https://www.mediaexpert.pl/smartfony-i-zegarki/smartfony/smartfon-apple-iphone-17-pro-5g-silver-512gb", 
        "args": {"main_selector": "span.whole", "cents_selector": "span.cents"}
    },
    "Euro RTV AGD": {
        "class": SplitPriceScraper, 
        "url": "https://www.euro.com.pl/telefony-komorkowe/apple-iphone-17-pro-512gb-srebrny.bhtml", 
        "args": {"main_selector": "div.price-normal__value", "cents_selector": "sup.price-normal__rest"}
    },
    "MediaMarkt": {
        "class": StandardScraper, 
        "url": "https://mediamarkt.pl/pl/product/_smartfon-apple-iphone-17-pro-5g-512-gb-srebrny-mg8k4hxa-1498053.html", 
        "args": {"selector": "span[data-testid='product-card-price'], span[data-testid='product-price']"}
    }
}