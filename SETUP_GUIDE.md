# 个护价格看板 - Setup Guide

## 你需要提供的（Action Items）

项目由子明执行，以下按优先级列出「只有你能拿到的东西」：

### ✅ 立即能用（无需任何额外提供）
| 市场 | 平台 | 状态 |
|---|---|---|
| 墨西哥 MX | Amazon MX | ✅ 已跑通（MXN$） |
| 巴西 BR | Amazon BR | ✅ 已跑通（R$） |
| 阿联酋 AE | Amazon AE | ✅ 已跑通（AED） |
| 沙特 SA | Amazon SA | ✅ 已跑通（SAR） |

### ⏳ 需要你提供才能开通
| # | 市场 | 平台 | 你需要做什么 | 给我什么 |
|---|---|---|---|---|
| 1 | 土耳其 TR | Trendyol | 在 Trendyol 搜每个产品（Dyson Airwrap / Shark FlexStyle / Dreame 等），复制**产品详情页链接**（形如 `trendyol.com/xxx/dyson-airwrap-p-123456`） | 产品直链列表（10 个产品 × 1 条 = 约 10 条链接） |
| 2 | 土耳其 TR | Hepsiburada | 同上，搜产品复制详情页链接（形如 `hepsiburada.com/...-p-HB0000...`） | 产品直链列表 |
| 3 | 阿联酋 AE | Noon | 在 noon.com 搜产品，复制详情页链接 | 产品直链列表 |
| 4 | 沙特 SA | Noon | 同上 | 产品直链列表 |
| 5 | 拉美 3 国 | Mercado Libre | 去 developers.mercadolibre.com 免费注册个 App | `client_id` + `client_secret` |

> **为什么需要直链**：Trendyol/Noon/Hepsiburada 搜索页有强反爬（403/超时），但**详情页**通常能读到 schema.org 结构化数据（价格、货币）。直链绕开搜索，命中率最高。
> **如果直链仍被拦**：需要一台能访问这些站点的机器/代理跑脚本（子明的电脑或公司代理），或换 Playwright 无头浏览器方案。

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate config (120 tracking entries)
python generate_config.py

# 3. Run the monitor
python price_monitor.py

# 4. Open dashboard
open dashboard.html
```

## File Structure

```
price-dashboard/
├── config.json           # Product x Market x Platform tracking config (auto-generated)
├── generate_config.py    # Config generator (edit PRODUCTS / MARKETS here)
├── price_monitor.py      # Main script: fetch prices → SQLite → detect changes → notify
├── notify.py             # Feishu webhook notification module
├── generate_dashboard.py # HTML dashboard generator (auto-called by price_monitor.py)
├── dashboard.html        # Self-contained dashboard (auto-generated, deployable)
├── dashboard_data.json   # Raw JSON data for dashboard
├── price_history.db      # SQLite price history database
└── requirements.txt      # Python dependencies
```

## Feishu Notification Setup

### Step 1: Create a Feishu Group

1. Open Feishu → click "+" next to a group list
2. Create a new group named "个护价格监控" (or your preferred name)
3. Add team members who should receive price alerts

### Step 2: Add a Custom Bot

1. In the group, click the settings gear → "群机器人" (Group Bots)
2. Click "添加机器人" → "自定义机器人" (Custom Bot)
3. Name it "Price Monitor"
4. Copy the **Webhook URL** (format: `https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx`)
5. (Optional) Set a security verification keyword like "价格变动"

### Step 3: Configure the Webhook URL

Edit `config.json`:

```json
{
  "settings": {
    "feishu_webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_URL_HERE",
    ...
  }
}
```

Save and run `python price_monitor.py` — price changes will now send Feishu card messages.

## Feishu Base (多维表格) Setup [Optional]

If you want a Feishu Base as a team-shared dashboard:

### Step 1: Create a Base

1. Feishu → 工作台 → 多维表格 → New
2. Name it "个护价格监控看板"

### Step 2: Define Fields

| Field Name | Type | Notes |
|---|---|---|
| Product | Text | e.g., "Dreame Airstyle Pro" |
| Brand | Single Select | Dreame / Dyson / Shark / etc. |
| Category | Single Select | 造型工具 / 直板夹 / 吹风机 |
| Market | Single Select | MX / BR / CO / TR / AE / SA |
| Platform | Single Select | Amazon / Mercado Libre / etc. |
| Price | Number | Current price |
| Currency | Text | MXN / BRL / etc. |
| Old Price | Number | Previous price |
| Change % | Number | Percentage change |
| URL | URL | Product link |
| Updated At | DateTime | Last check time |

### Step 3: Get Base Token

1. Open the Base → click "..." → Get Link
2. Extract `app_token` from the URL: `https://xxx.feishu.cn/base/{app_token}`
3. Add to `config.json`:
```json
{
  "settings": {
    "feishu_base_token": "YOUR_APP_TOKEN",
    "feishu_base_table_id": "tblXXXXXX",
    ...
  }
}
```

## Data Source Status（2026-08-17 实测）

| Platform | Markets | Method | Status |
|---|---|---|---|
| Amazon | MX, BR | Web scraping | ✅ Working |
| Amazon | AE, SA | Web scraping | ✅ Working (2026-08-17 验证通过) |
| Trendyol | TR | 产品直链 scraping | ⚠️ 搜索页 403，需要你提供产品详情页直链 |
| Noon | AE, SA | 产品直链 scraping | ⚠️ 超时，需要你提供产品详情页直链 |
| Hepsiburada | TR | 产品直链 scraping | ⚠️ 超时，需要你提供产品详情页直链 |
| Mercado Libre | MX, BR, CO | API (需认证) | ⚠️ 403，需要你注册 ML 开发者 App |
| Falabella | CO | Web scraping | 未测 |

### 解锁被拦数据源

**Mercado Libre API（免费）**:
1. 注册 https://developers.mercadolibre.com/
2. 创建 App → 拿到 `client_id` 和 `client_secret`
3. 填进 `config.json` 的 `settings.ml_client_id` / `ml_client_secret`
4. 脚本会自动认证并走官方搜索 API（拉美 3 国最稳）

**Trendyol / Noon / Hepsiburada（产品直链优先）**:
- 首选：把产品详情页 URL 填进 `config.json` 对应条目的 `"url"` 字段（脚本会跳过搜索、直接抓详情页）
- 兜底：Playwright 无头浏览器（`pip install playwright && playwright install chromium`）
- 兜底：换能访问这些站点的网络环境跑（子明的电脑/公司代理）

## Automation (Daily Run)

### Option A: WorkBuddy Automation

Set up a recurring automation in WorkBuddy:
- Schedule: Daily at 09:00 (or your preferred time)
- Prompt: "Run the price monitor script at /path/to/price_monitor.py and summarize any price changes detected"

### Option B: Cron Job (macOS)

```bash
# Edit crontab
crontab -e

# Add: run daily at 9:00 AM
0 9 * * * cd /path/to/price-dashboard && /path/to/python price_monitor.py >> price_monitor.log 2>&1
```

## Adding New Products

Edit `generate_config.py`:

```python
PRODUCTS = [
    ...existing products...
    {"id": "new-product-id", "brand": "Brand", "model": "Model", "category": "styler"},
]
```

Then run:
```bash
python generate_config.py
```

## Adding New Markets or Platforms

Edit `generate_config.py`:

```python
MARKETS = {
    ...existing markets...
    "CL": {"name": "Chile", "currency": "CLP", "platforms": {
        "mercadolibre": {"ml_site": "MLC"},
        "falabella": {},
    }},
}
```

Then regenerate config.
