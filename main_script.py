"""
Traveloka Hotel Rate Scraper
Install: pip install playwright && playwright install chromium
"""

import json
import os
from urllib.parse import quote
from playwright.sync_api import sync_playwright

URL = "https://www.traveloka.com/en-th/hotel/thailand/cera-resort-chaam--1000000401311?spec=18-03-2026.19-03-2026.1.1.HOTEL.1000000401311..2"

def generate_deep_link(check_in, check_out, num_nights, num_rooms,
                       hotel_id, hotel_name, num_adults, locale="en-th"):
    spec = (
        f"{check_in}.{check_out}.{num_nights}.{num_rooms}"
        f".HOTEL.{hotel_id}.{quote(hotel_name)}.{num_adults}"
    )
    return (
        f"https://www.traveloka.com/{locale}/hotel/detail"
        f"?spec={spec}&priceDisplay=NIGHT&multiRoomAlternativeOption=false"
    )

def scrape(url):
    print(f"Scraping: {url}\n")
    captured = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/145.0.0.0 Safari/537.36"
            ),
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"}
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = context.new_page()

        def handle_response(response):
            if "hotel/search/rooms" in response.url and response.status == 200:
                try:
                    captured["data"] = response.json()
                    print("✅ Rooms API captured!")
                except Exception as e:
                    print(f"❌ Parse error: {e}")

        page.on("response", handle_response)
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(10000)
        browser.close()

    return captured.get("data")

def fmt(amount):
    return f"{int(amount) / 100:.2f}"

def parse_rates(data):
    rates = []
    for room in data["data"]["recommendedEntries"]:
        for inv in room["hotelRoomInventoryList"]:
            rate   = inv["rateDisplay"]
            strike = inv["strikethroughRateDisplay"]
            final  = inv["finalPrice"]
            price  = fmt(rate["totalFare"]["amount"])
            orig   = None if strike.get("nullOrEmpty") or strike["totalFare"].get("nullOrEmpty") else fmt(strike["totalFare"]["amount"])

            rate_name = (
                inv.get("inventoryName")
                or inv.get("roomCardHeaderDisplay", {}).get("title")
                or room["name"]
            )

            entry = {
                "room_name":            room["name"],
                "rate_name":            rate_name,
                "shown_currency":       rate["baseFare"]["currency"],
                "shown_price":          fmt(rate["baseFare"]["amount"]),
                "net_price":            fmt(rate["baseFare"]["amount"]),
                "cancellation_policy":  inv["cancellationPolicyDisplay"]["label"],
                "breakfast":            inv["mealPlanDisplay"]["displayMealPlanIncluded"] if inv["isBreakfastIncluded"] else "No Breakfast",
                "number_of_guests":     room["baseOccupancy"],
                "taxes_amount":         fmt(rate["taxes"]["amount"]),
                "total_price":          price,
                "original_price":       orig if orig and orig != price else None,
                "shown_price_per_stay": fmt(final["totalPriceRateDisplay"]["baseFare"]["amount"]),
                "net_price_per_stay":   fmt(final["totalPriceRateDisplay"]["exclusiveFinalPrice"]["amount"]),
                "total_price_per_stay": fmt(final["totalPriceRateDisplay"]["totalFare"]["amount"]),
            }
            rates.append(entry)
    return rates

if __name__ == "__main__":
    deep_link = generate_deep_link(
        check_in="18-03-2026", check_out="19-03-2026",
        num_nights=1, num_rooms=1,
        hotel_id="1000000401311", hotel_name="Cera Resort Chaam",
        num_adults=2
    )
    print(f"Deep link: {deep_link}\n")

    # data  = scrape(URL)   Normal URL
    data = scrape(deep_link)
    if not data:
        raise Exception("Rooms API not captured.")

    rates  = parse_rates(data)
    result = {"rates": rates}

    # Save JSON in the same folder as this script
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rates.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved to {output_path}")
    print(json.dumps(result, indent=2, ensure_ascii=False))