"""
find_selectors.py

One-off debug tool. For each configured store, it:
  1. Opens the product page exactly like the real scraper does (stealth, same UA).
  2. Searches the rendered page for elements whose text contains the known
     price (e.g. "6 799" / "6799" / "6 439"), since we already know the price
     from the screenshots.
  3. Prints, for each match: tag name, class, id, data-testid (if any), and
     a CSS selector guess you can paste into config.py.
  4. Saves the outerHTML of each match to a .txt file so you can inspect the
     surrounding structure if the guessed selector still isn't unique enough.

This does NOT touch prices_history.json or send any email. Safe to run
as a one-off GitHub Action job, separate from main.py.

Usage: just edit KNOWN_PRICES below to match whatever price is currently
shown on each site (check the debug screenshots), then run this file
instead of main.py in the workflow, temporarily.
"""

import asyncio
import re
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

from config import PRODUCTS_CONFIG

# Fill in the price you SAW in each screenshot (digits only, no spaces).
# This is just to help the script find the right element automatically.
# If you don't know it for a store, leave it as None and the script
# will instead dump all elements containing "zł" near the top of the page.
KNOWN_PRICES = {
    "X-Kom": "6799",
    "Morele": "6799",
    "Komputronik": "6439",
    "Neonet": "6799",
    "MediaExpert": "6799",
    "Euro RTV AGD": None,  # blocked by WAF, skip — won't help until unblocked
    "MediaMarkt": "6799",
}


def build_selector(el_info: dict) -> str:
    """Best-effort CSS selector guess from element attributes."""
    tag = el_info["tag"]
    el_id = el_info.get("id")
    classes = el_info.get("class", "")
    testid = el_info.get("data-testid")

    if testid:
        return f"{tag}[data-testid='{testid}']"
    if el_id:
        return f"#{el_id}"
    if classes:
        first_class = classes.strip().split()[0]
        return f"{tag}.{first_class}"
    return tag


async def inspect_store(store, info, browser):
    url = info["url"]
    if "TUTAJ_WKLEJ" in url:
        print(f"[{store}] Pominięto - brak URL.")
        return

    price_digits = KNOWN_PRICES.get(store)

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="pl-PL",
    )
    page = await context.new_page()
    await stealth_async(page)

    print(f"\n=== {store} ===")
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
    except Exception as e:
        print(f"[{store}] goto failed/timed out ({e}); continuing with whatever loaded.")

    # Give SPA hydration a little extra buffer beyond networkidle.
    await page.wait_for_timeout(1500)

    if price_digits:
        # Find elements whose normalized text contains the known price digits,
        # ignoring spaces/non-breaking-spaces/commas used as thousand separators.
        matches = await page.evaluate(
            """(priceDigits) => {
                function norm(s) {
                    return (s || "").replace(/[\\s\\u00A0,.]/g, "");
                }
                const all = Array.from(document.querySelectorAll("body *"));
                const results = [];
                for (const el of all) {
                    // only leaf-ish nodes: avoid huge containers matching too
                    if (el.children.length > 2) continue;
                    const text = el.textContent || "";
                    if (norm(text).includes(priceDigits) && text.length < 60) {
                        results.push({
                            tag: el.tagName.toLowerCase(),
                            id: el.id || null,
                            class: el.className && typeof el.className === "string" ? el.className : null,
                            testid: el.getAttribute("data-testid"),
                            text: text.trim(),
                            outerHTML: el.outerHTML.slice(0, 500)
                        });
                    }
                }
                return results;
            }""",
            price_digits,
        )

        if not matches:
            print(f"[{store}] No element found containing '{price_digits}'. "
                  f"Price text might differ from screenshot, or page didn't fully render.")
        else:
            print(f"[{store}] Found {len(matches)} candidate element(s):")
            for i, m in enumerate(matches):
                guess = build_selector({
                    "tag": m["tag"],
                    "id": m["id"],
                    "class": m["class"] or "",
                    "data-testid": m["testid"],
                })
                print(f"  [{i}] tag={m['tag']} id={m['id']} class={m['class']} "
                      f"data-testid={m['testid']}")
                print(f"      text: {m['text']!r}")
                print(f"      suggested selector: {guess}")
                # save outerHTML for manual inspection
                fname = f"selector_debug_{store.replace(' ', '_')}_{i}.html"
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(m["outerHTML"])
                print(f"      saved snippet -> {fname}")
    else:
        print(f"[{store}] No known price configured, skipping targeted search "
              f"(likely blocked — check screenshot).")

    await page.screenshot(path=f"selector_debug_{store.replace(' ', '_')}.png", full_page=False)
    await context.close()


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for store, info in PRODUCTS_CONFIG.items():
            await inspect_store(store, info, browser)
            await asyncio.sleep(2)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())