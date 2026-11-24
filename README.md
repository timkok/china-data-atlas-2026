# 中国数据地图

中国大陆 31 个省级地区的公开年度统计。数字来自国家统计局《中国统计年鉴》，每条观测带表名和网址。缺年留空，不插值。

这一版不发布中国地图。浏览用分区瓦片和排名，原因见 `docs/map-compliance.md`。

## 数据

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
# 已提交原始 Excel 时可离线重建
python3 -m pipeline.run_all --offline
python3 -m pipeline.qa
pytest tests -q
```

首次从年鉴网站补抓 Excel（不会访问被拒绝的 data.stats.gov.cn，也不会覆盖 `data/manual/`）：

```bash
python3 -m pipeline.run_all
```

产物：

- `data/processed/observations.csv` 与 `.parquet`
- `data/qa/report.json`
- `web/data/` 供页面读取的 JSON
- `web/public/downloads/` CSV
- `docs/data-dictionary.md`、`docs/source-inventory.md`

人工核对过的 2025 年鉴印本在 `data/manual/transcribe_2025.py`，构建时写成 CSV。自动流程读这些文件，不改写它们。

## 网站

```bash
cd web
npm ci
npm run build
npm start
```

开发时用 `npm run dev`。浏览器测试（需先 build）：

```bash
cd web
npx playwright install chromium
npx playwright test
```

## 范围

统计范围是中国大陆 31 个省级地区。香港、澳门、台湾不在本数据集内；没有这些数字不是关于领土的表述。

地区代码用 GB/T 2260 省级 6 位码。`000000` 只表示年鉴里的全国合计。
