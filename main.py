
from fastapi import FastAPI
import requests
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/")
def home():
    return {"message": "It works on Railway!"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://testingmarmorkrafts.store"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# For DEv
WC_API_URL = "https://testingmarmorkrafts.store/wp-json/wc/v3"
WC_CONSUMER_KEY = "ck_fb05462837d9679c0f6c8b11ccbac57d09c79638"
WC_CONSUMER_SECRET = "cs_cd485ed45fc41da284d567e0d49cb8a272fbe4f1"

# # For Prod
# WC_API_URL = "https://marmorkrafts.com/wp-json/wc/v3"
# WC_CONSUMER_KEY = "ck_fb05462837d9679c0f6c8b11ccbac57d09c79638"
# WC_CONSUMER_SECRET = "cs_cd485ed45fc41da284d567e0d49cb8a272fbe4f1"

@app.get("/categories")
def get_categories():
    url = f"{WC_API_URL}/products/categories?per_page=100"
    response = requests.get(url, auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET))

    if response.status_code != 200:
        return JSONResponse(
            status_code=response.status_code,
            content={"error": "Failed to fetch categories from WooCommerce."}
        )

    data = response.json()

    mcp_formatted = {
        "@context": "https://schema.org",
        "@type": "Collection",
        "name": "Product Categories",
        "members": []
    }

    for item in data:
        # ✅ Include only categories where count > 0
        if item.get("count", 0) > 0:
            mcp_formatted["members"].append({
                "@type": "ProductCategory",
                "name": item["name"],
                "url": f"https://testingmarmorkrafts.store/product-category/{item['slug']}/",
                "image": {
                    "@type": "ImageObject",
                    "url": item["image"]["src"] if item.get("image") else ""
                },
                "description": item.get("description", "")
            })

    return JSONResponse(content=mcp_formatted)


@app.get("/products")
def get_products(query: str = ""):
    url = f"{WC_API_URL}/products?search={query}&per_page=10"
    response = requests.get(url, auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET))
    
    if response.status_code != 200:
        return JSONResponse(
            status_code=response.status_code,
            content={"error": "Failed to fetch products"}
        )

    data = response.json()

    formatted = {
        "@context": "https://schema.org",
        "@type": "Collection",
        "name": "Products",
        "members": []
    }

    for item in data:
        formatted["members"].append({
            "@type": "Product",
            "name": item["name"],
            "url": item["permalink"],
            "image": {
                "@type": "ImageObject",
                "url": item["images"][0]["src"] if item.get("images") else ""
            },
            "price": item.get("price"),
            "description": item.get("short_description", "")
        })

    return formatted


@app.get("/products/on-sale")
def get_on_sale_products():
    url = f"{WC_API_URL}/products?per_page=100&orderby=modified&order=desc"
    response = requests.get(url, auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET))

    if response.status_code != 200:
        return JSONResponse(
            status_code=response.status_code,
            content={"error": "Failed to fetch products"}
        )

    all_products = response.json()

    # Filter for on_sale items only
    sale_products = [p for p in all_products if p.get("on_sale") is True]

    formatted = {
        "@context": "https://schema.org",
        "@type": "Collection",
        "name": "On Sale Products",
        "members": []
    }

    for item in sale_products:
        formatted["members"].append({
            "@type": "Product",
            "name": item["name"],
            "url": item["permalink"],
            "image": {
                "@type": "ImageObject",
                "url": item["images"][0]["src"] if item.get("images") else ""
            },
            "price": item.get("price"),
            "description": item.get("short_description", "")
        })

    return JSONResponse(content=formatted)


# @app.get("/order-status/{order_id}")
# def get_order_status(order_id: int):
#     url = f"{WC_API_URL}/orders/{order_id}"
#     response = requests.get(url, auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET))

#     if response.status_code != 200:
#         return JSONResponse(
#             status_code=response.status_code,
#             content={"error": "Failed to fetch order details"}
#         )
    
#     order_data = response.json()
#     formatted_response = {
#         "@context": "https://schema.org",
#         "@type": "Order",
#         "order_number": order_data["number"],
#         "status": order_data["status"],
#         "currency": order_data["currency"],
#         "total": order_data["total"],
#         "shipping_method": order_data["shipping_lines"][0]["method_title"],
#         "billing_address": order_data["billing"],
#         "shipping_address": order_data["shipping"],
#         "tracking_number": order_data["meta_data"][25]["value"] if "meta_data" in order_data else "Not available",
#         "order_date": order_data["date_created"],
#         "line_items": [{"name": item["name"], "quantity": item["quantity"], "price": item["price"]} for item in order_data["line_items"]],
#     }

#     return JSONResponse(content=formatted_response)


@app.get("/order-status/{order_id}")
def get_order_status(order_id: int):
    # Fetch order details from WooCommerce API
    url = f"{WC_API_URL}/orders/{order_id}"
    response = requests.get(url, auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET))

    if response.status_code != 200:
        return JSONResponse(
            status_code=response.status_code,
            content={"error": "Failed to fetch order details"}
        )
    
    order_data = response.json()

    # Initialize tracking_number as "Not available"
    tracking_number = "Not available"
    
    # Check the meta_data to find the tracking items
    for meta_item in order_data.get("meta_data", []):
        if meta_item.get("key") == "_wc_shipment_tracking_items":
            # Find tracking number within the tracking items
            tracking_items = meta_item.get("value", [])
            if tracking_items:
                tracking_number = tracking_items[0].get("tracking_number", "Not available")
            break

    # Format the response
    formatted_response = {
        "@context": "https://schema.org",
        "@type": "Order",
        "order_number": order_data["number"],
        "status": order_data["status"],
        "currency": order_data["currency"],
        "total": order_data["total"],
        "shipping_method": order_data["shipping_lines"][0]["method_title"],
        "billing_address": order_data["billing"],
        "shipping_address": order_data["shipping"],
        "tracking_number": tracking_number,
        "order_date": order_data["date_created"],
        "line_items": [{"name": item["name"], "quantity": item["quantity"], "price": item["price"]} for item in order_data["line_items"]],
    }

    return JSONResponse(content=formatted_response)



    # Fetch order details from WooCommerce API
    url = f"{WC_API_URL}/orders/{order_id}"
    response = requests.get(url, auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET))

    if response.status_code != 200:
        return JSONResponse(
            status_code=response.status_code,
            content={"error": "Failed to fetch order details"}
        )
    
    order_data = response.json()

    # Check if tracking items are available
    tracking_number = None
    if "_wc_shipment_tracking_items" in order_data:
        tracking_items = order_data["_wc_shipment_tracking_items"]
        
        # Check if tracking items array is not empty
        if tracking_items and len(tracking_items) > 0:
            tracking_number = tracking_items[0].get("tracking_number")

    # If tracking number is found, return the formatted response
    if tracking_number:
        formatted_response = {
            "@context": "https://schema.org",
            "@type": "Order",
            "order_number": order_data["number"],
            "status": order_data["status"],
            "currency": order_data["currency"],
            "total": order_data["total"],
            "shipping_method": order_data["shipping_lines"][0]["method_title"],
            "billing_address": order_data["billing"],
            "shipping_address": order_data["shipping"],
            "tracking_number": tracking_number,
            "order_date": order_data["date_created"],
            "line_items": [{"name": item["name"], "quantity": item["quantity"], "price": item["price"]} for item in order_data["line_items"]],
        }

        return JSONResponse(content=formatted_response)
    else:
        return JSONResponse(
            status_code=404,
            content={"error": "Tracking number not found in the order"}
        )
