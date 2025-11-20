import yfinance as yf
import pandas as pd
import talib
import json

def fetch(symbol):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="1y")  # 取一年歷史
    return df, ticker

def calculate_kdj(df, n=9):
    """
    計算KDJ指標
    參數: (9, 3, 3)
    - n: RSV計算週期 (預設9天)
    - K值平滑係數: 1/3
    - D值平滑係數: 1/3
    """
    # 計算RSV (Raw Stochastic Value)
    low_list = df['Low'].rolling(window=n, min_periods=n).min()
    high_list = df['High'].rolling(window=n, min_periods=n).max()
    
    rsv = (df['Close'] - low_list) / (high_list - low_list) * 100
    
    # 初始化K, D, J列
    k_values = []
    d_values = []
    j_values = []
    
    prev_k = 50  # 初始K值
    prev_d = 50  # 初始D值
    
    for i in range(len(df)):
        if pd.isna(rsv.iloc[i]):
            k_values.append(None)
            d_values.append(None)
            j_values.append(None)
        else:
            # 當日K值 = 2/3×前一日K值 + 1/3×當日RSV
            k = (2/3) * prev_k + (1/3) * rsv.iloc[i]
            # 當日D值 = 2/3×前一日D值 + 1/3×當日K值
            d = (2/3) * prev_d + (1/3) * k
            # 當日J值 = 3×當日K值 - 2×當日D值
            j = 3 * k - 2 * d
            
            k_values.append(k)
            d_values.append(d)
            j_values.append(j)
            
            prev_k = k
            prev_d = d
    
    df['K'] = k_values
    df['D'] = d_values
    df['J'] = j_values
    
    return df

def detect_peaks(series, window=5):
    """
    檢測序列中的峰值(局部最大值)和谷值(局部最小值)
    返回: (peaks_indices, troughs_indices)
    """
    peaks = []
    troughs = []
    
    for i in range(window, len(series) - window):
        # 檢查是否為峰值
        is_peak = True
        is_trough = True
        
        for j in range(i - window, i + window + 1):
            if j != i:
                if series.iloc[i] <= series.iloc[j]:
                    is_peak = False
                if series.iloc[i] >= series.iloc[j]:
                    is_trough = False
        
        if is_peak:
            peaks.append(i)
        if is_trough:
            troughs.append(i)
    
    return peaks, troughs

def detect_signals(df):
    """
    檢測KDJ信號:
    1. 黃金交叉 (Golden Cross)
    2. 死亡交叉 (Death Cross)
    3. 頂背離 (Top Divergence)
    4. 底背離 (Bottom Divergence)
    """
    signals = {
        "golden_cross": False,
        "death_cross": False,
        "top_divergence": False,
        "bottom_divergence": False
    }
    
    if len(df) < 2:
        return signals
    
    # 獲取最近兩天的數據
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 檢查是否有有效的KDJ值
    if pd.isna(curr['K']) or pd.isna(curr['D']) or pd.isna(curr['J']):
        return signals
    if pd.isna(prev['K']) or pd.isna(prev['D']) or pd.isna(prev['J']):
        return signals
    
    # 1. 黃金交叉: K、J線同時向上突破D線
    if (prev['K'] <= prev['D'] and curr['K'] > curr['D'] and 
        prev['J'] <= prev['D'] and curr['J'] > curr['D']):
        signals["golden_cross"] = True
    
    # 2. 死亡交叉: K、J線同時向下突破D線
    if (prev['K'] >= prev['D'] and curr['K'] < curr['D'] and 
        prev['J'] >= prev['D'] and curr['J'] < curr['D']):
        signals["death_cross"] = True
    
    # 3 & 4. 背離檢測 - 需要足夠的歷史數據
    if len(df) >= 20:
        # 檢測價格和KDJ的峰值
        price_peaks, price_troughs = detect_peaks(df['Close'], window=3)
        kdj_peaks, kdj_troughs = detect_peaks(df['K'], window=3)
        
        # 頂背離: 股價峰值上升,但KDJ峰值下降
        if len(price_peaks) >= 2 and len(kdj_peaks) >= 2:
            last_price_peak_idx = price_peaks[-1]
            prev_price_peak_idx = price_peaks[-2]
            last_kdj_peak_idx = kdj_peaks[-1]
            prev_kdj_peak_idx = kdj_peaks[-2]
            
            # 確保峰值在合理的時間範圍內
            if (len(df) - last_price_peak_idx <= 5 and 
                df['Close'].iloc[last_price_peak_idx] > df['Close'].iloc[prev_price_peak_idx] and
                df['K'].iloc[last_kdj_peak_idx] < df['K'].iloc[prev_kdj_peak_idx]):
                signals["top_divergence"] = True
        
        # 底背離: 股價谷值下降,但KDJ谷值上升
        if len(price_troughs) >= 2 and len(kdj_troughs) >= 2:
            last_price_trough_idx = price_troughs[-1]
            prev_price_trough_idx = price_troughs[-2]
            last_kdj_trough_idx = kdj_troughs[-1]
            prev_kdj_trough_idx = kdj_troughs[-2]
            
            # 確保谷值在合理的時間範圍內
            if (len(df) - last_price_trough_idx <= 5 and 
                df['Close'].iloc[last_price_trough_idx] < df['Close'].iloc[prev_price_trough_idx] and
                df['K'].iloc[last_kdj_trough_idx] > df['K'].iloc[prev_kdj_trough_idx]):
                signals["bottom_divergence"] = True
    
    return signals

def compute(df, ticker):
    # 計算技術指標
    df['RSI'] = talib.RSI(df['Close'], timeperiod=14)
    df['MA20'] = talib.SMA(df['Close'], timeperiod=20)
    df['MA120'] = talib.SMA(df['Close'], timeperiod=120)
    df['MA240'] = talib.SMA(df['Close'], timeperiod=240)
    
    # 使用自定義KDJ計算
    df = calculate_kdj(df, n=9)
    
    # 檢測信號
    signals = detect_signals(df)

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
        # 優先使用 trailingPE,如果沒有則使用 forwardPE
        pe = info.get('trailingPE') or info.get('forwardPE')
        if pe is not None:
            pe = float(pe)
    except:
        pass  # 如果獲取失敗,保持為 None
    
    return {
        "close": float(last['Close']),
        "change_percent": change_percent,
        "pe": pe,
        "rsi": float(last['RSI']) if not pd.isna(last['RSI']) else None,
        "k": float(last['K']) if not pd.isna(last['K']) else None,
        "d": float(last['D']) if not pd.isna(last['D']) else None,
        "j": float(last['J']) if not pd.isna(last['J']) else None,
        "ma20": float(last['MA20']) if not pd.isna(last['MA20']) else None,
        "ma120": float(last['MA120']) if not pd.isna(last['MA120']) else None,
        "ma240": float(last['MA240']) if not pd.isna(last['MA240']) else None,
        "golden_cross": signals["golden_cross"],
        "death_cross": signals["death_cross"],
        "top_divergence": signals["top_divergence"],
        "bottom_divergence": signals["bottom_divergence"],
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
        # 如果獲取失敗,使用空數據
        data[stock["key"]] = {
            "close": None,
            "change_percent": None,
            "pe": None,
            "rsi": None,
            "k": None,
            "d": None,
            "j": None,
            "ma20": None,
            "ma120": None,
            "ma240": None,
            "golden_cross": False,
            "death_cross": False,
            "top_divergence": False,
            "bottom_divergence": False,
        }

# 生成 data.json 供 index.html 讀取
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
