from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from requests_html import AsyncHTMLSession

app = FastAPI()

class ScrapeRequest(BaseModel):
    url: str

@app.get("/")
async def root():
    return {"message": "Zomato scraper backend is live!"}

@app.post("/scrape")
async def scrape_menu(data: ScrapeRequest):
    try:
        session = AsyncHTMLSession()
        response = await session.get(data.url)
        await response.html.arender(timeout=20)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error rendering page: {e}")

    items = response.html.find("div[class^='sc-beySbM']")
    menu_data = []

    for item in items:
        name_elem = item.find("h4", first=True)
        price_elem = item.find("span[class*='sc-17hyc2s-1']", first=True)
        if name_elem and price_elem:
            menu_data.append({
                "name": name_elem.text.strip(),
                "price": price_elem.text.strip()
            })

    if not menu_data:
        raise HTTPException(status_code=404, detail="No menu items found on the page.")

    return {"menu": menu_data}
