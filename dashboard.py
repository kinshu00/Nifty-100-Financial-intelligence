import sys
from pathlib import Path
import streamlit as st
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.app.data_service import load_intelligence, load_sectors, load_risk, company_price_history, company_financial_history

st.set_page_config(page_title='Nifty 100 Financial Intelligence', page_icon='📊', layout='wide')
st.title('Nifty 100 Financial Intelligence Platform')
st.caption('Phase 5 — Interactive analyst dashboard | Development/demo dataset')

companies = load_intelligence()
risk = load_risk()
companies = companies.merge(risk[['ticker', 'risk_score', 'risk_band']], on='ticker', how='left')

with st.sidebar:
    st.header('Filters')
    sectors = ['All'] + sorted(companies['sector'].dropna().unique().tolist())
    sector = st.selectbox('Sector', sectors)
    stances = ['All', 'Positive', 'Neutral', 'Caution']
    stance = st.selectbox('Analyst stance', stances)
    min_score = st.slider('Minimum financial strength', 0, 100, 0)

view = companies.copy()
if sector != 'All': view = view[view.sector == sector]
if stance != 'All': view = view[view.analyst_stance == stance]
view = view[view.financial_strength_score >= min_score]

c1,c2,c3,c4 = st.columns(4)
c1.metric('Companies', len(view))
c2.metric('Avg strength score', f"{view.financial_strength_score.mean():.1f}" if len(view) else 'N/A')
c3.metric('Positive stance', int((view.analyst_stance == 'Positive').sum()))
c4.metric('High+ risk', int(view.risk_band.isin(['High','Very High']).sum()))

st.subheader('Company Screener')
cols = ['ticker','company_name','sector','financial_strength_score','investment_flag','risk_score','risk_band','analyst_stance','roe_pct','opm_pct','debt_to_equity','cfo_pat_ratio']
st.dataframe(view[cols].sort_values('financial_strength_score', ascending=False), use_container_width=True, hide_index=True)

st.subheader('Risk Monitor')
risk_view = risk[risk.ticker.isin(view.ticker)].sort_values('risk_score', ascending=False)
st.bar_chart(risk_view.set_index('ticker')['risk_score'])

st.subheader('Sector Intelligence')
sec = load_sectors()
if sector != 'All': sec = sec[sec.sector == sector]
st.dataframe(sec, use_container_width=True, hide_index=True)

st.subheader('Company Detail')
ticker = st.selectbox('Select company', view.ticker.tolist() if len(view) else companies.ticker.tolist())
row = companies[companies.ticker == ticker].iloc[0]
left, right = st.columns(2)
with left:
    st.markdown(f"### {row.company_name} ({ticker})")
    st.write(f"**Sector:** {row.sector}  ")
    st.write(f"**Analyst stance:** {row.analyst_stance}  ")
    st.write(f"**Financial strength:** {row.financial_strength_score:.2f}/100  ")
    st.write(f"**Risk:** {row.risk_band} ({row.risk_score:.2f})")
    st.markdown('**Pros**')
    for item in str(row.pros).split('|'): st.write('• ' + item.strip())
    st.markdown('**Cons**')
    for item in str(row.cons).split('|'): st.write('• ' + item.strip())
with right:
    prices = company_price_history(ticker)
    if not prices.empty:
        prices['date'] = pd.to_datetime(prices['date'])
        st.line_chart(prices.set_index('date')['close'])
    financials = company_financial_history(ticker)
    if not financials.empty:
        st.line_chart(financials.set_index('year')[['sales','net_profit']])

st.divider()
st.caption('Automated analytical output from the project dataset. Not investment advice.')
