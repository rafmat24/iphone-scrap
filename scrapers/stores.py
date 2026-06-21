from scrapers.base_scraper import BaseScraper

class StandardScraper(BaseScraper):
    """Dla sklepów, gdzie cała cena jest w jednym elemencie tekstowym."""
    def __init__(self, store_name, url, selector):
        super().__init__(store_name, url)
        self.selector = selector

    async def extract_price(self, page) -> float:
        element = await page.wait_for_selector(self.selector, timeout=20000)
        raw_price = await element.inner_text()
        return self.clean_price(raw_price)

class SplitPriceScraper(BaseScraper):
    """Dla sklepów, które rozbijają złote i grosze na osobne tagi HTML (np. MediaExpert, Euro)."""
    def __init__(self, store_name, url, main_selector, cents_selector):
        super().__init__(store_name, url)
        self.main_selector = main_selector
        self.cents_selector = cents_selector

    async def extract_price(self, page) -> float:
        main_element = await page.wait_for_selector(self.main_selector, timeout=20000)
        main_text = await main_element.inner_text()
        
        try:
            cents_element = await page.locator(self.cents_selector).first
            cents_text = await cents_element.inner_text()
        except:
            cents_text = "00"
            
        raw_price = f"{main_text},{cents_text}"
        return self.clean_price(raw_price)