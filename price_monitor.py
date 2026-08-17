#!/usr/bin/env python3
"""
Personal Care Price Monitor
Tracks product prices across 6 markets x multiple e-commerce platforms.
- Mercado Libre: official API (free, no auth)
- Amazon: web scraping with structured data extraction
- Trendyol/Noon/Falabella/Hepsiburada: generic scraping
"""
import json
import sqlite3
import time
import re
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
DB_PATH = os.path.join(SCRIPT_DIR, "price_history.db")

# ---------------------------------------------------------------------------
# Config & DB
# ---------------------------------------------------------------------------

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id    TEXT NOT NULL,
            product_name  TEXT NOT NULL,
            brand         TEXT NOT NULL,
            category      TEXT NOT NULL,
            market        TEXT NOT NULL,
            market_name   TEXT NOT NULL,
            platform      TEXT NOT NULL,
            platform_name TEXT NOT NULL,
            price         REAL,
            currency      TEXT,
            url           TEXT,
            fetched_at    TEXT NOT NULL,
            changed       INTEGER DEFAULT 0,
            old_price     REAL,
            change_pct    REAL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_pmp
        ON price_history(product_id, market, platform)
    """)
    return conn

# ---------------------------------------------------------------------------
# Mercado Libre API (Mexico MLB, Brazil MLB, Colombia MCO)
# ---------------------------------------------------------------------------

def fetch_mercadolibre(site, search_query, user_agent):
    """Fetch price from Mercado Libre search API."""
    api_url = f"https://api.mercadolibre.com/sites/{site}/search"
    params = {"q": search_query, "limit": 5}
    headers = {"User-Agent": user_agent}

    try:
        resp = requests.get(api_url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return None, None, None, "No results"

        # Prefer new condition; pick first relevant match
        best = None
        for r in results:
            if r.get("condition") == "new" and search_query.split()[0].lower() in r.get("title", "").lower():
                best = r
                break
        if not best:
            for r in results:
                if r.get("condition") == "new":
                    best = r
                    break
        if not best:
            best = results[0]

        return (best.get("price"), best.get("currency_id"),
                best.get("permalink"), None)
    except Exception as e:
        return None, None, None, str(e)

# ---------------------------------------------------------------------------
# Amazon scraper (MX com.mx, BR com.br, AE ae, SA sa)
# ---------------------------------------------------------------------------

def parse_price(text, currency=None):
    """Parse price from text, handling different locale formats.
    BR: R$ 5.154,63 -> 5154.63 (dot=thousands, comma=decimal)
    MX: $9,999.00 -> 9999.00 (comma=thousands, dot=decimal)
    """
    text = text.replace("\xa0", " ").strip()
    m = re.search(r"[\d.,]+", text)
    if not m:
        return None
    num_str = m.group()

    if currency == "BRL":
        num_str = num_str.replace(".", "").replace(",", ".")
    elif currency in ("MXN", "AED", "SAR", "USD", "EUR", "TRY", "COP"):
        num_str = num_str.replace(",", "")
    else:
        if "," in num_str and "." in num_str:
            if num_str.rfind(",") > num_str.rfind("."):
                num_str = num_str.replace(".", "").replace(",", ".")
            else:
                num_str = num_str.replace(",", "")
        elif "," in num_str:
            parts = num_str.split(",")
            if len(parts) == 2 and len(parts[1]) <= 2:
                num_str = num_str.replace(",", ".")
            else:
                num_str = num_str.replace(",", "")
    try:
        return float(num_str)
    except ValueError:
        return None


def fetch_amazon(domain, search_query, user_agent):
    """Fetch price from Amazon search results using product cards.
    Retries on transient 503s; excludes accessory/knockoff listings via title filtering."""
    search_url = f"https://www.amazon.{domain}/s"
    params = {"k": search_query}
    headers = {
        "User-Agent": user_agent,
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8,pt;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    currency_map = {
        "com.mx": "MXN", "com.br": "BRL",
        "ae": "AED", "sa": "SAR",
    }
    currency = currency_map.get(domain, "USD")

    # Keywords that indicate an accessory / spare part / knockoff, not the main device
    # (EN + ES + PT + TR + AR variants — Amazon BR/AE/SA/MX use these languages)
    exclude_kw = [
        # English
        "attachment", "accessory", "accessories", "case", "cover", "barrel",
        "diffuser", "comb", "brush", "filter", "replacement", "piece",
        "holder", "stand", "travel bag", "pouch", "clon", "copia", "nozzle",
        "concentrator", "paddle", "pad", "pads", "kit", "set", "sleeve",
        "protector", "cradle", "spare", "genuine", "compatible", "for dyson",
        "for airwrap", "for corrale", "for supersonic", "universal",
        # Spanish
        "accesorio", "accesorios", "estuche", "funda", "boquilla", "difusor",
        "peine", "cepillo", "bolsa", "tapa", "compatible", "para dyson",
        "para airwrap", "para corrale", "kit de", "set de accesorios",
        "protector", "carcasa", "repuesto", "clon", "copia",
        # Portuguese
        "capa", "estojo", "estojos", "acessório", "acessórios", "compatível",
        "compativel", "bico", "difusor", "pente", "escova", "bolsa", "tampa",
        "proteção", "protecao", "para dyson", "para airwrap", "para corrale",
        # Turkish
        "kılıf", "kilif", "kapak", "çanta", "canta", "fırça", "firca", "yedek",
        "adaptör", "adaptor", "uyumlu",
        # Arabic (transliterated + actual)
        "ghita", "hakeeba", "compatible", "amazon basics",
    ]

    def _try_fetch():
        try:
            resp = requests.get(search_url, params=params, headers=headers, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Find product cards
            cards = soup.select('div[data-component-type="s-search-result"]')
            if not cards:
                return None, None, None, "No product cards found"

            query_lower = search_query.lower()
            query_words = [w.lower() for w in search_query.split()]

            best_match = None
            best_score = 0
            for card in cards:
                title_el = card.select_one("h2 a span, h2 span, h2 span.a-size-base-plus")
                price_el = card.select_one("span.a-price span.a-offscreen")
                link_el = card.select_one("h2 a")

                if not title_el or not price_el:
                    continue
                title = title_el.get_text(strip=True)
                title_lower = title.lower()

                # Skip accessory / knockoff listings outright
                if any(kw in title_lower for kw in exclude_kw):
                    continue

                price_text = price_el.get_text(strip=True)
                price = parse_price(price_text, currency)
                if price is None:
                    continue

                # Score match: how many query words appear in title
                score = sum(1 for w in query_words if w in title_lower)
                # Bonus for brand name match (first word)
                if query_words and query_words[0] in title_lower:
                    score += 2

                if score > best_score:
                    best_score = score
                    best_match = {
                        "title": title,
                        "price": price,
                        "currency": currency,
                        "url": "",
                    }
                    if link_el:
                        href = link_el.get("href", "")
                        best_match["url"] = f"https://www.amazon.{domain}{href.split('?')[0]}"

            if best_match and best_score >= 2:
                return best_match["price"], best_match["currency"], best_match["url"], None

            return None, None, None, "No matching product found (score too low)"
        except Exception as e:
            return None, None, None, str(e)

    # Retry on transient 503 / network errors
    last_error = None
    for attempt in range(3):
        try:
            result = _try_fetch()
            if result[0] is not None or "No matching" in (result[3] or ""):
                return result
            last_error = result[3]
        except Exception as e:
            last_error = str(e)
        time.sleep(3 * (attempt + 1))  # 3s, 6s backoff

    return None, None, None, f"Failed after 3 attempts: {last_error}"

# ---------------------------------------------------------------------------
# Generic scraper: Trendyol, Hepsiburada, Noon, Falabella
# ---------------------------------------------------------------------------

PLATFORM_SEARCH_URLS = {
    "trendyol":    "https://www.trendyol.com/sr?q={q}",
    "hepsiburada": "https://www.hepsiburada.com/ara?q={q}",
    "noon":        "https://www.noon.com/search?q={q}",
    "falabella":   "https://www.falabella.com.co/falabella-co/search?Ntt={q}",
}

PRICE_SELECTORS = [
    "[data-price]",
    ".prc-dsc",
    ".product-price .value",
    ".price .value",
    ".actual-price",
    ".formatted-money",
    ".money-amount",
    ".price-current",
    ".price-text",
    "span[data-qa*='price']",
    "div[data-qa*='price']",
]

def fetch_generic(platform, search_query, url, user_agent):
    """Fetch price from generic e-commerce platform."""
    if url:
        target = url
    else:
        template = PLATFORM_SEARCH_URLS.get(platform)
        if not template:
            return None, None, None, f"No search template for {platform}"
        target = template.format(q=search_query.replace(" ", "+"))

    headers = {
        "User-Agent": user_agent,
        "Accept-Language": "en-US,en;q=0.9,tr;q=0.8,es;q=0.8,pt;q=0.8,ar;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        resp = requests.get(target, headers=headers, timeout=20,
                           allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # 1) Try structured data (schema.org/Product)
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") in ("Product", "ProductGroup", "ItemList"):
                        if item.get("@type") == "ItemList":
                            elems = item.get("itemListElement", [])
                            if elems and isinstance(elems[0], dict):
                                prod = elems[0].get("item", {})
                                offers = prod.get("offers", {})
                                price = offers.get("price") or offers.get("lowPrice")
                                currency = offers.get("priceCurrency")
                                if price:
                                    return float(price), currency, target, None
                        else:
                            offers = item.get("offers", {})
                            if isinstance(offers, list):
                                offers = offers[0]
                            price = offers.get("price") or offers.get("lowPrice")
                            currency = offers.get("priceCurrency")
                            if price:
                                return float(price), currency, target, None
            except (json.JSONDecodeError, TypeError):
                continue

        # 2) Fallback: common price selectors
        for sel in PRICE_SELECTORS:
            el = soup.select_one(sel)
            if el:
                raw = el.get_text(strip=True).replace("\xa0", " ")
                m = re.search(r"([\d.,]+)", raw)
                if m:
                    price_str = m.group(1).replace(".", "").replace(",", "")
                    try:
                        price = float(price_str)
                    except ValueError:
                        try:
                            price = float(m.group(1).replace(",", ""))
                        except ValueError:
                            continue
                    return price, None, target, None

        return None, None, None, "Price not found on page"
    except Exception as e:
        return None, None, None, str(e)

# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Personal Care Price Monitor")
    parser.add_argument("--config", default=None,
                        help="Path to config JSON (default: config.json next to script)")
    parser.add_argument("--db", default=None,
                        help="Path to SQLite DB (default: price_history.db next to script)")
    args = parser.parse_args()

    global CONFIG_PATH, DB_PATH
    if args.config:
        CONFIG_PATH = os.path.abspath(args.config)
    if args.db:
        DB_PATH = os.path.abspath(args.db)

    config = load_config()
    settings = config.get("settings", {})
    user_agent = settings.get("user_agent", "Mozilla/5.0")
    delay = settings.get("request_delay_seconds", 1.5)

    db = get_db()
    cursor = db.cursor()

    products = {p["id"]: p for p in config["products"]}
    tracking = config["tracking"]

    changes = []
    checked = 0
    errors = 0

    for i, entry in enumerate(tracking):
        product = products.get(entry["product_id"])
        if not product:
            continue

        platform = entry["platform"]
        pname = f"{product['brand']} {product['model']}"

        # Dispatch to the right fetcher
        if platform == "mercadolibre":
            price, currency, url, error = fetch_mercadolibre(
                entry.get("ml_site", ""), entry["search_query"], user_agent)
        elif platform == "amazon":
            price, currency, url, error = fetch_amazon(
                entry.get("amazon_domain", ""), entry["search_query"], user_agent)
        else:
            price, currency, url, error = fetch_generic(
                platform, entry["search_query"],
                entry.get("url", ""), user_agent)

        if error or price is None:
            errors += 1
            print(f"[SKIP] {pname} @ {entry['market']}/{platform}: {error}")
            time.sleep(delay)
            continue

        checked += 1

        # Get last known price
        cursor.execute("""
            SELECT price FROM price_history
            WHERE product_id=? AND market=? AND platform=?
            ORDER BY fetched_at DESC LIMIT 1
        """, (entry["product_id"], entry["market"], platform))
        row = cursor.fetchone()
        old_price = row[0] if row else None

        changed = 0
        old_price_val = None
        change_pct = None

        if old_price is not None and abs(price - old_price) > 0.01:
            changed = 1
            old_price_val = old_price
            if old_price != 0:
                change_pct = round((price - old_price) / old_price * 100, 2)

        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO price_history
            (product_id, product_name, brand, category, market, market_name,
             platform, platform_name, price, currency, url, fetched_at,
             changed, old_price, change_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry["product_id"], pname,
            product["brand"], product["category"],
            entry["market"], entry["market_name"],
            platform, entry["platform_name"],
            price, currency, url or "", now,
            changed, old_price_val, change_pct,
        ))

        if changed:
            changes.append({
                "product": pname,
                "category": product["category"],
                "market": entry["market_name"],
                "platform": entry["platform_name"],
                "old_price": old_price,
                "new_price": price,
                "currency": currency,
                "change_pct": change_pct,
                "url": url or "",
            })
            symbol = "+" if change_pct > 0 else ""
            print(f"[CHANGE] {pname} @ {entry['market_name']}/{entry['platform_name']}: "
                  f"{old_price:,.0f} -> {price:,.0f} ({symbol}{change_pct}%)")
        else:
            print(f"[OK] {pname} @ {entry['market_name']}/{entry['platform_name']}: "
                  f"{price:,.0f} {currency or ''}")

        # Commit incrementally so a partial run still saves data
        if (i + 1) % 5 == 0:
            db.commit()

        time.sleep(delay)

    db.commit()
    db.close()

    # Send Feishu notifications
    from notify import send_price_change_notifications, send_summary
    if changes:
        send_price_change_notifications(changes, config)
    send_summary(checked, changes, config)

    # Export for dashboard
    export_for_dashboard()

    # Generate HTML dashboard
    try:
        from generate_dashboard import generate
        generate()
    except Exception as e:
        print(f"[DASHBOARD] Error generating dashboard: {e}")

    print(f"\n{'='*60}")
    print(f"Checked: {checked}/{len(tracking)} | Errors: {errors} | Changes: {len(changes)}")
    print(f"Database: {DB_PATH}")

# ---------------------------------------------------------------------------
# Dashboard data export
# ---------------------------------------------------------------------------

def export_for_dashboard():
    """Export latest prices + recent changes as JSON for the HTML dashboard."""
    db = get_db()
    cursor = db.cursor()

    # Latest price per product x market x platform
    cursor.execute("""
        SELECT * FROM price_history p1
        WHERE id = (
            SELECT MAX(id) FROM price_history p2
            WHERE p1.product_id = p2.product_id
            AND p1.market = p2.market
            AND p1.platform = p2.platform
        )
        ORDER BY category, brand, market, platform
    """)
    columns = [d[0] for d in cursor.description]
    latest = [dict(zip(columns, r)) for r in cursor.fetchall()]

    # Recent changes (last 30 entries with changed=1)
    cursor.execute("""
        SELECT * FROM price_history
        WHERE changed = 1
        ORDER BY fetched_at DESC
        LIMIT 30
    """)
    recent_changes = [dict(zip(columns, r)) for r in cursor.fetchall()]

    # Price history for charts (last 30 days)
    cursor.execute("""
        SELECT product_id, market, platform, price, fetched_at
        FROM price_history
        WHERE fetched_at > datetime('now', '-30 days')
        ORDER BY fetched_at ASC
    """)
    history_rows = [dict(zip(["product_id","market","platform","price","fetched_at"], r))
                    for r in cursor.fetchall()]

    data = {
        "generated_at": datetime.now().isoformat(),
        "latest_prices": latest,
        "recent_changes": recent_changes,
        "price_history": history_rows,
    }

    out_path = os.path.join(SCRIPT_DIR, "dashboard_data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    db.close()
    print(f"Dashboard data exported: {out_path} ({len(latest)} entries)")

if __name__ == "__main__":
    main()
