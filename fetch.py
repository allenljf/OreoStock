import yfinance as yf
import pandas as pd
import talib
import json

def fetch(symbol):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="1y")  # 取一年歷史
    return df, ticker

def compute(df, ticker):
    df['RSI'] = talib.RSI(df['Close'], timeperiod=14)
    df['K'], df['D'] = talib.STOCH(
        df['High'], df['Low'], df['Close'],
        fastk_period=9,
        slowk_period=3,
        slowd_period=3
    )
    df['MA20'] = talib.SMA(df['Close'], timeperiod=20)
    df['MA120'] = talib.SMA(df['Close'], timeperiod=120)
    df['MA240'] = talib.SMA(df['Close'], timeperiod=240)

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last  # 前一日數據
    
    # 計算今日漲跌幅
    change_percent = None
    if len(df) > 1 and prev['Close'] > 0:
        change_percent = ((last['Close'] - prev['Close']) / prev['Close']) * 100
    
    # 嘗試獲取本益比 (P/E ratio)
    pe = None
    try:
        info = ticker.info
        # 優先使用 trailingPE，如果沒有則使用 forwardPE
        pe = info.get('trailingPE') or info.get('forwardPE')
        if pe is not None:
            pe = float(pe)
    except:
        pass  # 如果獲取失敗，保持為 None
    
    return {
        "close": float(last['Close']),
        "change_percent": change_percent,
        "pe": pe,
        "rsi": float(last['RSI']),
        "k": float(last['K']),
        "d": float(last['D']),
        "ma20": float(last['MA20']),
        "ma120": float(last['MA120']),
        "ma240": float(last['MA240']),
    }

# 定義所有要監測的股票（按順序）
stocks_config = [
    {"key": "twii", "symbol": "^TWII", "name": "台股加權 (TWII)"},
    {"key": "tsmc", "symbol": "2330.TW", "name": "台積電 (TSMC)"},
    {"key": "etf0050", "symbol": "0050.TW", "name": "元大台灣50 (0050)"},
    {"key": "etf00631l", "symbol": "00631L.TW", "name": "元大台灣50正2 (00631L)"},
    {"key": "etf00675l", "symbol": "00675L.TW", "name": "富邦台50正2 (00675L)"},
    {"key": "nasdaq", "symbol": "^IXIC", "name": "NASDAQ (IXIC)"},
    {"key": "tqqq", "symbol": "TQQQ", "name": "ProShares UltraPro QQQ (TQQQ)"},
    {"key": "qld", "symbol": "QLD", "name": "ProShares Ultra QQQ (QLD)"},
    {"key": "nvda", "symbol": "NVDA", "name": "NVIDIA (NVDA)"},
    {"key": "msft", "symbol": "MSFT", "name": "Microsoft (MSFT)"},
    {"key": "goog", "symbol": "GOOG", "name": "Google (GOOG)"},
    {"key": "tsla", "symbol": "TSLA", "name": "Tesla (TSLA)"},
    {"key": "smh", "symbol": "SMH", "name": "SMH ETF"},
    {"key": "aapl", "symbol": "AAPL", "name": "Apple (AAPL)"},
    {"key": "amzn", "symbol": "AMZN", "name": "Amazon (AMZN)"},
    {"key": "meta", "symbol": "META", "name": "Meta (META)"},
    {"key": "btc", "symbol": "BTC-USD", "name": "Bitcoin (BTC)"},
    {"key": "gld", "symbol": "GLD", "name": "Gold ETF (GLD)"},
]

# 抓取所有股票數據
data = {}
for stock in stocks_config:
    try:
        df, ticker = fetch(stock["symbol"])
        stock_data = compute(df, ticker)
        data[stock["key"]] = stock_data
        print(f"✓ 成功獲取 {stock['name']} 數據")
    except Exception as e:
        print(f"✗ 獲取 {stock['name']} 數據失敗: {e}")
        # 如果獲取失敗，使用空數據
        data[stock["key"]] = {
            "close": None,
            "change_percent": None,
            "pe": None,
            "rsi": None,
            "k": None,
            "d": None,
            "ma20": None,
            "ma120": None,
            "ma240": None,
        }

# 生成 data.json 供 index.html 讀取
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
