from scrapers.stores import StandardScraper, SplitPriceScraper

# Plik, w którym przechowywana jest historia cen z poprzednich dni
HISTORY_FILE = "prices_history.json"

# ==============================================================================
# MIEJSCE NA TWOJE LINKI URL ORAZ KONFIGURACJĘ SELEKTORÓW
# ==============================================================================
PRODUCTS_CONFIG = {
    "X-Kom": {
        "class": StandardScraper, 
        "url": "https://www.x-kom.pl/p/1362370-smartfon-telefon-apple-iphone-17-pro-max-512gb-srebrny.html", 
        "args": {"selector": "span.u-html-text"}
    },
    "Morele": {
        "class": StandardScraper, 
        "url": "https://www.morele.net/smartfon-apple-iphone-17-pro-5g-12-512gb-srebrny-mg8k4ql-a-15662750/", 
        "args": {"selector": ".product-price"}
    },
    "Komputronik": {
        "class": StandardScraper, 
        "url": "https://www.komputronik.pl/product/983042/telefon-apple-iphone-17-pro-512gb-srebrny.html", 
        "args": {"selector": ".price span"}
    },
    "Neonet": {
        "class": StandardScraper, 
        "url": "https://www.neonet.pl/p/1362361-smartfon-apple-iphone-17-pro-512gb-srebrny.html", 
        "args": {"selector": "span[class*='price']"}
    },
    "MediaExpert": {
        "class": SplitPriceScraper, 
        "url": "https://www.mediaexpert.pl/smartfony-i-zegarki/smartfony/smartfon-apple-iphone-17-pro-5g-silver-512gb", 
        "args": {"main_selector": ".main-price .whole", "cents_selector": ".main-price .cents"}
    },
    "Euro RTV AGD": {
        "class": SplitPriceScraper, 
        "url": "https://www.euro.com.pl/telefony-komorkowe/apple-iphone-17-pro-512gb-srebrny.bhtml", 
        "args": {"main_selector": ".price-normal__value", "cents_selector": ".price-normal__rest"}
    },
    "MediaMarkt": {
        "class": StandardScraper, 
        "url": "https://mediamarkt.pl/pl/product/_smartfon-apple-iphone-17-pro-max-512-gb-srebrny-mfyq4hxa-1498159.html", 
        "args": {"selector": "span[data-testid='product-price']"}
    }
}