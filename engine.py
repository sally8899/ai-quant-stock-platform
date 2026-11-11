import numpy as np
import pandas as pd

def _normalize_history(df):
    aliases = {"收盘":"close","开盘":"open","最高":"high","最低":"low","成交量":"volume",
               "日期":"date","成交额":"amount"}
    x = df.rename(columns=aliases).copy()
    if "close" not in x:
        raise ValueError("历史行情缺少收盘价字段")
    for c in ["close","open","high","low","volume"]:
        if c in x:
            x[c] = pd.to_numeric(x[c], errors="coerce")
    x = x.dropna(subset=["close"]).sort_values("date" if "date" in x else x.index.name or "close")
    x = x.reset_index(drop=True)
    return x

def score_stock(spot, history):
    h = _normalize_history(history)
    c = h["close"]
    if len(c) < 30:
        raise ValueError("历史数据不足")
    ma5, ma10, ma20, ma60 = c.rolling(5).mean(), c.rolling(10).mean(), c.rolling(20).mean(), c.rolling(60).mean()
    delta = c.diff()
    gain, loss = delta.clip(lower=0).rolling(14).mean(), -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = (100 - 100/(1+rs)).iloc[-1]
    ema12, ema26 = c.ewm(span=12).mean(), c.ewm(span=26).mean()
    macd = ema12-ema26
    signal = macd.ewm(span=9).mean()
    vol = h["volume"] if "volume" in h else pd.Series(np.ones(len(h)))
    vol_ratio = vol.iloc[-5:].mean() / max(vol.iloc[-20:].mean(), 1)
    last = float(c.iloc[-1])
    score = 0
    score += 10 if last > ma20.iloc[-1] else 0
    score += 8 if ma5.iloc[-1] > ma10.iloc[-1] else 0
    score += 7 if ma10.iloc[-1] > ma20.iloc[-1] else 0
    score += 5 if ma20.iloc[-1] > ma60.iloc[-1] else 0
    score += 8 if macd.iloc[-1] > signal.iloc[-1] else 0
    score += 5 if 50 <= (rsi if np.isfinite(rsi) else 0) <= 75 else 0
    score += 5 if vol_ratio > 1.2 else 0
    ret20 = float(c.pct_change(20).iloc[-1] * 100)
    score += 5 if ret20 > 0 else 0
    # Remaining points are intentionally conservative placeholders pending audited fundamentals/sector feeds.
    score += 5 if float(spot["amount"]) >= 1e8 else 0
    score = min(score, 58)  # No unsupported fundamental/sector points awarded.
    risk_pass = not (rsi > 85 or ret20 < -18 or last < ma20.iloc[-1]*0.90)
    if last > ma20.iloc[-1] and vol_ratio > 1.35 and macd.iloc[-1] > signal.iloc[-1]:
        strategy = "突破型"
    elif last > ma20.iloc[-1] and vol_ratio < 0.85:
        strategy = "回踩型"
    else:
        strategy = "潜伏观察型"
    buy_low = float(ma20.iloc[-1]*0.99)
    buy_high = float(ma20.iloc[-1]*1.02)
    stop = float(min(ma20.iloc[-1]*0.95, last*0.93))
    reason = f"20日线{'上方' if last>ma20.iloc[-1] else '下方'}；5日/20日均量比{vol_ratio:.2f}；RSI {rsi:.1f}；20日涨跌幅{ret20:.1f}%。"
    return {"code":spot["code"],"name":spot["name"],"price":float(spot["price"]),
            "score":score,"strategy":strategy,"risk_pass":bool(risk_pass),
            "buy_low":buy_low,"buy_high":buy_high,"stop":stop,"reason":reason,
            "rsi":float(rsi) if np.isfinite(rsi) else np.nan,"vol_ratio":float(vol_ratio)}

def build_candidates(rows):
    return pd.DataFrame(rows).sort_values("score", ascending=False)

def run_backtest(history):
    h = _normalize_history(history)
    if len(h) < 80:
        return None
    c = h["close"]
    ma20 = c.rolling(20).mean()
    ma60 = c.rolling(60).mean()
    signal = ((c > ma20) & (ma20 > ma60)).astype(int)
    # Avoid look-ahead: today's signal applies to next day's return.
    pos = signal.shift(1).fillna(0)
    daily = c.pct_change().fillna(0) * pos
    equity = (1+daily).cumprod()
    peak = equity.cummax()
    dd = (equity/peak-1).min()
    trades = int(((pos.diff()==1).sum()))
    return {"return_pct":float((equity.iloc[-1]-1)*100),
            "max_drawdown":float(dd*100),"trades":trades,
            "equity":pd.Series(equity.values)}
