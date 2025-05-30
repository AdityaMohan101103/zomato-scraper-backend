from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright
import json

app = FastAPI()

# Allow CORS (for frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/scrape")
async def scrape_zomato_menu(url: str = Query(..., description="Zomato restaurant URL")):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            content = await page.content()

            # Extract __NEXT_DATA__ from the page
            next_data_handle = await page.query_selector('script#__NEXT_DATA__')
            if not next_data_handle:
                raise HTTPException(status_code=404, detail="Could not find __NEXT_DATA__ script in page.")

            next_data_json = await next_data_handle.inner_text()
            data = json.loads(next_data_json)

            # Navigate the JSON to extract menu info
            try:
                menu_items = data["props"]["pageProps"]["initialState"]["menu"]["menus"][0]["menu"]["categories"]
                result = []
                for category in menu_items:
                    category_name = category["category"]["name"]
                    for item in category["items"]:
                        result.append({
                            "category": category_name,
                            "name": item["name"],
                            "price": item["price"],
                        })
                return {"items": result}
            except Exception:
                raise HTTPException(status_code=404, detail="No menu items found on the page.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
