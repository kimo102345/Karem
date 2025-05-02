import streamlit as st
from binance.client import Client
import pandas as pd
import pandas_ta as ta
import os

# إعدادات بينانس (ضع مفاتيحك هنا)
api_key = os.getenv("BINANCE_API_KEY") # أو اكتبها مباشرةً
api_secret = os.getenv("BINANCE_API_SECRET") # أو اكتبها مباشرةً
client = Client(api_key, api_secret)

# إعدادات Telegram (اختياري)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# واجهة المستخدم
st.set_page_config(layout="wide", page_title="Binance Analyzer")
st.markdown("<h1 style='text-align: center; color: #00ff00;'>Binance Trading Analyzer</h1>", unsafe_allow_html=True)

# اختيار الزوج
symbol = st.sidebar.selectbox("الزوج", ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT"])
timeframe = st.sidebar.selectbox("الإطار الزمني", ["15m", "1h", "4h"])

# جلب البيانات
@st.cache_data(ttl=300)
def get_data(symbol, timeframe):
    klines = client.get_klines(symbol=symbol, interval=timeframe, limit=100)
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'])
    df['close'] = pd.to_numeric(df['close'])
    return df

df = get_data(symbol, timeframe)

# حساب المؤشرات
df['RSI'] = ta.rsi(df['close'], length=14)
df['MACD'] = ta.macd(df['close'], fast=12, slow=26, signal=9)['MACD_12_26_9']
df['Volume_MA'] = df['volume'].rolling(20).mean()

# تحليل السيولة
liquidity_alert = "🔥 حركة سيولة عالية!" if df['volume'].iloc[-1] > 2 * df['Volume_MA'].iloc[-1] else ""

# عرض النتائج
col1, col2 = st.columns(2)
with col1:
    st.subheader(f"الرسم البياني لـ {symbol}")
    st.line_chart(df.set_index('timestamp')['close'])
with col2:
    st.subheader("المؤشرات")
    st.line_chart(df[['RSI', 'MACD']])
    st.error(liquidity_alert) if liquidity_alert else st.success("السيولة طبيعية")

# إشعارات Telegram (اختياري)
if liquidity_alert and TELEGRAM_TOKEN:
    import requests
    message = f"تنبيه: {liquidity_alert} على {symbol} ({timeframe})"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    requests.get(url)
