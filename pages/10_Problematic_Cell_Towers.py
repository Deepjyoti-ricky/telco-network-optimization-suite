import streamlit as st
import pandas as pd
import plotly.express as px
from snowflake.snowpark.context import get_active_session
from datetime import datetime

# ------------------------
# Page Configuration
# ------------------------
st.set_page_config(
    page_title="Network Health Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
    <style>
    .big-font { font-size:32px !important; font-weight:bold; }
    .metric-label { font-size: 16px; color: #888888; }
    .section-header { font-size:24px; margin-top:24px; margin-bottom:12px; }
    </style>
""", unsafe_allow_html=True)

# ------------------------
# Data Loading
# ------------------------
@st.cache_data(ttl=600)
def load_data():
    session = get_active_session()
    tickets = session.sql(
        """
        SELECT ticket_id, cell_id, request, sentiment_score
        FROM TELCO_NETWORK_OPTIMIZATION_PROD.RAW.SUPPORT_TICKETS
        """
    ).to_pandas()
    tickets.columns = tickets.columns.str.lower()
    towers = session.sql(
        """
        SELECT cell_id,
               pm_pdcp_lat_time_dl AS latency_dl,
               pm_ue_thp_time_dl AS throughput_dl,
               pm_erab_rel_abnormal_enb AS drop_rate,
               pm_prb_util_dl AS prb_util_dl
        FROM TELCO_NETWORK_OPTIMIZATION_PROD.RAW.CELL_TOWER
        """
    ).to_pandas()
    towers.columns = towers.columns.str.lower()
    return tickets, towers

tickets_df, towers_df = load_data()

# ------------------------
# Preprocessing & Metrics
# ------------------------
# Complaint categories
def categorize_complaint(text):
    t = text.lower() if isinstance(text, str) else ''
    if 'latency' in t: return 'Latency'
    if 'connection' in t: return 'Connection'
    if 'drop' in t: return 'Drops'
    if 'throughput' in t or 'speed' in t: return 'Throughput'
    if 'signal' in t: return 'Signal'
    return 'Other'

tickets_df['category'] = tickets_df['request'].apply(categorize_complaint)

# Aggregate metrics
agg_tickets = tickets_df.groupby('cell_id').agg(
    ticket_count=pd.NamedAgg(column='ticket_id', aggfunc='nunique'),
    avg_sentiment=pd.NamedAgg(column='sentiment_score', aggfunc='mean')
).reset_index()

metrics_df = (
    towers_df
    .merge(agg_tickets, on='cell_id', how='left')
    .fillna({'ticket_count': 0, 'avg_sentiment': 0})
)

# ------------------------
# Sidebar Filters & Controls
# ------------------------
st.sidebar.header("🔧 Filters & Analysis Controls")
with st.sidebar.expander("Filter Towers", expanded=True):
    min_tickets = st.slider(
        "Minimum Ticket Count", 0, int(metrics_df['ticket_count'].max()), 5
    )
    max_sentiment = st.slider(
        "Maximum Average Sentiment", float(metrics_df['avg_sentiment'].min()), float(metrics_df['avg_sentiment'].max()), 0.0
    )
    categories = st.multiselect(
        "Complaint Categories", sorted(tickets_df['category'].unique()), default=None
    )
    if not categories:
        categories = tickets_df['category'].unique().tolist()

with st.sidebar.expander("Anomaly Threshold", expanded=False):
    std_mult = st.slider(
        "Ticket Count Std Dev Multiplier", 1.0, 5.0, 2.0, step=0.5
    )

# Apply filters
df = metrics_df[
    (metrics_df['ticket_count'] >= min_tickets) &
    (metrics_df['avg_sentiment'] <= max_sentiment)
]
valid_ids = tickets_df[tickets_df['category'].isin(categories)]['cell_id'].unique()
df = df[df['cell_id'].isin(valid_ids)]

# ------------------------
# Dashboard Header & KPIs
# ------------------------
st.markdown("<div class='big-font'>Network Health Overview</div>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Towers", f"{len(metrics_df):,}")
col2.metric("Filtered Towers", f"{len(df):,}")
# Compute anomaly threshold
threshold = metrics_df['ticket_count'].mean() + std_mult * metrics_df['ticket_count'].std()
col3.metric("Anomaly Threshold", f"{threshold:.0f}")
anom_count = df[df['ticket_count'] > threshold].shape[0]
col4.metric("Towers Above Threshold", f"{anom_count}")
st.markdown("---")

# ------------------------
# Main Tabs (3 Tabs)
# ------------------------
tab1, tab2, tab3 = st.tabs([
    "📈 Top Towers",
    "📊 Category Analysis",
    "⚠️ Anomalies"
])

# Top Towers
with tab1:
    st.markdown("<div class='section-header'>Top Problematic Towers</div>", unsafe_allow_html=True)
    st.dataframe(
        df.sort_values('ticket_count', ascending=False)
          .head(10)
          .style.format({
              'ticket_count': '{:.0f}',
              'avg_sentiment': '{:.2f}',
              'latency_dl': '{:.1f}',
              'drop_rate': '{:.1f}'
          }),
        use_container_width=True
    )

# Category Analysis
with tab2:
    st.markdown("<div class='section-header'>Latency by Complaint Category</div>", unsafe_allow_html=True)
    cat_df = (
        tickets_df[['cell_id','category']]
        .drop_duplicates()
        .merge(metrics_df[['cell_id','latency_dl']], on='cell_id')
    )
    # Sample to limit data volume: max 200 per category
    cat_df = (
        cat_df
        .groupby('category', group_keys=False)
        .apply(lambda grp: grp.sample(n=min(len(grp), 200), random_state=42))
        .reset_index(drop=True)
    )
    fig = px.box(
        cat_df, x='category', y='latency_dl', points=False,
        labels={'category':'Category','latency_dl':'Latency (ms)'},
        template='plotly_white'
    )
    fig.update_layout(margin=dict(t=40,b=20))
    st.plotly_chart(fig, use_container_width=True)

# Anomalies
with tab3:
    st.markdown("<div class='section-header'>Anomalous Towers</div>", unsafe_allow_html=True)
    anomalies = df[df['ticket_count'] > threshold]
    if not anomalies.empty:
        st.dataframe(
            anomalies[['cell_id','ticket_count','avg_sentiment','latency_dl','drop_rate']]
              .sort_values('ticket_count', ascending=False),
            use_container_width=True
        )
    else:
        st.success("No anomalies detected.")

# End of dashboard
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 