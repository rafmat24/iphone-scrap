import re
from scrapers.base_scraper import BaseScraper


class StandardScraper(BaseScraper):
    """Dla sklepów, gdzie cała cena jest w jednym elemencie tekstowym."""
    def __init__(self, store_name, url, selector):
        super().__init__(store_name, url)
        self.selector = selector

    async def extract_price(self, page) -> float:
        # .first avoids "strict mode" failures if a selector matches more
        # than one element on the page (e.g. duplicate price blocks).
        # We wait for "attached" rather than "visible": some stores
        # (e.g. Komputronik) legitimately render the correct price inside
        # a node that's hidden (alternate layout, hover-card duplicate,
        # etc.) - the text is still correct, visibility just isn't a
        # reliable signal here.
        element = page.locator(self.selector).first
        await element.wait_for(state="attached", timeout=20000)
        raw_price = await element.inner_text()
        return self.clean_price(raw_price)


class SplitPriceScraper(BaseScraper):
    """Dla sklepów, które rozbijają złote i grosze na osobne tagi HTML (np. MediaExpert, Euro, MediaMarkt)."""
    def __init__(self, store_name, url, main_selector, cents_selector):
        super().__init__(store_name, url)
        self.main_selector = main_selector
        self.cents_selector = cents_selector

    async def extract_price(self, page) -> float:
        main_locator = page.locator(self.main_selector).first
        await main_locator.wait_for(state="attached", timeout=20000)
        main_text = await main_locator.inner_text()

        # The "whole" part sometimes already ends in its own separator
        # (e.g. MediaMarkt renders "6799," before the decimal span), so we
        # strip any trailing punctuation before we add our own comma back.
        main_digits = re.sub(r"[^\d]+$", "", main_text.strip())

        # Fixed: page.locator() is synchronous and never raises on its own,
        # so the old try/except here never actually caught a missing-cents
        # case. We now explicitly check the count and use a short timeout
        # on the cents wait, falling back to "00" if it's missing, empty,
        # or not actually numeric (e.g. a literal "–" meaning "no grosze").
        cents_text = "00"
        cents_locator = page.locator(self.cents_selector).first
        try:
            if await cents_locator.count() > 0:
                await cents_locator.wait_for(state="attached", timeout=3000)
                candidate = (await cents_locator.inner_text()).strip()
                if candidate.isdigit():
                    cents_text = candidate
        except Exception:
            cents_text = "00"

        raw_price = f"{main_digits},{cents_text}"
        return self.clean_price(raw_price)


class AriaPriceScraper(BaseScraper):
    """
    Dla sklepów (np. X-Kom, Neonet), gdzie najbardziej niezawodna cena
    znajduje się w atrybucie aria-label elementu dla czytników ekranu,
    np. aria-label="Cena: 6 799,00 zł", zamiast w jego widocznym tekście.
    Ten element bywa wizualnie ukryty (sr-only), dlatego nie czekamy na
    state="visible", tylko state="attached" - wystarczy, że jest w DOM.
    """
    def __init__(self, store_name, url, selector):
        super().__init__(store_name, url)
        self.selector = selector

    async def extract_price(self, page) -> float:
        element = page.locator(self.selector).first
        await element.wait_for(state="attached", timeout=20000)
        aria_label = await element.get_attribute("aria-label")
        if not aria_label:
            # fallback: maybe the visible text already has it
            aria_label = await element.inner_text()
        # aria_label looks like "Cena: 6 799,00 zł" -> strip the "Cena:" prefix
        raw_price = re.sub(r"^[^\d]*", "", aria_label)
        return self.clean_price(raw_price)