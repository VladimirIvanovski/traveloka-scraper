# Traveloka Hotel Rate Scraper

## How to run
```bash
pip install -r requirements.txt
playwright install chromium
python main_script.py
```

## What it does
Scrapes all room rates from a Traveloka hotel page and saves them to `rates.json`.
It intercepts the internal `/api/v2/hotel/search/rooms` API call that the browser makes when loading the page.
Each rate contains: room name, rate name, price, currency, taxes, total price, cancellation policy, breakfast info, and number of guests.
If a room has a discounted price, the original price is stored separately under `original_price`.
Prices per night are also multiplied to produce `shown_price_per_stay`, `net_price_per_stay`, and `total_price_per_stay`.

## Why this approach
Traveloka is a JavaScript-rendered SPA protected by AWS WAF and DataDome bot detection — plain `requests` calls to the API get blocked by JS challenges that require a real browser to solve.
Playwright launches a real Chromium browser (undetected), navigates to the hotel page, and captures the rooms API response automatically — no manual cookie copying needed.
The `deep_link` is generated programmatically from the hotel parameters (check-in, check-out, hotel ID, etc.) so the script can target any hotel without hardcoding a URL.
