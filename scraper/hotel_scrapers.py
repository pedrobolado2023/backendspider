from .base_scraper import BaseScraper
from playwright.async_api import async_playwright
import datetime
import re

class BookingScraper(BaseScraper):
    async def get_hotel_rate(self, hotel_url, check_in_date, check_out_date, adults=2):
        """
        Scrapes rates from a Booking.com hotel page.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                # Booking.com URL often needs parameters for dates and adults
                # Format: https://www.booking.com/hotel/br/nome.html?checkin=YYYY-MM-DD&checkout=YYYY-MM-DD&group_adults=2
                checkin_str = check_in_date.strftime("%Y-%m-%d")
                checkout_str = check_out_date.strftime("%Y-%m-%d")
                
                # If the URL already has parameters, append with &, else with ?
                separator = "&" if "?" in hotel_url else "?"
                full_url = f"{hotel_url}{separator}checkin={checkin_str}&checkout={checkout_str}&group_adults={adults}"
                
                print(f"Scraping Booking: {full_url}")
                await page.goto(full_url, wait_until="networkidle")
                
                # Look for price elements (these selectors change often, this is a common one)
                price_selectors = [
                    "span[data-testid='price-and-possession']",
                    ".prco-valign-middle-helper",
                    ".bui-price-display__value",
                    "[data-component='hotel/new-rooms-table/room-type'] .prco-valign-middle-helper"
                ]
                
                price_text = None
                for selector in price_selectors:
                    element = await page.query_selector(selector)
                    if element:
                        price_text = await element.inner_text()
                        break
                
                if price_text:
                    # Extract numbers from string like "R$ 450,00" or "$120"
                    price_match = re.search(r'[\d\.,]+', price_text.replace('\xa0', ' '))
                    if price_match:
                        price_str = price_match.group().replace('.', '').replace(',', '.')
                        return {
                            "hotel_url": hotel_url,
                            "check_in": check_in_date,
                            "check_out": check_out_date,
                            "rate": float(price_str),
                            "currency": "BRL", # Defaulting to BRL for now
                            "status": "SUCCESS"
                        }
                
                return {"status": "NOT_FOUND", "hotel_url": hotel_url}

            except Exception as e:
                print(f"Error scraping {hotel_url}: {e}")
                return {"status": "ERROR", "error": str(e)}
            finally:
                await browser.close()

class OfficialSiteScraper(BaseScraper):
    # Specific logic for official sites (Omnibees, Let's Book, etc.)
    # Would be implemented per hotel/engine
    pass
