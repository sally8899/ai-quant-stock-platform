import pandas as pd
import numpy as np

def get_market_spot():
    import akshare as ak
    raw = ak.stock_zh_a_spot_em()
    # Eastmoney column names are Chinese; normalize defensively.
    cols = {c: c for c in raw.columns}
    code_col = next((c for c in raw.columns if c in ["代码","证券代码"]), None)
    name_col = next((c for c in raw.columns if c in ["名称","证券简称"]), None)
    price_col = next((c for c in raw.columns if c in ["最新价","现价"]), None)
    amount_col = next((c for c in raw.columns if c in ["成交额"]), None)
    if not all([code_col, name_col, price_col, amount_col]):
        raise ValueError(f"行情字段无法识别，实际字段：{list(raw.columns)}")
    df = pd.DataFrame({
        "code": raw[code_col].astype(str).str.zfill(6),
        "name": raw[name_col].astype(str),
        "price": pd.to_numeric(raw[price_col], errors="coerce"),
        "amount": pd.to_numeric(raw[amount_col], errors="coerce"),
    })
    df = df.dropna(subset=["price","amount"])
    df = df[~df["name"].str.contains("ST|退", case=False, na=False)]
    df = df[~df["code"].str.startswith(("4","8"))]
    return df.sort_values("amount", ascending=False).reset_index(drop=True)

def get_history(code, demo=False):
    if demo:
        seed = int(str(code)[-4:])
        rng = np.random.default_rng(seed)
        n = 260
        dates = pd.bdate_range(end=pd.Timestamp.today(), periods=n)
        ret = rng.normal(0.0005, 0.018, n)
        close = 15 * np.exp(np.cumsum(ret))
        volume = rng.integers(500000, 3000000, n)
        return pd.DataFrame({"日期":dates, "收盘":close, "开盘":close*(1+rng.normal(0,.006,n)),
                             "最高":close*1.02, "最低":close*.98, "成交量":volume})
    import akshare as ak
    df = ak.stock_zh_a_hist(symbol=str(code), period="daily", start_date="20240101",
                            end_date=pd.Timestamp.today().strftime("%Y%m%d"), adjust="qfq")
    if df is None or df.empty:
        raise ValueError(f"{code}没有获取到历史行情")
    return df
def make_demo_market():
    rng = np.random.default_rng(2026)
    rows=[]
    for i in range(100):
        code = f"{600000+i:06d}"
        rows.append({"code":code, "name":f"演示股票{i+1:03d}", "price":float(rng.uniform(5,80)),
                     "amount":float(rng.uniform(8e7,8e8))})
    return pd.DataFrame(rows).sort_values("amount", ascending=False).reset_index(drop=True)
