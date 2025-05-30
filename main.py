from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import asyncio
from playwright.async_api import async_playwright

app = FastAPI()

# Enable CORS so frontend (like Vercel) can access it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Zomato Scraper Backend is running"}

@app.get("/scrape")
async def scrape_menu(url: str = Query(..., description="Zomato restaurant URL")):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_selector("script#__NEXT_DATA__", timeout=15000)

            content = await page.content()
            next_data = await page.locator("script#__NEXT_DATA__").inner_text()

            import json
            data = json.loads(next_data)
            items = []

            try:
                menus = data["props"]["pageProps"]["orderMenu"]["menu"]["menus"]
                for menu in menus:
                    for category in menu.get("categories", []):
                        for item in category.get("items", []):
                            items.append({
                                "name": item.get("name"),
                                "price": item.get("price")
                            })
            except KeyError:
                return {"detail": "Could not parse menu structure."}

            if not items:
                return {"detail": "No menu items found on the page."}

            return items

        except Exception as e:
            return {"detail": f"Error scraping page: {str(e)}"}
        finally:
            await browser.close()
