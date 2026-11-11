import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from quant.data import get_market_spot, get_history, make_demo_market
from quant.engine import score_stock, build_candidates, run_backtest

st.set_page_config(page_title="AI智能量化选股平台", page_icon="📈", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background: rgba(120,120,120,.08); padding: 12px; border-radius: 10px;}
@media (max-width: 768px) {
  .block-container {padding-left: .8rem; padding-right: .8rem;}
  h1 {font-size: 1.65rem !important;}
  [data-testid="stMetric"] {padding: 8px;}
  [data-testid="stDataFrame"] {font-size: .78rem;}
}
.small-note {font-size: .85rem; opacity: .75;}
</style>
""", unsafe_allow_html=True)

st.title("📈 AI智能量化选股平台")
st.caption("AI QUANT PRO · A股多因子筛选 / 策略评分 / 风险管理 / 历史回测")

with st.sidebar:
    st.header("系统设置")
    source = st.radio("行情数据模式", ["公开行情接口（AKShare）", "演示数据（不代表真实行情）"], index=0)
    st.divider()
    st.subheader("初筛条件")
    min_price = st.number_input("最低股价（元）", 0.0, 500.0, 3.0, 0.5)
    max_price = st.number_input("最高股价（元）", 0.1, 1000.0, 150.0, 1.0)
    min_turnover = st.number_input("最低成交额（万元）", 0, 1000000, 5000, 1000)
    min_score = st.slider("最低综合评分", 0, 100, 70)
    scan_limit = st.slider("扫描股票数量上限", 20, 200, 80, 20)
    st.caption("免费公开数据可能延迟、限流或暂时不可用。")

if "market" not in st.session_state:
    st.session_state.market = None
if "source_label" not in st.session_state:
    st.session_state.source_label = ""

col1, col2 = st.columns([1, 3])
with col1:
    run_scan = st.button("🔎 开始扫描A股", type="primary", use_container_width=True)
with col2:
    st.markdown("<div class='small-note'>扫描流程：基础过滤 → 技术指标 → 三类策略识别 → 量化评分 → 风险审核。首次扫描可能需要一些时间。</div>", unsafe_allow_html=True)

if run_scan:
    with st.spinner("正在获取行情并计算量化信号……"):
        try:
            if source.startswith("演示"):
                market = make_demo_market()
                label = "演示数据（非真实行情）"
            else:
                market = get_market_spot()
                label = "AKShare公开行情"
            st.session_state.market = market
            st.session_state.source_label = label
            st.session_state.scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            st.error(f"行情获取失败：{e}")
            st.info("可以切换到演示数据检查界面和策略流程；演示结果不可用于真实交易。")

market = st.session_state.market
if market is None:
    st.info("请点击“开始扫描A股”。建议首次先用演示数据熟悉界面，再切换公开行情接口。")
    st.markdown("### 平台模块")
    a,b,c,d = st.columns(4)
    a.metric("策略引擎", "3类")
    b.metric("评分体系", "100分")
    c.metric("风险控制", "独立审核")
    d.metric("交易模式", "模拟")
    st.stop()

st.caption(f"数据来源：{st.session_state.source_label}　|　扫描时间：{st.session_state.get('scan_time','—')}　|　请核对行情时间戳")
filtered = market.copy()
filtered = filtered[(filtered["price"] >= min_price) & (filtered["price"] <= max_price) & (filtered["amount"] >= min_turnover * 10000)]
filtered = filtered.head(scan_limit)

progress = st.progress(0, text="正在分析候选股票")
records = []
for i, row in enumerate(filtered.to_dict("records")):
    try:
        hist = get_history(row["code"], demo=(st.session_state.source_label.startswith("演示")))
        item = score_stock(row, hist)
        records.append(item)
    except Exception:
        continue
    progress.progress((i+1)/max(len(filtered),1), text=f"已分析 {i+1}/{len(filtered)}")
progress.empty()

if not records:
    st.warning("没有得到可用分析结果。可能是行情接口限流、网络异常或筛选条件过严。请稍后重试或切换演示数据。")
    st.stop()

results = pd.DataFrame(records)
results = results.sort_values("score", ascending=False).reset_index(drop=True)
results["通过风险审核"] = results["risk_pass"].map({True:"通过", False:"否决"})
results["评分"] = results["score"].round(1)
results["最新价"] = results["price"].round(2)
results["建议观察区间"] = results.apply(lambda x: f'{x["buy_low"]:.2f}–{x["buy_high"]:.2f}', axis=1)
results["止损参考"] = results["stop"].round(2)
results["策略类型"] = results["strategy"]
results["代码"] = results["code"]
results["名称"] = results["name"]

eligible = results[(results["score"] >= min_score) & (results["risk_pass"])]
top = eligible.head(5)

m1,m2,m3,m4 = st.columns(4)
m1.metric("分析股票数", len(results))
m2.metric("通过风险审核", int(results["risk_pass"].sum()))
m3.metric("核心候选股", len(top))
m4.metric("最高评分", f'{results["score"].max():.1f}分')

st.subheader("⭐ 核心候选股票")
if top.empty:
    st.warning("当前没有符合评分及风险门槛的核心候选股。空仓等待也是有效策略。")
else:
    show_cols = ["代码","名称","最新价","评分","策略类型","建议观察区间","止损参考","通过风险审核"]
    st.dataframe(top[show_cols], use_container_width=True, hide_index=True)

st.subheader("📋 全部扫描结果")
all_cols = ["代码","名称","最新价","评分","策略类型","建议观察区间","止损参考","通过风险审核","reason"]
st.dataframe(results[all_cols].rename(columns={"reason":"入选依据"}), use_container_width=True, hide_index=True)
st.download_button("下载选股结果 CSV", results[all_cols].to_csv(index=False, encoding="utf-8-sig"), "ai_quant_candidates.csv", "text/csv")

st.subheader("🔬 个股深度分析")
choices = results["code"].tolist()
selected = st.selectbox("选择股票代码", choices, format_func=lambda x: f'{x} · {results.loc[results.code==x,"name"].iloc[0]}')
r = results[results.code == selected].iloc[0]
x1,x2,x3,x4 = st.columns(4)
x1.metric("综合评分", f'{r["score"]:.1f}/100')
x2.metric("最新价", f'{r["price"]:.2f}元')
x3.metric("策略", r["strategy"])
x4.metric("风险审核", "通过" if r["risk_pass"] else "否决")
st.write(f"**AI量化解释：** {r['reason']}")
st.write(f"**支撑/观察：** 买入观察区间 {r['buy_low']:.2f}–{r['buy_high']:.2f} 元；止损参考 {r['stop']:.2f} 元。")
st.warning("以上价格为算法观察值，不是交易指令。实际成交可能受跳空、涨跌停、滑点及数据延迟影响。")

st.subheader("🧪 简易历史回测")
st.caption("使用所选股票的历史日线，演示均线趋势策略；结果不代表未来收益，未计入所有实盘摩擦因素。")
if st.button("运行所选股票回测"):
    with st.spinner("正在运行回测……"):
        hist = get_history(selected, demo=st.session_state.source_label.startswith("演示"))
        bt = run_backtest(hist)
    if bt:
        q1,q2,q3 = st.columns(3)
        q1.metric("策略累计收益", f'{bt["return_pct"]:.2f}%')
        q2.metric("最大回撤", f'{bt["max_drawdown"]:.2f}%')
        q3.metric("交易次数", bt["trades"])
        st.line_chart(bt["equity"])
        st.caption("回测采用收盘信号、下一交易日持仓的简化假设；真实使用前需进一步完善成交、复权、费用及涨跌停处理。")
    else:
        st.warning("历史数据不足，无法回测。")

st.divider()
st.caption("风险提示：本工具用于研究和模拟，不构成投资建议。第一版不自动下单，不保证收益。")
