#!/usr/bin/env python3
"""
Generate a self-contained HTML price dashboard from dashboard_data.json.
White minimalist Silicon Valley style (Linear/Vercel white), deployable to GitHub Pages.
"""
import json
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "dashboard_data.json")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "dashboard.html")

CURRENCY_SYMBOLS = {
    "MXN": "MXN$", "BRL": "R$", "COP": "COP$",
    "TRY": "TRY", "AED": "AED", "SAR": "SAR",
    "USD": "$",
}

CATEGORY_LABELS = {
    "styler": "造型工具 Styler",
    "flat_iron": "直板夹 Flat Iron",
    "hair_dryer": "吹风机 Hair Dryer",
}

def format_price(price, currency):
    if price is None:
        return "N/A"
    sym = CURRENCY_SYMBOLS.get(currency or "", currency or "")
    if isinstance(price, float) and price == int(price):
        price = int(price)
    return f"{sym} {price:,.0f}"

def generate():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    data_json = json.dumps(data, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>个护价格看板 | Personal Care Price Dashboard</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  :root {{
    --bg: #FAFAFA;
    --surface: #FFFFFF;
    --border: #E8E8EC;
    --border-hi: #D4D4D8;
    --text: #18181B;
    --text2: #71717A;
    --text3: #A1A1AA;
    --accent: #6D5BD0;
    --accent-soft: rgba(109,91,208,0.08);
    --accent-ink: #4F46A5;
    --red: #DC2626;
    --red-soft: rgba(220,38,38,0.08);
    --green: #059669;
    --green-soft: rgba(5,150,105,0.08);
    --amber: #B45309;
    --amber-soft: rgba(180,83,9,0.08);
    --blue: #2563EB;
    --blue-soft: rgba(37,99,235,0.08);
    --radius: 12px;
    --shadow: 0 1px 2px rgba(0,0,0,0.04), 0 1px 3px rgba(0,0,0,0.03);
  }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
    font-size: 14px;
    line-height: 1.6;
    padding: 40px 32px;
    -webkit-font-smoothing: antialiased;
  }}
  .container {{ max-width: 1160px; margin: 0 auto; }}

  /* Header */
  .header {{ margin-bottom: 28px; }}
  h1 {{ font-size: 22px; font-weight: 650; letter-spacing: -0.02em; margin-bottom: 6px; }}
  .subtitle {{ color: var(--text2); font-size: 13px; }}
  .subtitle .dot {{ color: var(--text3); margin: 0 6px; }}

  /* Summary bar */
  .summary-bar {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
    margin-bottom: 28px;
  }}
  .summary-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 18px 20px;
    box-shadow: var(--shadow);
  }}
  .summary-card .label {{ color: var(--text3); font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.06em; }}
  .summary-card .value {{ font-size: 26px; font-weight: 650; margin-top: 4px; letter-spacing: -0.02em; }}
  .summary-card .value.accent {{ color: var(--accent-ink); }}
  .summary-card .value.red {{ color: var(--red); }}

  /* Filters */
  .filters {{ display: flex; gap: 6px; margin-bottom: 18px; flex-wrap: wrap; align-items: center; }}
  .filter-group {{ display: flex; gap: 6px; align-items: center; }}
  .filter-sep {{ width: 1px; height: 20px; background: var(--border); margin: 0 8px; }}
  .filter-label {{ font-size: 11px; color: var(--text3); font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-right: 4px; }}
  .filter-btn {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 999px; padding: 5px 14px; color: var(--text2);
    cursor: pointer; font-size: 12.5px; font-family: inherit;
    transition: all 0.15s ease;
  }}
  .filter-btn:hover {{ border-color: var(--border-hi); color: var(--text); }}
  .filter-btn.active {{
    background: var(--accent-soft); border-color: var(--accent);
    color: var(--accent-ink); font-weight: 550;
  }}

  /* Table */
  .table-wrap {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow);
  }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{
    text-align: left; padding: 11px 16px; font-size: 11px;
    color: var(--text3); text-transform: uppercase; letter-spacing: 0.06em;
    border-bottom: 1px solid var(--border); background: #FCFCFD;
    font-weight: 550; white-space: nowrap;
  }}
  td {{ padding: 12px 16px; border-bottom: 1px solid #F4F4F5; font-size: 13px; }}
  tr:last-child td {{ border-bottom: none; }}
  tbody tr {{ transition: background 0.12s; }}
  tbody tr:hover {{ background: #FAFAFC; }}
  .price-cell {{ font-variant-numeric: tabular-nums; font-weight: 600; color: var(--text); }}
  .change-up {{ color: var(--red); }}
  .change-down {{ color: var(--green); }}
  .change-none {{ color: var(--text3); }}
  .badge {{
    display: inline-block; padding: 3px 10px; border-radius: 999px;
    font-size: 11px; font-weight: 550;
  }}
  .badge-styler {{ background: var(--accent-soft); color: var(--accent-ink); }}
  .badge-flat_iron {{ background: var(--amber-soft); color: var(--amber); }}
  .badge-hair_dryer {{ background: var(--blue-soft); color: var(--blue); }}
  .market-tag {{
    display: inline-block; padding: 2px 8px; border-radius: 6px;
    font-size: 11px; font-weight: 550; background: #F4F4F5;
    color: var(--text2);
  }}
  .link {{ color: var(--accent-ink); text-decoration: none; font-weight: 500; }}
  .link:hover {{ text-decoration: underline; }}

  /* Changes section */
  .changes-section {{ margin-top: 32px; }}
  .changes-section h2 {{ font-size: 15px; font-weight: 650; margin-bottom: 12px; letter-spacing: -0.01em; }}
  .change-item {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 14px 18px; margin-bottom: 8px;
    display: flex; align-items: center; justify-content: space-between;
    box-shadow: var(--shadow);
  }}
  .change-item .left {{ display: flex; flex-direction: column; gap: 1px; }}
  .change-item .product-name {{ font-weight: 600; font-size: 13.5px; }}
  .change-item .meta {{ color: var(--text2); font-size: 12px; }}
  .change-item .right {{ text-align: right; }}
  .change-item .price-diff {{ font-size: 15px; font-weight: 650; font-variant-numeric: tabular-nums; }}
  .empty-state {{ text-align: center; padding: 56px 24px; color: var(--text3); font-size: 13px; }}

  /* Footer */
  .footer {{
    margin-top: 28px; padding-top: 14px; border-top: 1px solid var(--border);
    color: var(--text3); font-size: 12px; display: flex; justify-content: space-between;
  }}

  @media (max-width: 720px) {{
    body {{ padding: 20px 16px; }}
    .summary-bar {{ grid-template-columns: repeat(2, 1fr); }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>个护价格看板</h1>
    <p class="subtitle">Personal Care Price Dashboard<span class="dot">·</span>6 Markets<span class="dot">·</span><span id="last-updated"></span></p>
  </div>

  <div class="summary-bar" id="summary-bar"></div>

  <div class="filters" id="filters"></div>

  <div class="table-wrap">
    <table id="price-table">
      <thead>
        <tr>
          <th>Product</th>
          <th>Category</th>
          <th>Market</th>
          <th>Platform</th>
          <th>Price</th>
          <th>Change</th>
          <th>Link</th>
        </tr>
      </thead>
      <tbody id="price-body"></tbody>
    </table>
  </div>

  <div class="changes-section" id="changes-section" style="display:none;">
    <h2>最近价格变动 Recent Changes</h2>
    <div id="changes-list"></div>
  </div>

  <div class="footer">
    <span>Auto-generated by Price Monitor</span>
    <span id="entry-count"></span>
  </div>
</div>

<script>
const DATA = {data_json};
const CAT_LABELS = {{
  styler: "造型工具",
  flat_iron: "直板夹",
  hair_dryer: "吹风机",
}};
const CUR_SYM = {{
  MXN: "MXN$", BRL: "R$", COP: "COP$",
  TRY: "TRY", AED: "AED", SAR: "SAR", USD: "$",
}};
const MARKETS = ["MX", "BR", "CO", "TR", "AE", "SA"];
const MARKET_NAMES = {{
  MX: "Mexico", BR: "Brazil", CO: "Colombia",
  TR: "Turkey", AE: "UAE", SA: "Saudi",
}};

let activeMarket = "ALL";
let activeCategory = "ALL";

function fmtPrice(price, cur) {{
  if (price === null || price === undefined) return "N/A";
  const sym = CUR_SYM[cur] || cur || "";
  const p = Number.isInteger(price) ? price : price.toFixed(0);
  return sym + " " + p.toLocaleString("en-US");
}}

function init() {{
  const latest = DATA.latest_prices || [];
  const changes = DATA.recent_changes || [];

  document.getElementById("last-updated").textContent =
    new Date(DATA.generated_at).toLocaleString("en-US", {{
      dateStyle: "medium", timeStyle: "short",
    }});

  // Summary cards
  const marketsActive = new Set(latest.map(p => p.market));
  const changesCount = changes.length;
  const totalProducts = new Set(latest.map(p => p.product_id)).size;

  const summaryBar = document.getElementById("summary-bar");
  summaryBar.innerHTML = `
    <div class="summary-card">
      <div class="label">Products Tracked</div>
      <div class="value accent">${{totalProducts}}</div>
    </div>
    <div class="summary-card">
      <div class="label">Markets Active</div>
      <div class="value">${{marketsActive.size}}<span style="font-size:14px;color:var(--text3)">/6</span></div>
    </div>
    <div class="summary-card">
      <div class="label">Price Entries</div>
      <div class="value">${{latest.length}}</div>
    </div>
    <div class="summary-card">
      <div class="label">Recent Changes</div>
      <div class="value ${{changesCount > 0 ? 'red' : ''}}">${{changesCount}}</div>
    </div>
  `;

  // Filter buttons
  const filterDiv = document.getElementById("filters");
  let btns = `<span class="filter-label">Market</span>`;
  btns += `<div class="filter-group"><button class="filter-btn active" data-market="ALL">All</button>`;
  MARKETS.forEach(m => {{
    if (marketsActive.has(m)) {{
      btns += `<button class="filter-btn" data-market="${{m}}">${{MARKET_NAMES[m]}}</button>`;
    }}
  }});
  btns += `</div>`;
  btns += `<div class="filter-sep"></div>`;
  btns += `<span class="filter-label">Category</span>`;
  btns += `<div class="filter-group"><button class="filter-btn active" data-cat="ALL">All</button>`;
  ["styler", "flat_iron", "hair_dryer"].forEach(c => {{
    if (latest.some(p => p.category === c)) {{
      btns += `<button class="filter-btn" data-cat="${{c}}">${{CAT_LABELS[c]}}</button>`;
    }}
  }});
  btns += `</div>`;
  filterDiv.innerHTML = btns;

  filterDiv.querySelectorAll("button").forEach(btn => {{
    btn.addEventListener("click", () => {{
      if (btn.dataset.market) {{
        activeMarket = btn.dataset.market;
        filterDiv.querySelectorAll("[data-market]").forEach(b =>
          b.classList.toggle("active", b.dataset.market === activeMarket));
      }}
      if (btn.dataset.cat) {{
        activeCategory = btn.dataset.cat;
        filterDiv.querySelectorAll("[data-cat]").forEach(b =>
          b.classList.toggle("active", b.dataset.cat === activeCategory));
      }}
      renderTable();
    }});
  }});

  renderTable();

  // Changes section
  if (changes.length > 0) {{
    const section = document.getElementById("changes-section");
    const list = document.getElementById("changes-list");
    section.style.display = "block";
    list.innerHTML = changes.map(c => {{
      const pct = c.change_pct || 0;
      const cls = pct > 0 ? "change-up" : pct < 0 ? "change-down" : "change-none";
      const arrow = pct > 0 ? "↑" : pct < 0 ? "↓" : "→";
      return `
        <div class="change-item">
          <div class="left">
            <span class="product-name">${{c.product_name}}</span>
            <span class="meta">${{c.market_name}} / ${{c.platform_name}}</span>
          </div>
          <div class="right">
            <div class="price-diff ${{cls}}">${{arrow}} ${{fmtPrice(c.old_price, c.currency)}} → ${{fmtPrice(c.price, c.currency)}}</div>
            <div class="meta ${{cls}}">${{pct > 0 ? "+" : ""}}${{pct.toFixed(1)}}%</div>
          </div>
        </div>
      `;
    }}).join("");
  }}
}}

function renderTable() {{
  const latest = DATA.latest_prices || [];
  const tbody = document.getElementById("price-body");

  const filtered = latest.filter(p => {{
    if (activeMarket !== "ALL" && p.market !== activeMarket) return false;
    if (activeCategory !== "ALL" && p.category !== activeCategory) return false;
    return true;
  }}).sort((a, b) => {{
    if (a.category !== b.category) return a.category.localeCompare(b.category);
    if (a.brand !== b.brand) return a.brand.localeCompare(b.brand);
    return a.market.localeCompare(b.market);
  }});

  document.getElementById("entry-count").textContent =
    `${{filtered.length}} / ${{latest.length}} entries`;

  if (filtered.length === 0) {{
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">暂无该筛选条件的数据 No data for this filter</td></tr>`;
    return;
  }}

  tbody.innerHTML = filtered.map(p => {{
    const pct = p.change_pct;
    let changeHtml = '<span class="change-none">—</span>';
    if (p.changed && pct !== null && pct !== undefined) {{
      const cls = pct > 0 ? "change-up" : pct < 0 ? "change-down" : "change-none";
      const arrow = pct > 0 ? "↑" : pct < 0 ? "↓" : "→";
      changeHtml = `<span class="${{cls}}">${{arrow}} ${{Math.abs(pct).toFixed(1)}}%</span>`;
    }}
    const catLabel = CAT_LABELS[p.category] || p.category;
    const link = p.url ? `<a class="link" href="${{p.url}}" target="_blank">查看 View</a>` : "—";
    return `
      <tr>
        <td>${{p.product_name}}</td>
        <td><span class="badge badge-${{p.category}}">${{catLabel}}</span></td>
        <td><span class="market-tag">${{p.market}}</span></td>
        <td>${{p.platform_name}}</td>
        <td class="price-cell">${{fmtPrice(p.price, p.currency)}}</td>
        <td>${{changeHtml}}</td>
        <td>${{link}}</td>
      </tr>
    `;
  }}).join("");
}}

init();
</script>
</body>
</html>"""

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard generated: {OUTPUT_PATH}")
    print(f"  Entries: {len(data.get('latest_prices', []))}")
    print(f"  Changes: {len(data.get('recent_changes', []))}")

if __name__ == "__main__":
    generate()
