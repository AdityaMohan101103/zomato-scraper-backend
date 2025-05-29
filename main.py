from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from requests_html import HTMLSession
import json
import re
from html import unescape

app = FastAPI()

class ScrapeRequest(BaseModel):
    url: str

session = HTMLSession()

def extract_needed_data(json_data):
    if isinstance(json_data, str):
        json_data = json.loads(json_data)

    resId = str(json_data.get("pages", {}).get('current', {}).get("resId"))
    menus = json_data.get("pages", {}).get('restaurant', {}).get(resId, {}).get("order", {}).get("menuList", {}).get("menus", [])
    name = json_data.get("pages", {}).get('restaurant', {}).get(resId, {}).get("sections", {}).get("SECTION_BASIC_INFO", {}).get('name', 'Restaurant')

    filtered_data = []
    for menu in menus:
        category_name = menu.get("menu", {}).get("name", "")
        for category in menu.get("menu", {}).get("categories", []):
            sub_category_name = category.get("category", {}).get("name", "")
            for item in category.get("category", {}).get("items", []):
                item_data = item["item"]
                filtered_data.append({
                    "restaurant": name,
                    "category": category_name,
                    "sub_category": sub_category_name,
                    "dietary_slugs": ','.join(item_data.get("dietary_slugs", [])),
                    "item_name": item_data.get("name", ""),
                    "price": item_data.get("display_price", ""),
                    "desc": item_data.get("desc", "")
                })

    return filtered_data, name

@app.get("/")
def read_root():
    return {"message": "Zomato scraper backend is live!"}

@app.post("/scrape")
def scrape_menu(request: ScrapeRequest):
    url = request.url.strip()
    if not url.endswith('/order'):
        url += '/order'

    try:
        response = session.get(url)
        response.html.render(timeout=20)
        html = response.html.html
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error rendering page: {str(e)}")

    match = re.search(r'window\.__PRELOADED_STATE__ = JSON\.parse\((.+?)\);', html)
    if match:
        try:
            escaped_json = match.group(1)
            decoded_json_str = unescape(escaped_json)
            parsed_json = json.loads(decoded_json_str)
            preloaded_state = json.loads(parsed_json)

            flat_data, restaurant_name = extract_needed_data(preloaded_state)

            return {
                "restaurant": restaurant_name,
                "menu": flat_data
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error parsing JSON: {str(e)}")

    raise HTTPException(status_code=404, detail="No embedded menu data found on this page.")
