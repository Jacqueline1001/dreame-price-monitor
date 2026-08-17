# Dreame Price Monitor · 个护价格监控看板

跨市场个护产品（造型器 / 直板夹 / 吹风机）价格监控系统。盯住 Dreame、Dyson、Shark、BaBylissPRO、Remington、Laifen 的价格，变动自动通知飞书，数据沉淀为 HTML 看板。

## 覆盖市场与平台

| 市场 | Amazon | Mercado Libre | Trendyol / Hepsiburada | Noon |
|---|---|---|---|---|
| MX 墨西哥 | ✅ | 待接入 | - | - |
| BR 巴西 | ✅ | 待接入 | - | - |
| CO 哥伦比亚 | - | 待接入 | - | - |
| TR 土耳其 | - | - | 待直链 | - |
| AE 阿联酋 | ✅ | - | - | 待直链 |
| SA 沙特 | ✅ | - | - | 待直链 |

## 功能

- **价格监控**：每日定时抓取 Amazon MX/BR/AE/SA 四站价格（产品详情页直连，后续可切 Sorftime API 数据源）
- **飞书通知**：价格变动自动推送交互卡片到飞书群（webhook 或 Actions secret 配置）
- **HTML 看板**：白色极简硅谷风，自动生成，GitHub Pages 托管，可直接分享
- **历史记录**：SQLite 存储全量价格历史，支持变价检测

## 快速开始

```bash
pip install -r requirements.txt

# 编辑 config_amazon.json 填入飞书 webhook（可选）后：
python price_monitor.py --config config_amazon.json --db price_history.db
python generate_dashboard.py   # 生成 dashboard.html
```

## GitHub Actions 每日定时

`.github/workflows/price_monitor.yml` 每天 02:00 UTC（北京 10:00）自动运行。仓库 Secrets 配置：

| Secret | 用途 |
|---|---|
| `FEISHU_WEBHOOK_URL` | 飞书群机器人 webhook（可选，不配则不通知） |
| `SORFTIME_KEY` | Sorftime API key（可选，后续数据源切换用） |

## 配置说明

`config_amazon.json` 结构：`settings`（全局配置）+ `products`（产品清单）+ `tracking`（产品 × 市场 × 平台条目，含 `amazon_domain` 等站点参数）。

**注意**：`config_full.json` / `config_test.json` / `*.db` 已加入 `.gitignore`，不要提交含真实 webhook 的配置文件。

## 借鉴的开源项目

- [ompatel-io/price-tracker](https://github.com/ompatel-io/price-tracker) — undetected_chromedriver 反爬 + 详情页直连
- [erdenizkorkmaz/competitive-pricing-tracker](https://github.com/erdenizkorkmaz/competitive-pricing-tracker) — GitHub Actions 定时模板

详细设置见 [SETUP_GUIDE.md](./SETUP_GUIDE.md)。
