import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

class BaseScraper:
    def __init__(self, store_name: str, url: str):
        self.store_name = store_name
        self.url = url

    async def scrape_price(self) -> float:
        async with async_playwright() as p:
            # Uruchamiamy chromium w trybie headless
            browser = await p.chromium.launch(headless=True)
            
            # Tworzymy kontekst z realistycznym User-Agentem
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="pl-PL"
            )
            
            page = await context.new_page()
            # Aplikujemy stealth, aby ominąć podstawowe wykrywanie botów
            await stealth_async(page)
            
            try:
                # Zwiększamy timeout do 30 sekund i czekamy na załadowanie sieci
                await page.goto(self.url, wait_until="networkidle", timeout=30000)
                
                # Wywołujemy logikę specyficzną dla danego sklepu
                price = await self.extract_price(page)
                return price
            except Exception as e:
                print(f"[{self.store_name}] Błąd podczas pobierania: {e}")
                return None
            finally:
                await browser.close()

    async def extract_price(self, page) -> float:
        raise NotImplementedError("Każdy scraper musi implementować metodę extract_price")

    def clean_price(self, price_str: str) -> float:
        """Pomocnicza metoda do czyszczenia stringa z ceną na float."""
        if not price_str:
            return None
        # Usuwamy zł, spacje, i inne śmieci, zamieniamy przecinek na kropkę
        cleaned = "".join([c for c in price_str if c.isdigit() or c in [',', '.']])
        cleaned = cleaned.replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return None