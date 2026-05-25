import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
from datetime import datetime

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ModuleNotFoundError:
    yf = None
    YFINANCE_AVAILABLE = False

try:
    import firebase_admin
    from firebase_admin import credentials, firestore as _fs
    FIREBASE_AVAILABLE = True
except ModuleNotFoundError:
    FIREBASE_AVAILABLE = False

# 웹 페이지 기본 설정
st.set_page_config(
    page_title="미국주식 수익률 시뮬레이터",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .stApp {
        background: linear-gradient(165deg, #eef4ff 0%, #f8fafc 45%, #ffffff 100%);
        color: #0f172a;
    }
    header[data-testid="stHeader"] { background: rgba(255,255,255,0.85); backdrop-filter: blur(8px); }
    .main .block-container { padding-top: 1.25rem; padding-bottom: 2.5rem; max-width: 1180px; }
    .main label, .main p, .main span, .main .stMarkdown, .main [data-testid="stCaptionContainer"] {
        color: #0f172a;
    }
    .main [data-testid="stAlert"] {
        border: 1px solid #3b82f6 !important;
        color: #0f172a !important;
    }
    /* ── Streamlit-version-sensitive selectors (tested on Streamlit ≥1.36) ──
       data-testid values can change across major releases.
       Upgrade breakage usually starts here — check these selectors first.  */
    section[data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, #0f2744 0%, #163a5f 100%);
    }
    section[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary {
        background: rgba(255,255,255,0.12);
        border-radius: 12px;
        color: #f8fafc !important;
        font-weight: 600;
        border: 1px solid #94a3b8;
    }
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary * {
        color: #f8fafc !important;
    }
    section[data-testid="stSidebar"] [data-testid="stExpanderDetails"] {
        background: #f1f5f9 !important;
        border: 1px solid #64748b !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px;
        padding: 0.6rem 0.5rem 0.8rem;
    }
    section[data-testid="stSidebar"] [data-testid="stExpanderDetails"] label,
    section[data-testid="stSidebar"] [data-testid="stExpanderDetails"] p,
    section[data-testid="stSidebar"] [data-testid="stExpanderDetails"] span,
    section[data-testid="stSidebar"] [data-testid="stExpanderDetails"] small,
    section[data-testid="stSidebar"] [data-testid="stExpanderDetails"] .stMarkdown,
    section[data-testid="stSidebar"] [data-testid="stExpanderDetails"] [data-testid="stCaptionContainer"] {
        color: #0f172a !important;
    }
    section[data-testid="stSidebar"] [data-testid="stForm"] {
        background: #ffffff !important;
        border-radius: 14px;
        padding: 0.5rem 0.75rem 1rem;
        border: 1px solid #64748b !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
    }
    section[data-testid="stSidebar"] [data-testid="stForm"] label,
    section[data-testid="stSidebar"] [data-testid="stForm"] p,
    section[data-testid="stSidebar"] [data-testid="stForm"] span {
        color: #0f172a !important;
    }
    .hero {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 55%, #3b82f6 100%);
        border-radius: 20px; padding: 28px 32px; margin-bottom: 1.25rem;
        box-shadow: 0 20px 50px rgba(30, 58, 138, 0.25); color: #fff;
        border: 1px solid #1e40af;
    }
    .hero-badge {
        display: inline-block; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.06em;
        text-transform: uppercase; background: rgba(255,255,255,0.22); padding: 6px 12px;
        border-radius: 999px; margin-bottom: 10px; color: #fff;
    }
    .hero h1 { margin: 0 0 8px 0; font-size: 1.75rem; font-weight: 800; line-height: 1.25; color: #fff !important; }
    .hero p { margin: 0; font-size: 1rem; color: #e0eaff !important; }
    .section-card {
        background: #fff;
        border: 1px solid #64748b;
        border-radius: 18px;
        padding: 20px 22px;
        margin-bottom: 1rem;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    }
    .section-card h3 { margin: 0 0 6px 0; font-size: 1.1rem; color: #0f172a !important; }
    .section-card p { margin: 0; color: #475569 !important; font-size: 0.92rem; }
    .empty-state {
        text-align: center; padding: 48px 24px; background: #fff; border-radius: 18px;
        border: 2px dashed #64748b; color: #334155;
    }
    .empty-state h3 { color: #0f172a !important; margin-bottom: 8px; }
    div[data-testid="stMetric"] {
        background: #fff;
        border: 1px solid #64748b !important;
        border-radius: 16px;
        padding: 14px 18px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
    }
    div[data-testid="stMetric"] label { color: #475569 !important; font-weight: 600 !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #0f172a !important; font-weight: 800 !important; }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] { color: #1d4ed8 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background: transparent; border-bottom: 2px solid #94a3b8; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0; font-weight: 600; padding: 10px 20px;
        background: #e2e8f0; color: #1e293b !important;
        border: 1px solid #94a3b8;
    }
    .stTabs [aria-selected="true"] {
        background: #2563eb !important;
        color: #fff !important;
        border-color: #1d4ed8 !important;
    }
    .stButton > button {
        border-radius: 12px; font-weight: 600;
        border: 1px solid #64748b !important;
        color: #0f172a !important;
        background: #fff !important;
    }
    .stButton > button[kind="primary"], .stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        color: #fff !important;
        border: 1px solid #1e40af !important;
    }
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        color: #fff !important;
        border: 1px solid #1e40af !important;
        font-weight: 700 !important;
    }
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        border-radius: 10px;
        border: 1px solid #64748b !important;
        background: #fff !important;
        color: #0f172a !important;
    }
    [data-testid="stDataFrame"] {
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid #64748b !important;
    }
    div[data-testid="stToolbarActionButton"], .stFormSubmitHint { display: none !important; }
</style>
"""
st.markdown(APP_CSS, unsafe_allow_html=True)
st.markdown(
    """
    <div class="hero">
        <div class="hero-badge">USD · Real-time</div>
        <h1>🇺🇸 미국주식 투자 관리 &amp; 매도 수익률 시뮬레이터</h1>
        <p>매수·매도(분할 매도) 기록 · 실시간 평가 · 매도 시뮬레이션을 한 화면에서 관리하세요.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

components.html(
    """
    <script>
        (function () {
            const root = window.parent.document;
            const INITIAL_DELAY_MS = 350;
            const REPEAT_MS = 70;

            function isNumberStepperButton(btn) {
                const testId = btn.getAttribute("data-testid") || "";
                if (testId === "stNumberInputStepUp" || testId === "stNumberInputStepDown") {
                    return true;
                }
                if (!btn.closest('[data-testid="stNumberInput"]')) {
                    return false;
                }
                const text = (btn.textContent || "").trim();
                if (text === "+" || text === "-" || text === "▲" || text === "▼") {
                    return true;
                }
                const label = (btn.getAttribute("aria-label") || "").toLowerCase();
                return /increase|decrease|increment|decrement|step up|step down|늘리|줄이/.test(label);
            }

            function attachHoldRepeat(button) {
                if (button.dataset.holdRepeatBound === "1") {
                    return;
                }
                button.dataset.holdRepeatBound = "1";

                let delayTimer = null;
                let repeatTimer = null;

                const clearTimers = () => {
                    if (delayTimer) {
                        clearTimeout(delayTimer);
                        delayTimer = null;
                    }
                    if (repeatTimer) {
                        clearInterval(repeatTimer);
                        repeatTimer = null;
                    }
                };

                const stepOnce = () => button.click();

                const startHold = (event) => {
                    if (event.type === "pointerdown" && event.button !== 0) {
                        return;
                    }
                    clearTimers();
                    event.preventDefault();
                    stepOnce();
                    delayTimer = setTimeout(() => {
                        repeatTimer = setInterval(stepOnce, REPEAT_MS);
                    }, INITIAL_DELAY_MS);
                };

                button.addEventListener("pointerdown", startHold);
                ["pointerup", "pointerleave", "pointercancel"].forEach((name) => {
                    button.addEventListener(name, clearTimers);
                });
                root.addEventListener("pointerup", clearTimers);
            }

            function bindAllSteppers() {
                root.querySelectorAll("button").forEach((btn) => {
                    if (isNumberStepperButton(btn)) {
                        attachHoldRepeat(btn);
                    }
                });
            }

            bindAllSteppers();
            setTimeout(bindAllSteppers, 400);
            setInterval(bindAllSteppers, 900);

            const observer = new MutationObserver(() => bindAllSteppers());
            observer.observe(root.body, { childList: true, subtree: true });
        })();
    </script>
    """,
    height=0,
)

# 데이터 저장을 위한 CSV 파일 경로
DATA_FILE = "stocks_usd.csv"
HISTORY_FILE = "history_usd.csv"
DEFAULT_COLUMNS = ["종목명", "매수평단가(USD)", "보유수량", "목표매도가(USD)"]
HISTORY_COLUMNS = [
    "종목명", "매수평단가(USD)", "매도수량", "매도비율(%)",
    "매도가(USD)", "매도손익($)", "매도수익률(%)", "매도일시",
]

@st.cache_data(ttl=10)
def get_usd_krw_rate():
    if not YFINANCE_AVAILABLE:
        return None
    try:
        ticker = yf.Ticker("KRW=X")
        price = None
        if hasattr(ticker, "fast_info"):
            try:
                price = ticker.fast_info.get("last_price")
            except Exception:
                price = None
        if price is None:
            price = ticker.info.get("regularMarketPrice")
        if price is None:
            history = ticker.history(period="1d", interval="1m")
            if not history.empty:
                price = float(history["Close"].iloc[-1])
        return float(price) if price is not None else None
    except Exception:
        return None


_initial_fx = get_usd_krw_rate()
_initial_fx_js = "null" if _initial_fx is None else f"{_initial_fx:.4f}"

# 시간·환율: 클라이언트에서 매초/주기 갱신 (페이지 새로고침 없음)
components.html(
    f"""
    <div style="display:flex; gap: 14px; margin-bottom: 4px; font-family: 'Noto Sans KR', sans-serif;">
        <div style="flex:1; padding:20px 22px; border-radius:16px; background:#fff; border:1px solid #dbeafe; box-shadow:0 8px 24px rgba(37,99,235,0.08);">
            <div style="font-size:0.8rem; font-weight:700; color:#2563eb; letter-spacing:0.04em; margin-bottom:6px;">🇺🇸 미국 (ET)</div>
            <div id="us_time" style="font-size:1.4rem; font-weight:800; color:#0f172a; line-height:1.2;"></div>
            <div id="market_status" style="margin-top:14px; font-size:0.9rem; font-weight:700; padding:8px 14px; border-radius:999px; display:inline-block;"></div>
        </div>
        <div style="flex:1; padding:20px 22px; border-radius:16px; background:#fff; border:1px solid #fde68a; box-shadow:0 8px 24px rgba(217,119,6,0.08);">
            <div style="font-size:0.8rem; font-weight:700; color:#d97706; letter-spacing:0.04em; margin-bottom:6px;">🇰🇷 한국 (KST)</div>
            <div id="kr_time" style="font-size:1.4rem; font-weight:800; color:#0f172a; line-height:1.2;"></div>
        </div>
        <div style="flex:1; padding:20px 22px; border-radius:16px; background:#fff; border:1px solid #bbf7d0; box-shadow:0 8px 24px rgba(22,163,74,0.08);">
            <div style="font-size:0.8rem; font-weight:700; color:#16a34a; letter-spacing:0.04em; margin-bottom:6px;">💱 USD → KRW</div>
            <div id="fx_rate" style="font-size:1.4rem; font-weight:800; color:#0f172a; line-height:1.2;">조회 중...</div>
            <div id="fx_updated" style="margin-top:14px; font-size:0.85rem; font-weight:600; color:#64748b;"></div>
        </div>
    </div>
    <script>
        let fxRate = {_initial_fx_js};
        let fxUpdatedAt = fxRate ? new Date() : null;

        function formatFx(rate) {{
            return '1 USD = ' + rate.toLocaleString('ko-KR', {{ maximumFractionDigits: 2 }}) + ' 원';
        }}

        function renderFx() {{
            const rateEl = document.getElementById('fx_rate');
            const updatedEl = document.getElementById('fx_updated');
            if (fxRate) {{
                rateEl.textContent = formatFx(fxRate);
                if (fxUpdatedAt) {{
                    const tick = fxUpdatedAt.toLocaleTimeString('ko-KR', {{ hour: '2-digit', minute: '2-digit', second: '2-digit' }});
                    updatedEl.textContent = '갱신 ' + tick;
                }}
            }} else {{
                rateEl.textContent = '환율 조회 중...';
                updatedEl.textContent = '';
            }}
        }}

        async function fetchExchangeRate() {{
            const providers = [
                async () => {{
                    const res = await fetch('https://open.er-api.com/v6/latest/USD');
                    const data = await res.json();
                    if (data && data.result === 'success' && data.rates && data.rates.KRW) {{
                        return data.rates.KRW;
                    }}
                    return null;
                }},
                async () => {{
                    const res = await fetch('https://api.frankfurter.app/latest?from=USD&to=KRW');
                    const data = await res.json();
                    if (data && data.rates && data.rates.KRW) {{
                        return data.rates.KRW;
                    }}
                    return null;
                }},
            ];
            for (const provider of providers) {{
                try {{
                    const rate = await provider();
                    if (rate) {{
                        fxRate = rate;
                        fxUpdatedAt = new Date();
                        renderFx();
                        return;
                    }}
                }} catch (err) {{
                    /* 다음 API 시도 */
                }}
            }}
            renderFx();
        }}

        function updateMarkets() {{
            const now = new Date();
            const krString = now.toLocaleString('ko-KR', {{ timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }});
            const usString = now.toLocaleString('en-US', {{ timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }});
            document.getElementById('kr_time').textContent = krString + ' KST';
            document.getElementById('us_time').textContent = usString + ' ET';

            const usDate = new Date(now.toLocaleString('en-US', {{ timeZone: 'America/New_York' }}));
            const statusEl = document.getElementById('market_status');
            if (!isNaN(usDate)) {{
                const day = usDate.getDay();
                const hour = usDate.getHours();
                const minute = usDate.getMinutes();
                let status = '';
                let style = '';
                if (day === 0 || day === 6) {{
                    status = '주말 휴장';
                    style = 'background: #f9d6d5; color: #9a0000;';
                }} else if (hour < 4) {{
                    status = '장 마감';
                    style = 'background: #f0f4ff; color: #2b3c8f;';
                }} else if (hour < 9 || (hour === 9 && minute < 30)) {{
                    status = '프리마켓';
                    style = 'background: #fff4cc; color: #a06100;';
                }} else if (hour < 16 || (hour === 16 && minute === 0)) {{
                    status = '정규장';
                    style = 'background: #d6f5d6; color: #1b5e20;';
                }} else if (hour < 20) {{
                    status = '애프터마켓';
                    style = 'background: #e8f4ff; color: #1f4e8f;';
                }} else {{
                    status = '장 마감';
                    style = 'background: #f0f4ff; color: #2b3c8f;';
                }}
                statusEl.textContent = '현재 상태: ' + status;
                statusEl.style = style + ' margin-top: 12px; font-size: 1rem; font-weight: 700; padding: 10px 12px; border-radius: 10px; display: inline-block;';
            }} else {{
                statusEl.textContent = '현재 상태: 계산 불가';
                statusEl.style = 'background: #f5f5f5; color: #333; margin-top: 12px; font-size: 1rem; font-weight: 700; padding: 10px 12px; border-radius: 10px; display: inline-block;';
            }}
            renderFx();
        }}

        renderFx();
        updateMarkets();
        fetchExchangeRate();
        setInterval(updateMarkets, 1000);
        setInterval(fetchExchangeRate, 15000);
    </script>
    """,
    height=175,
)

@st.cache_data(ttl=30)
def get_live_price(ticker_symbol: str):
    if not ticker_symbol:
        return None

    # 1순위: Yahoo Finance REST API 직접 호출 (클라우드 환경에서 안정적)
    try:
        import requests
        for base in ("https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com"):
            try:
                resp = requests.get(
                    f"{base}/v8/finance/chart/{ticker_symbol}",
                    headers={"User-Agent": "Mozilla/5.0"},
                    params={"interval": "1m", "range": "1d"},
                    timeout=8,
                )
                price = resp.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]
                return float(price)
            except Exception:
                continue
    except Exception:
        pass

    # 2순위: yfinance 폴백
    if not YFINANCE_AVAILABLE:
        return None
    try:
        ticker = yf.Ticker(ticker_symbol)
        price = None
        if hasattr(ticker, "fast_info"):
            try:
                price = ticker.fast_info.get("last_price")
            except Exception:
                price = None
        if price is None:
            price = ticker.info.get("regularMarketPrice")
        if price is None:
            history = ticker.history(period="1d", interval="1m")
            if not history.empty:
                price = float(history["Close"].iloc[-1])
        return float(price) if price is not None else None
    except Exception:
        return None


def profit_loss_color(val):
    if isinstance(val, pd.Series):
        return [profit_loss_color(x) for x in val]
    if pd.isna(val):
        return ""
    if val > 0:
        return "color: red; font-weight: bold;"
    if val < 0:
        return "color: blue; font-weight: bold;"
    return ""


def target_price_color(val):
    if isinstance(val, pd.Series):
        return [target_price_color(x) for x in val]
    if pd.isna(val) or val == 0:
        return ""
    return "color: #0b6623; background-color: #e8f7e8; font-weight: bold;"


def condition_color(val):
    if isinstance(val, pd.Series):
        return [condition_color(x) for x in val]
    if val == "목표 도달":
        return "background-color: #d4f8d4; color: #065f00; font-weight: bold;"
    return ""


def calc_sell_quantity(hold_qty: int, sell_pct: float) -> int:
    hold_qty = int(hold_qty)
    if hold_qty <= 0:
        return 0
    if sell_pct >= 100:
        return hold_qty
    sell_qty = int(round(hold_qty * sell_pct / 100))
    return max(1, min(sell_qty, hold_qty))


def record_partial_sell(row: pd.Series, sell_price: float, sell_pct: float) -> tuple[int, int]:
    """매도 기록 후 (매도수량, 잔여수량) 반환."""
    hold_qty = int(row["보유수량"])
    sell_qty = calc_sell_quantity(hold_qty, sell_pct)
    buy_cost = row["매수평단가(USD)"] * sell_qty
    sell_total = sell_price * sell_qty
    profit = sell_total - buy_cost
    roi = (profit / buy_cost) * 100 if buy_cost else 0
    actual_pct = (sell_qty / hold_qty) * 100 if hold_qty else 0

    history_row = pd.DataFrame([{
        "종목명": row["종목명"],
        "매수평단가(USD)": row["매수평단가(USD)"],
        "매도수량": sell_qty,
        "매도비율(%)": actual_pct,
        "매도가(USD)": sell_price,
        "매도손익($)": profit,
        "매도수익률(%)": roi,
        "매도일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }])
    st.session_state.history = pd.concat([st.session_state.history, history_row], ignore_index=True)

    remaining = hold_qty - sell_qty
    idx = row.name
    if remaining <= 0:
        st.session_state.df = st.session_state.df.drop(index=idx).reset_index(drop=True)
    else:
        st.session_state.df.at[idx, "보유수량"] = remaining

    save_history(st.session_state.history)
    save_data(st.session_state.df)
    return sell_qty, remaining


def init_session_state():
    """fragment 단독 rerun 시에도 세션 데이터가 준비되도록 보장."""
    if "df" not in st.session_state:
        st.session_state.df = load_data()
    if "history" not in st.session_state:
        st.session_state.history = load_history()
    if "auto_quote_refresh" not in st.session_state:
        st.session_state.auto_quote_refresh = False
    if "quote_refresh_interval" not in st.session_state:
        st.session_state.quote_refresh_interval = 5


def build_portfolio_df():
    init_session_state()
    df = st.session_state.df.copy()
    df["총 매수금액($)"] = df["매수평단가(USD)"] * df["보유수량"]
    df["현재가(USD)"] = df["종목명"].apply(get_live_price)
    df["평가금액($)"] = df["현재가(USD)"] * df["보유수량"]
    df["평가손익($)"] = df["평가금액($)"] - df["총 매수금액($)"]
    df["수익률(%)"] = (df["평가손익($)"] / df["총 매수금액($)"]) * 100
    df["조건"] = df.apply(
        lambda row: "목표 도달"
        if pd.notna(row["현재가(USD)"])
        and pd.notna(row["목표매도가(USD)"])
        and row["목표매도가(USD)"] > 0
        and row["현재가(USD)"] >= row["목표매도가(USD)"]
        else "",
        axis=1,
    )
    st.session_state.quotes_updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return df


def style_portfolio_df(df_display):
    styled = df_display.style.format(
        {
            "매수평단가(USD)": "${:,.2f}",
            "목표매도가(USD)": "${:,.2f}",
            "현재가(USD)": "${:,.2f}",
            "보유수량": "{:,} 주",
            "총 매수금액($)": "${:,.2f}",
            "평가금액($)": "${:,.2f}",
            "평가손익($)": "${:,.2f}",
            "수익률(%)": "{:+.2f}%",
            "미실현 손익($)": "${:,.2f}",
            "미실현 수익률(%)": "{:+.2f}%",
        },
        na_rep="N/A",
    )
    pl_cols = [c for c in ["미실현 손익($)", "미실현 수익률(%)", "평가손익($)", "수익률(%)"] if c in df_display.columns]
    styled = styled.apply(profit_loss_color, subset=pl_cols)
    styled = styled.apply(target_price_color, subset=["목표매도가(USD)"])
    styled = styled.apply(condition_color, subset=["조건"])
    return styled


def portfolio_display_df(df_display: pd.DataFrame) -> pd.DataFrame:
    return df_display.rename(columns={
        "평가손익($)": "미실현 손익($)",
        "수익률(%)": "미실현 수익률(%)",
    })


@st.dialog("포트폴리오 전체 초기화")
def _confirm_reset():
    st.warning("⚠️ 보유 종목 전체가 삭제됩니다. 매도 내역은 유지됩니다.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("삭제", type="primary", use_container_width=True):
            st.session_state.df = pd.DataFrame(columns=DEFAULT_COLUMNS)
            save_data(st.session_state.df)
            st.rerun()
    with c2:
        if st.button("취소", use_container_width=True):
            st.rerun()


@st.dialog("매도 기록 삭제")
def _confirm_del_history():
    idx = st.session_state.get("_del_hist_idx")
    row = st.session_state.history.loc[idx]
    st.warning(f"**{row['종목명']}** {row['매도일시']} 기록을 삭제합니다.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("삭제", type="primary", use_container_width=True):
            st.session_state.history = st.session_state.history.drop(index=idx).reset_index(drop=True)
            save_history(st.session_state.history)
            st.rerun()
    with c2:
        if st.button("취소", use_container_width=True):
            st.rerun()


@st.dialog("전체 매도 내역 삭제")
def _confirm_clear_history():
    st.warning(f"매도 내역 {len(st.session_state.history):,}건이 모두 삭제됩니다.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("전체 삭제", type="primary", use_container_width=True):
            st.session_state.history = pd.DataFrame(columns=HISTORY_COLUMNS)
            save_history(st.session_state.history)
            st.rerun()
    with c2:
        if st.button("취소", use_container_width=True):
            st.rerun()


def render_portfolio_tab(df_display, live_mode: bool):
    st.markdown(
        """
        <div class="section-card">
            <h3>보유 현황 (미실현)</h3>
            <p>아직 팔지 않은 주식만, <strong>현재가</strong> 기준으로 계산합니다. 파일에 저장되지 않으며 시세가 바뀌면 함께 변합니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    updated_at = st.session_state.get("quotes_updated_at", "")
    if live_mode:
        st.caption(f"🟢 자동 갱신 ON · {st.session_state.quote_refresh_interval}초마다 · 마지막 시세 {updated_at}")
    elif updated_at:
        st.caption(f"⏸ 자동 갱신 OFF · 마지막 시세 {updated_at}")

    st.caption("💡 **실현 손익**은 「매도 기록」 후 **매도 내역** 탭에만 저장됩니다.")

    total_current = df_display["평가금액($)"].sum()
    total_cost = df_display["총 매수금액($)"].sum()
    total_profit = df_display["평가손익($)"].sum()
    avg_roi = df_display["수익률(%)"].mean()
    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    col_a.metric("총 평가금액", f"${total_current:,.2f}", help="현재가 × 보유수량 합계")
    col_b.metric("총 매수금액", f"${total_cost:,.2f}", help="매수 평단가 × 보유수량 합계")
    col_c.metric("미실현 손익", f"${total_profit:+,.2f}", help="아직 매도하지 않은 평가 손익")
    col_d.metric("평균 미실현 수익률", f"{avg_roi:+.2f}%", help="종목별 미실현 수익률 평균")
    col_e.metric("보유 종목 수", f"{len(df_display):,}개")

    if not st.session_state.history.empty:
        realized_profit = st.session_state.history["매도손익($)"].sum()
        st.caption(f"📁 참고: 누적 **실현 손익** ${realized_profit:+,.2f} (매도 내역 탭에서 상세 확인)")

    st.markdown("##### 보유 종목 상세")
    st.dataframe(
        style_portfolio_df(portfolio_display_df(df_display)),
        use_container_width=True,
        hide_index=True,
    )

    reset_col, _ = st.columns([1, 3])
    with reset_col:
        if st.button("🔄 전체 포트폴리오 초기화", use_container_width=True):
            _confirm_reset()


def render_simulator_tab(df_display, live_mode: bool):
    st.markdown(
        """
        <div class="section-card">
            <h3>목표 매도 시뮬레이터</h3>
            <p>예상 매도가를 조정하며 수익률과 손익을 미리 계산합니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected_ticker = st.selectbox("시뮬레이션 종목", df_display["종목명"].unique())
    stock_info = df_display[df_display["종목명"] == selected_ticker].iloc[0]
    qty = int(stock_info["보유수량"])
    current_px = stock_info["현재가(USD)"]
    if live_mode and pd.notna(current_px):
        st.caption(f"📡 {selected_ticker} 현재가 ${current_px:,.2f} · {datetime.now().strftime('%H:%M:%S')}")

    default_sell_price = (
        float(stock_info["목표매도가(USD)"])
        if pd.notna(stock_info["목표매도가(USD)"]) and stock_info["목표매도가(USD)"] > 0
        else (float(current_px) if pd.notna(current_px) else float(stock_info["매수평단가(USD)"]))
    )

    sell_pct = st.slider("매도 비율 (%)", min_value=1, max_value=100, value=100, key="sim_sell_pct")
    sim_qty = calc_sell_quantity(qty, sell_pct)
    sim_buy_cost = stock_info["매수평단가(USD)"] * sim_qty

    sim_left, sim_right = st.columns(2)
    with sim_left:
        st.markdown("##### ⚙️ 매도 가격 입력")
        sell_price = st.number_input(
            "예상 매도 가격 ($)",
            min_value=0.01,
            value=default_sell_price,
            step=0.01,
            format="%.2f",
        )
        st.caption(
            f"매도 예정 {sim_qty:,}주 ({sim_qty / qty * 100:.1f}%) · "
            f"잔여 {qty - sim_qty:,}주 · 매수원가 ${sim_buy_cost:,.2f}"
        )
    with sim_right:
        total_sell_usd = sell_price * sim_qty
        profit_usd = total_sell_usd - sim_buy_cost
        roi_usd = (profit_usd / sim_buy_cost) * 100 if sim_buy_cost else 0
        st.markdown("##### 💵 예상 결과")
        st.metric(
            label=f"{selected_ticker} 예상 수익률",
            value=f"{roi_usd:+.2f}%",
            delta=f"${profit_usd:+,.2f}",
        )
        st.caption(f"총 매도 예상액 ${total_sell_usd:,.2f}")

    if roi_usd > 0:
        st.success(f"🎉 ${sell_price:,.2f}에 매도 시 순이익 **${profit_usd:,.2f}** 예상")
    elif roi_usd < 0:
        st.error(f"📉 예상 손실 **${abs(profit_usd):,.2f}**")


def _get_firestore():
    """Firestore 클라이언트 반환. secrets 미설정 시 None."""
    if not FIREBASE_AVAILABLE:
        return None
    try:
        if not firebase_admin._apps:
            key_dict = dict(st.secrets.get("firebase", {}))
            if not key_dict:
                return None
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)
        return _fs.client()
    except Exception:
        return None


_PORTFOLIO_DOC = ("portfolio", "main")


def load_data():
    db = _get_firestore()
    if db is not None:
        try:
            doc = db.collection(_PORTFOLIO_DOC[0]).document(_PORTFOLIO_DOC[1]).get()
            if doc.exists:
                rows = doc.to_dict().get("stocks", [])
                df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=DEFAULT_COLUMNS)
                for col in DEFAULT_COLUMNS:
                    if col not in df.columns:
                        df[col] = None
                return df[DEFAULT_COLUMNS]
            return pd.DataFrame(columns=DEFAULT_COLUMNS)
        except Exception:
            pass
    # 로컬 CSV 폴백
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        for col in DEFAULT_COLUMNS:
            if col not in df.columns:
                df[col] = None
        return df[DEFAULT_COLUMNS]
    return pd.DataFrame(columns=DEFAULT_COLUMNS)


def save_data(df):
    db = _get_firestore()
    if db is not None:
        try:
            db.collection(_PORTFOLIO_DOC[0]).document(_PORTFOLIO_DOC[1]).set(
                {"stocks": df.to_dict("records")}, merge=True
            )
            return
        except Exception:
            pass
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")


def load_history():
    db = _get_firestore()
    if db is not None:
        try:
            doc = db.collection(_PORTFOLIO_DOC[0]).document(_PORTFOLIO_DOC[1]).get()
            if doc.exists:
                rows = doc.to_dict().get("history", [])
                df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=HISTORY_COLUMNS)
                if "매도수량" not in df.columns and "보유수량" in df.columns:
                    df["매도수량"] = df["보유수량"]
                if "매도비율(%)" not in df.columns:
                    df["매도비율(%)"] = 100.0
                for col in HISTORY_COLUMNS:
                    if col not in df.columns:
                        df[col] = None
                return df[HISTORY_COLUMNS]
            return pd.DataFrame(columns=HISTORY_COLUMNS)
        except Exception:
            pass
    # 로컬 CSV 폴백
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        if "매도수량" not in df.columns and "보유수량" in df.columns:
            df["매도수량"] = df["보유수량"]
        if "매도비율(%)" not in df.columns:
            df["매도비율(%)"] = 100.0
        for col in HISTORY_COLUMNS:
            if col not in df.columns:
                df[col] = None
        return df[HISTORY_COLUMNS]
    return pd.DataFrame(columns=HISTORY_COLUMNS)


def save_history(df):
    db = _get_firestore()
    if db is not None:
        try:
            db.collection(_PORTFOLIO_DOC[0]).document(_PORTFOLIO_DOC[1]).set(
                {"history": df.to_dict("records")}, merge=True
            )
            return
        except Exception:
            pass
    df.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")

init_session_state()

if not YFINANCE_AVAILABLE:
    st.warning(
        "yfinance가 설치되어 있지 않습니다. 아래 명령어로 yfinance를 설치하거나, 이 앱을 venv 환경에서 실행하세요.\n"
        r"예: .\.venv\Scripts\python.exe -m pip install yfinance" "\n"
        "또는 py -m pip install yfinance"
    )

# ----------------- 사이드바 -----------------
st.sidebar.markdown(
    """
    <div style="margin-bottom:1rem;">
        <div style="font-size:1.15rem;font-weight:800;color:#fff;">포트폴리오 메뉴</div>
        <div style="font-size:0.85rem;color:#94b8e8;margin-top:4px;">매수 · 분할 매도 · 평가</div>
    </div>
    """,
    unsafe_allow_html=True,
)
with st.sidebar.expander("➕ 새 매수 기록", expanded=True):
    with st.form(key="add_stock_form", clear_on_submit=True, enter_to_submit=False, border=False):
        ticker = st.text_input("종목명 (예: AAPL, TSLA)").upper().strip()
        buy_price = st.number_input("매수 평단가 ($)", min_value=0.01, step=0.01, format="%.2f")
        quantity = st.number_input("보유 수량 (주)", min_value=1, step=1)
        target_price = st.number_input(
            "목표 매도가 ($, 선택)",
            min_value=0.0,
            value=buy_price,
            step=0.01,
            format="%.2f",
            help="0이면 목표가 없음",
        )
        submit_button = st.form_submit_button("포트폴리오에 추가", type="primary", use_container_width=True)

if submit_button:
    if ticker:
        existing_mask = st.session_state.df["종목명"] == ticker
        if existing_mask.any():
            idx = st.session_state.df.index[existing_mask][0]
            old_qty = int(st.session_state.df.at[idx, "보유수량"])
            old_price = float(st.session_state.df.at[idx, "매수평단가(USD)"])
            new_qty = old_qty + quantity
            new_avg = (old_price * old_qty + buy_price * quantity) / new_qty
            st.session_state.df.at[idx, "보유수량"] = new_qty
            st.session_state.df.at[idx, "매수평단가(USD)"] = round(new_avg, 6)
            if target_price > 0:
                st.session_state.df.at[idx, "목표매도가(USD)"] = target_price
            save_data(st.session_state.df)
            st.success(f"{ticker} 추가 매수 반영 — 평단가 ${new_avg:,.2f} · 총 {new_qty:,}주")
        else:
            new_data = pd.DataFrame([{
                "종목명": ticker,
                "매수평단가(USD)": buy_price,
                "보유수량": quantity,
                "목표매도가(USD)": target_price if target_price > 0 else 0.0,
            }])
            st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
            save_data(st.session_state.df)
            st.success(f"{ticker} 종목이 성공적으로 추가되었습니다!")
    else:
        st.error("종목명을 입력해주세요.")

if not st.session_state.df.empty:
    with st.sidebar.expander("✅ 보유·매도 관리", expanded=True):
        manage_ticker = st.selectbox("종목 선택", st.session_state.df["종목명"].unique(), key="manage_ticker")
        manage_row = st.session_state.df[st.session_state.df["종목명"] == manage_ticker].iloc[0]
        hold_qty = int(manage_row["보유수량"])

        st.caption(f"보유 **{hold_qty:,}주** · 매수가 **${manage_row['매수평단가(USD)']:,.2f}**")

        edit_target = st.number_input(
            "목표 매도가 ($, 선택)",
            min_value=0.0,
            value=float(manage_row["목표매도가(USD)"]) if pd.notna(manage_row["목표매도가(USD)"]) else 0.0,
            step=0.01,
            format="%.2f",
            key="manage_target",
        )
        if st.button("목표가 저장", use_container_width=True):
            idx = st.session_state.df.index[st.session_state.df["종목명"] == manage_ticker][0]
            st.session_state.df.at[idx, "목표매도가(USD)"] = edit_target if edit_target > 0 else 0.0
            save_data(st.session_state.df)
            st.success(f"{manage_ticker} 목표가 저장됨")

        st.markdown("---")
        manage_current_price = get_live_price(manage_ticker)
        if pd.notna(manage_current_price):
            st.caption(f"현재가 참고: **${manage_current_price:,.2f}**")

        manage_sell_price = st.number_input(
            "매도 가격 ($)",
            min_value=0.01,
            value=float(manage_current_price) if pd.notna(manage_current_price) else float(manage_row["매수평단가(USD)"]),
            step=0.01,
            format="%.2f",
            key="manage_sell_price",
        )
        sell_pct = st.slider(
            "매도 비율 (%)",
            min_value=1,
            max_value=100,
            value=100,
            key="manage_sell_pct",
            help="100%면 전량 매도, 그 외에는 일부만 매도 후 잔량 유지",
        )
        preview_qty = calc_sell_quantity(hold_qty, sell_pct)
        st.caption(
            f"매도 예정 **{preview_qty:,}주** ({preview_qty / hold_qty * 100:.1f}%) · "
            f"잔여 **{hold_qty - preview_qty:,}주**"
        )

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("매도 기록", use_container_width=True, type="primary"):
                sold_qty, remaining = record_partial_sell(manage_row, manage_sell_price, sell_pct)
                if remaining > 0:
                    st.success(f"{manage_ticker} {sold_qty:,}주 매도 · 잔여 {remaining:,}주")
                else:
                    st.success(f"{manage_ticker} 전량 매도 완료 ({sold_qty:,}주)")
                st.rerun()
        with btn_col2:
            if st.button("보유 삭제", use_container_width=True):
                st.session_state.df = st.session_state.df[st.session_state.df["종목명"] != manage_ticker].reset_index(drop=True)
                save_data(st.session_state.df)
                st.success(f"{manage_ticker} 보유 삭제됨")
                st.rerun()

with st.sidebar.expander("📡 시세 갱신", expanded=True):
    st.session_state.auto_quote_refresh = st.toggle(
        "자동 시세 갱신",
        value=st.session_state.auto_quote_refresh,
        help="ON: 주기적으로 현재가 자동 조회 · OFF: 시세 고정(새로고침 없음)",
    )

    live_quote_secs = 0
    if st.session_state.auto_quote_refresh:
        st.session_state.quote_refresh_interval = st.selectbox(
            "갱신 간격",
            [3, 5, 10, 15, 30],
            index=[3, 5, 10, 15, 30].index(st.session_state.quote_refresh_interval)
            if st.session_state.quote_refresh_interval in [3, 5, 10, 15, 30]
            else 1,
            format_func=lambda x: f"{x}초마다",
        )
        live_quote_secs = st.session_state.quote_refresh_interval
        st.caption(f"🟢 **ON** — {live_quote_secs}초마다 현재가 자동 갱신")
    else:
        st.caption("⏸ **OFF** — 시세가 자동으로 바뀌지 않습니다")
    st.caption("※ yfinance 무료 데이터는 HTS 실시간과 다를 수 있습니다.")

# ----------------- 메인 화면 -----------------
if st.session_state.df.empty:
    st.markdown(
        """
        <div class="empty-state">
            <h3>📭 아직 보유 종목이 없습니다</h3>
            <p>왼쪽 사이드바 <strong>「➕ 새 매수 기록」</strong>에서 종목을 추가하면<br>
            실시간 평가·시뮬레이션·매도 내역을 확인할 수 있습니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    if st.session_state.auto_quote_refresh:
        st.info(
            f"🟢 자동 시세 갱신 **ON** ({st.session_state.quote_refresh_interval}초) · "
            f"마지막 조회 {st.session_state.get('quotes_updated_at', '—')}"
        )
    else:
        st.info(
            f"⏸ 자동 시세 갱신 **OFF** · 마지막 조회 {st.session_state.get('quotes_updated_at', '—')} · "
            "사이드바 스위치를 켜면 자동 갱신됩니다."
        )

    tab_portfolio, tab_simulator, tab_history = st.tabs(
        ["📊 보유 (미실현)", "📈 매도 시뮬레이션", "📁 매도 내역 (실현)"]
    )

    with tab_portfolio:
        if live_quote_secs > 0:

            @st.fragment(run_every=live_quote_secs)
            def live_portfolio_panel():
                render_portfolio_tab(build_portfolio_df(), live_mode=True)

            live_portfolio_panel()
        else:
            render_portfolio_tab(build_portfolio_df(), live_mode=False)

    with tab_simulator:
        if live_quote_secs > 0:

            @st.fragment(run_every=live_quote_secs)
            def live_simulator_panel():
                render_simulator_tab(build_portfolio_df(), live_mode=True)

            live_simulator_panel()
        else:
            render_simulator_tab(build_portfolio_df(), live_mode=False)

    with tab_history:
        st.markdown(
            """
            <div class="section-card">
                <h3>매도 내역</h3>
                <p>분할·전량 매도 기록과 실현 손익을 확인합니다.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.session_state.history.empty:
            st.info("아직 매도 기록이 없습니다. 사이드바 **「✅ 보유·매도 관리」**에서 매도를 기록하세요.")
        else:
            history_total_profit = st.session_state.history["매도손익($)"].sum()
            history_avg_roi = st.session_state.history["매도수익률(%)"].mean()
            hcol1, hcol2, hcol3 = st.columns(3)
            hcol1.metric("누적 실현 손익", f"${history_total_profit:+,.2f}", help="매도 기록으로 확정·저장된 손익")
            hcol2.metric("평균 실현 수익률", f"{history_avg_roi:+.2f}%", help="매도 건별 실현 수익률 평균")
            hcol3.metric("매도 건수", f"{len(st.session_state.history):,}건")
            st.dataframe(
                st.session_state.history.style.format({
                    "매수평단가(USD)": "${:,.2f}",
                    "매도수량": "{:,} 주",
                    "매도비율(%)": "{:.1f}%",
                    "매도가(USD)": "${:,.2f}",
                    "매도손익($)": "${:,.2f}",
                    "매도수익률(%)": "{:+.2f}%",
                }, na_rep="N/A").apply(profit_loss_color, subset=["매도손익($)", "매도수익률(%)"]),
                use_container_width=True,
                hide_index=True,
            )
            with st.expander("🗑 매도 기록 삭제"):
                opts = {
                    f"{row['종목명']} | {row['매도일시']} | {int(row['매도수량'])}주 @ ${row['매도가(USD)']:,.2f}": i
                    for i, row in st.session_state.history.iterrows()
                }
                sel_label = st.selectbox("삭제할 기록 선택", list(opts.keys()), key="del_hist_sel")
                btn_d, btn_a = st.columns(2)
                with btn_d:
                    if st.button("선택 기록 삭제", use_container_width=True, type="primary"):
                        st.session_state._del_hist_idx = opts[sel_label]
                        _confirm_del_history()
                with btn_a:
                    if st.button("전체 매도 내역 삭제", use_container_width=True):
                        _confirm_clear_history()