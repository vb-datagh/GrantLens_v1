from datetime import date
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from analytics import prepare, pipeline_sql, safe_csv, PIPELINE_SQL

st.set_page_config(page_title='GrantLens | Funding intelligence', page_icon='◈', layout='wide')
st.markdown('''<style>.stApp {background:#f5f7f9} h1,h2,h3 {color:#133b3a}
[data-testid="stMetric"] {background:white;padding:20px;border-radius:12px;border:1px solid #dce6e4}
</style>''', unsafe_allow_html=True)
st.caption('GRANTLENS / DECISION INTELLIGENCE')
st.title('Turn your funding pipeline into a plan.')
st.write('Explore opportunity, surface gaps, and focus your next research sprint.')
with st.sidebar:
    st.header('Your workspace')
    upload = st.file_uploader('Import prospect CSV', type=['csv'])
    st.caption('Required schema and template are in the README. Uploads are processed by the running app; do not upload confidential data to a public deployment.')
    as_of = st.date_input('Analysis date', value=date(2026, 10, 29) if upload is None else date.today())
try:
    raw = pd.read_csv(upload if upload else Path(__file__).parent / 'data/demo.csv')
    df, issues = prepare(raw, as_of)
except (ValueError, UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
    st.error(f'Cannot analyze this file: {exc}')
    st.stop()
if upload is None:
    st.info('Demo workspace · fictional organizations and opportunities · snapshot: October 29, 2026. All amounts are USD.')
with st.sidebar:
    types = sorted(df.type.unique())
    selected = st.multiselect('Funding types', types, default=types)
    statuses = sorted(df.status.unique())
    stages = st.multiselect('Pipeline stages', statuses, default=statuses)
    st.download_button('Download CSV template', (Path(__file__).parent / 'data/demo.csv').read_bytes(), 'grantlens-template.csv', 'text/csv')
view = df[df.type.isin(selected) & df.status.isin(stages)]
valid = view[view.eligible_for_metrics]
active = valid[valid.active]
near = active[active.days_left.between(0, 30)]
cols = st.columns(4)
cols[0].metric('Active prospects', len(active))
cols[1].metric('Known active potential', f'${active.amount.sum():,.0f}')
cols[2].metric('Due within 30 days', len(near))
cols[3].metric('Amount coverage', f'{active.amount.notna().mean():.0%}' if len(active) else '—')
st.caption(f'{len(view) - len(valid)} selected records excluded due to duplicate identity, missing identity, or unknown status. Potential is the sum of recorded opportunity amounts, not expected revenue. Missing amounts are excluded.')
overview, actions, quality, method = st.tabs(['Business overview', 'Action queue', 'Data quality', 'Method & SQL'])
with overview:
    st.subheader('What needs your attention')
    if valid.empty:
        st.info('No valid records match these filters. Adjust your filters or resolve data issues.')
    else:
        st.write(f'**{len(near)} active prospects** have deadlines in the next 30 days; **{int(active.days_left.lt(0).sum())}** have past deadlines that need a status review.')
        st.write(f'**{int(active.amount.isna().sum())} active prospects** lack usable amounts and **{int(active.days_left.isna().sum())}** have unknown deadlines. Resolve these gaps before making a resource allocation decision.')
        left, right = st.columns(2)
        summary = pipeline_sql(valid)
        left.plotly_chart(px.bar(summary, x='status', y='prospects', title='Pipeline by stage', color_discrete_sequence=['#197c75']), width='stretch')
        landscape = active.groupby('type', as_index=False).amount.sum(min_count=1)
        right.plotly_chart(px.bar(landscape, x='type', y='amount', title='Known active potential by type (USD)', color_discrete_sequence=['#c27b45']), width='stretch')
        st.dataframe(summary, hide_index=True, width='stretch')
with actions:
    st.subheader('Prioritize the next research sprint')
    st.caption('Priority = 80% fit + 20% deadline urgency. Unknown fit stays unranked; unknown timing earns no urgency points. Past deadlines and closed prospects are unranked.')
    queue = valid.sort_values('priority', ascending=False, na_position='last')
    st.dataframe(queue[['funder','program','status','amount','fit_score','deadline','priority','next_action']], hide_index=True, width='stretch')
    st.download_button('Export selected analysis', safe_csv(queue), 'grantlens-analysis.csv', 'text/csv')
with quality:
    st.subheader('Trust starts with the source')
    st.caption('Quality findings cover the entire imported file, independently of sidebar filters. CSV row numbers include the header.')
    st.metric('Quality findings', len(issues))
    st.dataframe(issues, hide_index=True, width='stretch')
    st.download_button('Export quality findings', safe_csv(issues), 'grantlens-quality.csv', 'text/csv')
with method:
    st.subheader('Transparent by design')
    st.write('One row represents one funding opportunity. All amounts must use a single currency: USD. Fit is an analyst-supplied 0–100 assessment, not a probability of winning. Urgency declines linearly from 100 today to 0 at 90 days; later dates receive 0. Scoring does not establish eligibility.')
    st.write('Active stages: Research, Qualified, Preparing, Submitted. Awarded and Declined remain in stage counts but leave active potential. Potential can include overlapping opportunities and does not represent a forecast. Duplicated funder/program pairs are all excluded pending review; comparisons are case-sensitive after trimming whitespace.')
    st.write('Missing or invalid numbers become unknown, never zero. Missing or invalid deadlines remain unknown and are flagged. No funding source verification is performed. Filters apply before the following SQL runs in an in-memory SQLite database.')
    st.code(PIPELINE_SQL, language='sql')
