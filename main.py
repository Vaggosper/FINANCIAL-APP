# main.py
import os
import streamlit as st
import yfinance as yf
from openai import OpenAI

st.set_page_config(page_title="Financial Smart App", layout="wide")

# ---------------- Secure OpenAI key loader ----------------
def load_openai_key():
    # 1) Πρώτα από Streamlit Secrets (Cloud ή .streamlit/secrets.toml)
    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    # 2) Fallback σε ENV var
    return os.getenv("OPENAI_API_KEY")

OPENAI_API_KEY = load_openai_key()

if not OPENAI_API_KEY:
    st.error("❌ Δεν βρέθηκε OPENAI_API_KEY. Πρόσθεσέ το στο `.streamlit/secrets.toml` ή ως env var.")
    st.stop()

# Create OpenAI client safely
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------- helper functions ----------------
def get_stock_data(ticker, start_date='2024-01-01', end_date='2024-02-01'):
    return yf.download(ticker, start=start_date, end=end_date)

# ---------------- UI ----------------
st.title('Interactive Financial Stock Market Comparative Analysis Tool')

# Sidebar for user inputs
with st.sidebar:
    st.header('User Input Options')
    selected_stock = st.text_input('Enter Stock Ticker 1', 'AAPL').upper().strip()
    selected_stock2 = st.text_input('Enter Stock Ticker 2', 'GOOGL').upper().strip()
    chart_choice_1 = st.selectbox(f'Select Chart Type for {selected_stock}', ['Line', 'Bar'])
    chart_choice_2 = st.selectbox(f'Select Chart Type for {selected_stock2}', ['Line', 'Bar'])

# Fetch data
stock_data = get_stock_data(selected_stock)
stock_data2 = get_stock_data(selected_stock2)

col1, col2 = st.columns(2)

with col1:
    st.subheader(f"Displaying data for: {selected_stock}")
    st.write(stock_data)
    if not stock_data.empty:
        if chart_choice_1 == 'Line':
            st.line_chart(stock_data['Close'])
        else:
            st.bar_chart(stock_data['Close'])

with col2:
    st.subheader(f"Displaying data for: {selected_stock2}")
    st.write(stock_data2)
    if not stock_data2.empty:
        if chart_choice_2 == 'Line':
            st.line_chart(stock_data2['Close'])
        else:
            st.bar_chart(stock_data2['Close'])

# ---------------- Comparative analysis ----------------
if st.button('Comparative Performance'):
    # Basic safety: don't send full DataFrames to the model (tokens & privacy)
    def small_summary(df):
        if df.empty:
            return None
        close = df['Close']
        return {
            "first": float(close.iloc[0]),
            "last": float(close.iloc[-1]),
            "pct_change": float((close.iloc[-1] / close.iloc[0] - 1) * 100)
        }

    s1 = small_summary(stock_data)
    s2 = small_summary(stock_data2)

    if not s1 or not s2:
        st.error("Δεν υπάρχουν επαρκή δεδομένα για τα ticker.")
    else:
        prompt_text = (
            f"Compare stocks {selected_stock} and {selected_stock2} using these metrics:\n\n"
            f"{selected_stock}: {s1}\n"
            f"{selected_stock2}: {s2}\n\n"
            "Provide a concise markdown summary with bullets: performance, volatility note, highs/lows, conclusion (non-investment advice)."
        )

        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a financial analyst. Be concise, factual, no investment advice."},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0.2,
            )
            st.markdown(resp.choices[0].message.content)
        except Exception as e:
            st.error(f"OpenAI API error: {e}")
