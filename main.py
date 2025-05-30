from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import json

app = FastAPI()

# Allow CORS (so frontend can access this backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your Vercel frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Zomato Scraper API running."}

@app.get("/scrape")
def scrape_menu(url: str = Query(..., description="Full Zomato restaurant URL")):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        script_tag = soup.find("script", id="__NEXT_DATA__")
        if not script_tag:
            return {"detail": "Could not find __NEXT_DATA__ script in page."}

        data = json.loads(script_tag.string)

        # DEBUG: Uncomment this if you're unsure where the menu data is
        # return data  # send raw structure to frontend for inspection

        menus = data.get("props", {}).get("pageProps", {}).get("initialState", {}).get("menu", {}).get("menus", [])
        menu_items = []

        for menu in menus:
            for section in menu.get("categories", []):
                for item in section.get("items", []):
                    name = item.get("name")
                    price = item.get("price")
                    if name and price is not None:
                        menu_items.append({"name": name, "price": price})

        if not menu_items:
            return {"detail": "No menu items found on the page."}

        return {"menu": menu_items}

    except Exception as e:
        return {"detail": f"Error scraping page: {str(e)}"}
