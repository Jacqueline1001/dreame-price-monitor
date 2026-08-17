#!/usr/bin/env python3
"""
Config generator for the personal care price dashboard.
Generates config.json with all product x market x platform tracking entries.
"""
import json

PRODUCTS = [
    {"id": "dreame-airstyle-pro",  "brand": "Dreame",     "model": "Airstyle Pro",   "category": "styler"},
    {"id": "dyson-airwrap",         "brand": "Dyson",      "model": "Airwrap",        "category": "styler"},
    {"id": "shark-flexstyle",       "brand": "Shark",       "model": "FlexStyle",      "category": "styler"},
    {"id": "dyson-corrale",         "brand": "Dyson",       "model": "Corrale",        "category": "flat_iron"},
    {"id": "babylisspro-titanium",  "brand": "BaBylissPRO", "model": "Titanium",       "category": "flat_iron"},
    {"id": "remington-flat-iron",   "brand": "Remington",   "model": "Flat Iron",      "category": "flat_iron"},
    {"id": "dreame-pocket-ultra",   "brand": "Dreame",      "model": "Pocket Ultra",   "category": "hair_dryer"},
    {"id": "dyson-supersonic",      "brand": "Dyson",       "model": "Supersonic",     "category": "hair_dryer"},
    {"id": "shark-hyperair",        "brand": "Shark",       "model": "HyperAir",       "category": "hair_dryer"},
    {"id": "laifen-dryer",           "brand": "Laifen",      "model": "Hair Dryer",     "category": "hair_dryer"},
]

MARKETS = {
    "MX": {"name": "Mexico",       "currency": "MXN", "platforms": {
        "amazon":         {"amazon_domain": "com.mx"},
        "mercadolibre":   {"ml_site": "MLM"},
    }},
    "BR": {"name": "Brazil",       "currency": "BRL", "platforms": {
        "amazon":         {"amazon_domain": "com.br"},
        "mercadolibre":   {"ml_site": "MLB"},
    }},
    "CO": {"name": "Colombia",     "currency": "COP", "platforms": {
        "mercadolibre":   {"ml_site": "MCO"},
        "falabella":      {},
    }},
    "TR": {"name": "Turkey",       "currency": "TRY", "platforms": {
        "trendyol":       {},
        "hepsiburada":    {},
    }},
    "AE": {"name": "UAE",          "currency": "AED", "platforms": {
        "noon":           {"noon_region": "uae"},
        "amazon":         {"amazon_domain": "ae"},
    }},
    "SA": {"name": "Saudi Arabia", "currency": "SAR", "platforms": {
        "noon":           {"noon_region": "saudi"},
        "amazon":         {"amazon_domain": "sa"},
    }},
}

PLATFORM_NAMES = {
    "amazon": "Amazon",
    "mercadolibre": "Mercado Libre",
    "falabella": "Falabella",
    "trendyol": "Trendyol",
    "hepsiburada": "Hepsiburada",
    "noon": "Noon",
}

def generate_tracking():
    entries = []
    for product in PRODUCTS:
        for market_code, market_info in MARKETS.items():
            for platform_code, platform_extra in market_info["platforms"].items():
                search_query = f"{product['brand']} {product['model']}"
                entry = {
                    "product_id": product["id"],
                    "market": market_code,
                    "market_name": market_info["name"],
                    "currency": market_info["currency"],
                    "platform": platform_code,
                    "platform_name": PLATFORM_NAMES[platform_code],
                    "search_query": search_query,
                    "url": "",
                    "item_id": "",
                }
                entry.update(platform_extra)
                entries.append(entry)
    return entries

def main():
    config = {
        "settings": {
            "feishu_webhook_url": "",
            "feishu_base_token": "",
            "feishu_base_table_id": "",
            "db_path": "price_history.db",
            "check_frequency": "daily",
            "request_delay_seconds": 1.5,
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
        "products": PRODUCTS,
        "tracking": generate_tracking(),
    }

    output_path = "config.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"Config generated: {output_path}")
    print(f"  Products: {len(PRODUCTS)}")
    print(f"  Markets:  {len(MARKETS)}")
    print(f"  Tracking entries: {len(config['tracking'])}")

if __name__ == "__main__":
    main()
