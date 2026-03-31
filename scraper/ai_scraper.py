import os
import google.generativeai as genai
from playwright.async_api import async_playwright
import asyncio
import json
import re
from .base_scraper import BaseScraper
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

class AIScraper(BaseScraper):
    def __init__(self, browser_type="chromium"):
        super().__init__(browser_type)
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    def simplify_html(self, html_content):
        """
        Simplifies HTML by removing unnecessary tags (script, style, head, etc.)
        to reduce token count while keeping structural integrity.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove common non-data tags
        for tag in soup(['script', 'style', 'head', 'title', 'meta', 'link', 'svg', 'path', 'noscript', 'iframe']):
            tag.decompose()
            
        # Remove attributes except for classes/ids that might be helpful
        for tag in soup.find_all(True):
            attrs = dict(tag.attrs)
            tag.attrs = {k: v for k, v in attrs.items() if k in ['id', 'class', 'role', 'aria-label', 'data-testid']}
            
        return soup.prettify()[:15000] # Cap at 15k chars for token safety

    async def get_hotel_rate(self, hotel_id, hotel_url, check_in_date, check_out_date, instruction, proxy_config=None, discovery_map=None):
        """
        Advanced extraction using AI Discovery.
        """
        if not self.model:
            return {"status": "ERROR", "message": "GEMINI_API_KEY not found in .env"}

        browser_args = []
        proxy = None
        if proxy_config and proxy_config.get("host"):
            proxy = {
                "server": f"http://{proxy_config['host']}:{proxy_config['port']}",
                "username": proxy_config.get("user"),
                "password": proxy_config.get("pass")
            }

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, proxy=proxy)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                # 1. Navigation
                checkin_str = check_in_date.strftime("%Y-%m-%d")
                checkout_str = check_out_date.strftime("%Y-%m-%d")
                
                # Intelligent URL construction or direct access
                await page.goto(hotel_url, wait_until="networkidle", timeout=30000)

                # 2. HTML Simplification
                raw_html = await page.content()
                clean_html = self.simplify_html(raw_html)

                # 3. AI Analysis (Discovery)
                # If we don't have a map or instructions changed, we perform discovery
                prompt = f"""
                Analyze this simplified HTML from a hotel site. 
                INSTRUCTION: {instruction}
                DATES: {checkin_str} to {checkout_str}
                
                HTML CONTENT:
                {clean_html}
                
                Identify where the requested information is located. 
                Return a JSON object with:
                {{
                    "rate": float,
                    "currency": "string",
                    "found_hotel_name": "string",
                    "ai_thought": "brief explanation of how you found the data",
                    "status": "SUCCESS"
                }}
                If not found, explain why in "ai_thought" and set status to "NOT_FOUND".
                """
                
                response = self.model.generate_content(prompt)
                ai_text = response.text
                
                try:
                    json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
                    if not json_match:
                        return {"status": "ERROR", "message": "AI did not return valid JSON", "raw_ai": ai_text}
                    
                    result = json.loads(json_match.group())
                    result["ai_log"] = ai_text # Store full log
                    
                    if result.get("status") == "SUCCESS":
                        return {
                            **result,
                            "hotel_url": hotel_url,
                            "check_in": check_in_date,
                            "check_out": check_out_date
                        }
                    else:
                        return {"status": "FAILED", "message": result.get("ai_thought", "Data not found"), "ai_log": ai_text}
                        
                except Exception as e:
                    return {"status": "ERROR", "message": f"Parse Error: {str(e)}", "raw_ai": ai_text}

            except Exception as e:
                return {"status": "ERROR", "message": str(e)}
            finally:
                await browser.close()
