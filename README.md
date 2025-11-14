# OreoStock - 股票指標自動化監測平台(每日更新)

## 📋 專案簡介

OreoStock 是一個自動化的股票指標監測平台，透過 GitHub Actions 每天定時爬取台股加權指數（TWII）和美股 NASDAQ（IXIC）的技術指標數據，並自動更新網頁顯示。

## 🔄 專案運作原理

### 整體架構流程

```
GitHub Actions (定時觸發)
    ↓
執行 Python 爬蟲腳本 (fetch.py)
    ↓
從 yfinance API 獲取股票數據
    ↓
計算技術指標 (RSI, K/D, 移動平均線等)
    ↓
生成 data.json 檔案
    ↓
自動 Commit 並 Push 到 GitHub
    ↓
網頁 (index.html) 讀取 data.json 並顯示
```

### 詳細運作流程

#### 1. **GitHub Actions 自動觸發**

- **觸發方式**：
  - 定時觸發：每天 UTC 22:00（台灣時間早上 6:00）自動執行
  - 手動觸發：可在 GitHub Actions 頁面手動執行 workflow

- **Workflow 設定**：`.github/workflows/update.yml`
  ```yaml
  on:
    schedule:
      - cron: "0 22 * * *"  # 每天 UTC 22:00
    workflow_dispatch:       # 允許手動執行
  ```

#### 2. **環境準備與依賴安裝**

Workflow 會自動：
- 設定 Python 3.12 環境
- 安裝必要的套件：
  - `pandas`：數據處理
  - `yfinance`：Yahoo Finance API 爬蟲
  - `ta-lib`：技術指標計算庫

#### 3. **數據爬取與計算** (`fetch.py`)

**步驟 A：獲取歷史數據**
```python
def fetch(symbol):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="1y")  # 取一年歷史數據
    return df
```

**步驟 B：計算技術指標**
- **RSI (相對強弱指標)**：14 日週期，判斷超買超賣
- **K/D 值 (隨機指標)**：9/3/3 參數，判斷趨勢轉折
- **移動平均線**：
  - MA20：月線（20 日）
  - MA120：半年線（120 日）
  - MA240：年線（240 日）

**步驟 C：生成 JSON 數據**
```python
data = {
    "twii": { "close": ..., "rsi": ..., ... },
    "nasdaq": { "close": ..., "rsi": ..., ... }
}
# 寫入 data.json
```

#### 4. **自動 Commit 與 Push**

Workflow 使用內建的 `GITHUB_TOKEN` 自動：
- 將 `data.json` 加入 Git
- Commit 變更（訊息："Update stock dashboard"）
- Push 到 main 分支

**權限設定**：
- Workflow 需要 `contents: write` 權限才能寫入 repository
- 使用 `GITHUB_TOKEN` 無需額外設定，更安全

#### 5. **網頁動態顯示** (`index.html`)

- 網頁使用 JavaScript 的 `fetch()` API 讀取 `data.json`
- 動態渲染表格，顯示所有技術指標
- 使用 `?ts=` 參數避免瀏覽器快取問題

## 📊 監測指標說明

| 指標 | 說明 | 用途 |
|------|------|------|
| **收盤價** | 當日收盤價格 | 基本價格資訊 |
| **RSI** | 相對強弱指標 (14日) | 判斷超買(>70)或超賣(<30) |
| **K 值** | 隨機指標快速線 | 判斷短期趨勢 |
| **D 值** | 隨機指標慢速線 | 判斷中期趨勢 |
| **月線 (20MA)** | 20 日移動平均 | 短期趨勢判斷 |
| **半年線 (120MA)** | 120 日移動平均 | 中期趨勢判斷 |
| **年線 (240MA)** | 240 日移動平均 | 長期趨勢判斷 |

## 🛠️ 技術棧

- **後端爬蟲**：Python 3.12
- **數據來源**：Yahoo Finance (yfinance)
- **技術指標**：TA-Lib
- **自動化**：GitHub Actions
- **前端顯示**：HTML + JavaScript
- **數據格式**：JSON

