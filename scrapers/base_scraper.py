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
            # Launch Chromium in headless mode
            browser = await p.chromium.launch(headless=True)

            # Create a context with a realistic User-Agent
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US"
            )

            page = await context.new_page()
            # Apply stealth measures to bypass basic bot detection
            await stealth_async(page)

            try:
                await self._goto_resilient(page)

                # Run store-specific extraction logic
                price = await self.extract_price(page)
                return price
            except Exception as e:
                # Keep this for future debugging: a screenshot helps when a selector changes.
                try:
                    await page.screenshot(path=f"debug_{self.store_name}.png", full_page=True)
                except Exception:
                    pass
                print(f"[{self.store_name}] Fetch error: {e}")
                return None
            finally:
                await browser.close()

    async def extract_price(self, page) -> float:
        raise NotImplementedError("Each scraper must implement the extract_price method")

    def clean_price(self, price_str: str) -> float:
        """Helper method that cleans a price string and converts it to float."""
        if not price_str:
            return None
        # Remove currency symbols, spaces, and other noise; normalize comma to dot.
        cleaned = "".join([c for c in price_str if c.isdigit() or c in [',', '.']])
        cleaned = cleaned.replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return None