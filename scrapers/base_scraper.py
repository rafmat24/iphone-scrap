import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async


class BaseScraper:
    def __init__(self, store_name: str, url: str):
        self.store_name = store_name
        self.url = url

    async def _goto_resilient(self, page):
        """
        Navigate to the page, preferring 'networkidle' (best signal that a
        JS-heavy SPA has actually rendered its price), but falling back to
        'domcontentloaded' + a short hydration buffer if the page never goes
        fully idle. Some sites (e.g. MediaExpert) keep background requests
        running indefinitely (chat widgets, stock polling, analytics), which
        means 'networkidle' can time out even though the price has long
        since rendered.
        """
        try:
            await page.goto(self.url, wait_until="networkidle", timeout=15000)
        except Exception:
            # Page is alive but never went idle - fall back to a cheaper
            # wait condition and give the SPA a moment to hydrate instead.
            await page.goto(self.url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

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
                await self._goto_resilient(page)

                # Wywołujemy logikę specyficzną dla danego sklepu
                price = await self.extract_price(page)
                return price
            except Exception as e:
                # Zostaw na przyszłość: zrzut ekranu ułatwia diagnozę,
                # gdy selektor znowu się zmieni.
                try:
                    await page.screenshot(path=f"debug_{self.store_name}.png", full_page=True)
                except Exception:
                    pass
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