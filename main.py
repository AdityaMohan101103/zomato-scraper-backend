from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright
import json

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/scrape")
async def scrape_zomato(url: str = Query(..., description="Zomato restaurant URL")):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        content = await page.content()
        
        # Look for __NEXT_DATA__ in scripts
        scripts = await page.query_selector_all("script#__NEXT_DATA__")
        if not scripts:
            await browser.close()
            return {"detail": "Could not find __NEXT_DATA__ script in page."}
        
        json_text = await scripts[0].inner_text()
        data = json.loads(json_text)
        await browser.close()

        # Extract menu items
        try:
            menu_data = data["props"]["pageProps"]["initialState"]["menu"]["menus"]
            items = []
            for menu in menu_data:
                for section in menu.get("menu", {}).get("categoriesMap", {}).values():
                    for item in section.get("items", []):
                        items.append({
                            "name": item.get("name"),
                            "price": item.get("price"),
                        })
            if not items:
                return {"detail": "No menu items found in parsed data."}
            return {"items": items}
        except KeyError:
            return {"detail": "Could not extract menu items from __NEXT_DATA__."}
