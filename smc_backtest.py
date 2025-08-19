import ccxt
import pandas as pd

# --- 1. Binance 연결 ---
# 백테스트용이므로 API 키 없이 공개 엔드포인트만 사용합니다.
exchange = ccxt.binance({
    "enableRateLimit": True
})

symbol = "BTC/USDT"
timeframe = "1h"

# --- 2. 데이터 수집 ---
def fetch_ohlcv(symbol, timeframe, since=None, limit=1000):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["time", "open", "high", "low", "close", "volume"])
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    return df

# --- 3. 스윙포인트 탐지 ---
def detect_swings(df, lookback=3):
    swings = []
    for i in range(lookback, len(df) - lookback):
        high = df["high"].iloc[i]
        low = df["low"].iloc[i]
        if high == max(df["high"].iloc[i - lookback : i + lookback + 1]):
            swings.append((df["time"].iloc[i], "H", high))
        if low == min(df["low"].iloc[i - lookback : i + lookback + 1]):
            swings.append((df["time"].iloc[i], "L", low))
    return swings

# --- 4. BOS / CHoCH ---
def detect_bos(df, swings):
    signals = []
    for t, typ, level in swings:
        after = df[df["time"] > t].iloc[:3]
        if typ == "H" and any(after["close"] > level):
            signals.append(("BOS_UP", t, level))
        if typ == "L" and any(after["close"] < level):
            signals.append(("BOS_DOWN", t, level))
    return signals

# --- 5. Order Block ---
def detect_order_blocks(df, bos_signals):
    obs = []
    for sig, t, level in bos_signals:
        idx = df.index[df["time"] == t][0]
        if sig == "BOS_UP":
            # 상승 전 마지막 음봉
            for j in range(idx - 5, idx):
                if df["close"].iloc[j] < df["open"].iloc[j]:
                    ob_low = min(df["open"].iloc[j], df["close"].iloc[j])
                    ob_high = max(df["open"].iloc[j], df["close"].iloc[j])
                    obs.append((t, ob_low, ob_high, "BullishOB"))
                    break
        if sig == "BOS_DOWN":
            # 하락 전 마지막 양봉
            for j in range(idx - 5, idx):
                if df["close"].iloc[j] > df["open"].iloc[j]:
                    ob_low = min(df["open"].iloc[j], df["close"].iloc[j])
                    ob_high = max(df["open"].iloc[j], df["close"].iloc[j])
                    obs.append((t, ob_low, ob_high, "BearishOB"))
                    break
    return obs

# --- 6. Fair Value Gap (FVG) ---
def detect_fvg(df):
    fvgs = []
    for i in range(2, len(df)):
        if df["high"].iloc[i - 2] < df["low"].iloc[i]:
            fvgs.append((df["time"].iloc[i], df["high"].iloc[i - 2], df["low"].iloc[i], "BullishFVG"))
        if df["low"].iloc[i - 2] > df["high"].iloc[i]:
            fvgs.append((df["time"].iloc[i], df["low"].iloc[i - 2], df["high"].iloc[i], "BearishFVG"))
    return fvgs

# --- 7. 엔트리 조건 (OB 되돌림) ---
def check_entry(df, obs):
    entries = []
    for t, low, high, typ in obs:
        after = df[df["time"] > t].iloc[:10]
        for _, row in after.iterrows():
            if typ == "BullishOB" and low <= row["low"] <= high:
                entries.append(("BUY", row["time"], row["close"]))
            if typ == "BearishOB" and low <= row["high"] <= high:
                entries.append(("SELL", row["time"], row["close"]))
    return entries

# --- 실행 ---
if __name__ == "__main__":
    df = fetch_ohlcv(symbol, timeframe, limit=500)
    swings = detect_swings(df)
    bos = detect_bos(df, swings)
    obs = detect_order_blocks(df, bos)
    fvgs = detect_fvg(df)
    entries = check_entry(df, obs)

    print("Swings:", swings[:10])
    print("BOS:", bos[:5])
    print("Order Blocks:", obs[:3])
    print("FVGs:", fvgs[:3])
    print("Entries:", entries[:3])