## 📁 專案結構

```
OreoStock/
├── .github/
│   └── workflows/
│       └── update.yml      # GitHub Actions 工作流程
├── fetch.py                # Python 爬蟲與計算腳本
├── index.html              # 網頁顯示介面
├── data.json               # 自動生成的數據檔案（由 workflow 產生）
└── README.md               # 專案說明文件
```

## 🚀 使用方式

### 查看最新數據

1. 開啟 GitHub Pages 或直接查看 `index.html`
2. 網頁會自動讀取最新的 `data.json` 並顯示數據

### 手動觸發更新

1. 前往 GitHub Repository 的 **Actions** 頁面
2. 選擇 **Daily Update** workflow
3. 點擊 **Run workflow** 按鈕手動執行

## ⚙️ 設定說明

### 修改更新時間

編輯 `.github/workflows/update.yml` 中的 cron 表達式：
```yaml
schedule:
  - cron: "0 22 * * *"  # 格式：分 時 日 月 星期
```

### 添加更多股票

修改 `fetch.py`：
```python
# 添加新的股票代號
new_stock_data = compute(fetch("^新股票代號"))
data["新股票"] = { ... }
```

並更新 `index.html` 的顯示邏輯。

## 🔒 安全性

- 使用 GitHub 內建的 `GITHUB_TOKEN`，無需額外管理 API Key
- Token 在 workflow 結束後自動失效
- 所有數據來源於公開的 Yahoo Finance API

## 📝 注意事項

- 數據更新時間為每天 UTC 22:00（台灣時間早上 6:00）
- 市盈率 (PE) 欄位目前顯示為 N/A，因為 yfinance 可能不提供此數據
- 所有數值顯示為小數點後一位
- 網頁會自動避免快取，確保顯示最新數據

## 📄 授權

本專案僅供學習與個人使用。

1️⃣ RSI（Relative Strength Index，相對強弱指標）

計算概念：RSI 是衡量一段時間內價格上漲與下跌的強弱比，通常用 14日 RSI。
	•	RSI = 100 × (平均漲幅 / (平均漲幅 + 平均跌幅))
	•	值範圍：0~100

解讀方式：
	•	RSI > 70 → 超買，股價可能短期過高，需注意回調
	•	RSI < 30 → 超賣，股價可能短期過低，可能出現反彈
	•	50 附近 → 市場中性，沒有明顯趨勢

⚠️ 注意：RSI 高不一定立刻跌，RSI 低也不一定立刻漲，它偏向趨勢強弱參考。

⸻

2️⃣ K, D 值（隨機指標 Stochastic Oscillator）

計算概念：用最高價、最低價與收盤價之間的位置，衡量股價動能。
	•	K = （當日收盤價 - N日最低價） / (N日最高價 - N日最低價) × 100
	•	D = K 的 N 日移動平均

解讀方式：
	•	K 或 D > 80 → 超買區，可能反轉向下
	•	K 或 D < 20 → 超賣區，可能反轉向上
	•	K 與 D 黃金交叉（K 上穿 D） → 買訊
	•	K 與 D 死亡交叉（K 下穿 D） → 賣訊

K, D 對短期價格動作比較敏感，比 RSI 更適合捕捉短線波動。

⸻

3️⃣ MA（Moving Average，移動平均線）
	•	MA20 → 20日平均線 → 短期趨勢
	•	MA120 → 120日平均線 → 中期趨勢
	•	MA240 → 240日平均線 → 長期趨勢

解讀方式：
	•	價格 > MA → 上漲趨勢
	•	價格 < MA → 下跌趨勢
	•	MA 短期上穿長期 → 多頭訊號（黃金交叉）
	•	MA 短期下穿長期 → 空頭訊號（死亡交叉）

搭配使用：
	•	MA20 與 MA120/MA240 比較，可看短期趨勢與中長期趨勢是否一致
	•	例如：價格突破 MA20 且 MA20 > MA120 → 短期上攻可能延續