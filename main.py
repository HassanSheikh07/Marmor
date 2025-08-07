from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import requests
from bs4 import BeautifulSoup
app = FastAPI() 

@app.get("/")
def home():
  return {"message It is working! yes"}

# WooCommerce API credentials
WC_API_URL = "https://marmorkrafts.com/wp-json/wc/v3"
WC_CONSUMER_KEY = "ck_fb05462837d9679c0f6c8b11ccbac57d09c79638"
WC_CONSUMER_SECRET = "cs_cd485ed45fc41da284d567e0d49cb8a272fbe4f1"

def strip_html(html):
    return BeautifulSoup(html, "html.parser").get_text()
 

 
@app.get("/products")
def get_products(
    query: str = "",
    color: str = "",
    exclude_marble: bool = False,
    include_variations: bool = False
):
    fetch_url = f"{WC_API_URL}/products?search={query}&per_page=50"
    response = requests.get(fetch_url, auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET))
 
    if response.status_code != 200:
        return JSONResponse(status_code=response.status_code, content={"error": "Failed to fetch products"})
 
    data = response.json()
    query_lower = query.lower().strip()
    products = []
 
    for item in data:
        name = item["name"].lower()
        short_desc = item.get("short_description", "").lower()
        long_desc = strip_html(item.get("description", "")).lower()
 
        if exclude_marble and "marble" in f"{name} {short_desc} {long_desc}":
            continue
 
        shapes = ["rectangular", "square", "round", "set", "oval", "triangle", "chess set"]
        explicit_shape = next((shape for shape in shapes if shape in query_lower), None)
        if explicit_shape and explicit_shape not in name:
            continue
 
        variations = get_variations(item["id"]) if include_variations else []
 
        if color:
            variations = [
                v for v in variations
                if any(attr["name"].lower() == "color" and attr["option"].lower() == color.lower()
                       for attr in v.get("attributes", []))
            ]
            if not variations and include_variations:
                continue
 
        score = 0
        full_text = f"{name} {short_desc} {long_desc}"
 
        if query_lower in name:
            score += 5
        elif query_lower in full_text:
            score += 3
 
        matched_words = 0
        for word in query_lower.split():
            if word in name:
                score += 1.5
                matched_words += 1
            elif word in short_desc:
                score += 1
                matched_words += 1
            elif word in long_desc:
                score += 0.5
                matched_words += 1
 
        if matched_words < len(query_lower.split()) / 2:
            continue
 
        products.append({
            "@type": "Product",
            "name": item["name"],
            "url": item["permalink"],
            "image": {
                "@type": "ImageObject",
                "url": item["images"][0]["src"] if item.get("images") else ""
            },
            "price": item.get("price"),
            "description": item.get("short_description", ""),
            "score": score
        })
 
    products.sort(key=lambda x: x["score"], reverse=True)
 
    return {
        "@context": "https://schema.org",
        "@type": "Collection",
        "name": "Products",
        "members": products[:10]
    }