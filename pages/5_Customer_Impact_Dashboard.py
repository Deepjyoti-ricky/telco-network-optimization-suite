import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from snowflake.snowpark.context import get_active_session
import _snowflake
from datetime import datetime, timedelta
import numpy as np

# Page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="Customer Impact Dashboard",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
    <style>
    .metric-container { 
        background-color: #f0f2f6; 
        padding: 1rem; 
        border-radius: 0.5rem; 
        margin: 0.5rem 0;
    }
    .impact-high { background-color: #ffebee; border-left: 4px solid #f44336; }
    .impact-medium { background-color: #fff3e0; border-left: 4px solid #ff9800; }
    .impact-low { background-color: #e8f5e8; border-left: 4px solid #4caf50; }
    .loyalty-gold { color: #ffd700; font-weight: bold; }
    .loyalty-silver { color: #c0c0c0; font-weight: bold; }
    .loyalty-bronze { color: #cd7f32; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Initialize Snowpark session
@st.cache_resource
def init_session():
    return get_active_session()

session = init_session()

# Data loading functions
@st.cache_data(ttl=600)
def load_customer_loyalty():
    """Load customer loyalty data from Snowflake"""
    query = """
    SELECT 
        phone_number,
        status,
        points,
        tier_start_date,
        tier_end_date
    FROM TELCO_NETWORK_OPTIMIZATION_PROD.RAW.CUSTOMER_LOYALTY
    """
    df = session.sql(query).to_pandas()
    df.columns = df.columns.str.lower()
    return df

@st.cache_data(ttl=600)
def load_support_tickets():
    """Load support tickets data from Snowflake"""
    query = """
    SELECT 
        ticket_id,
        cell_id,
        customer_id,
        service_type,
        issue_description,
        priority,
        status as ticket_status,
        sentiment_score,
        created_date,
        resolved_date,
        request
    FROM TELCO_NETWORK_OPTIMIZATION_PROD.RAW.SUPPORT_TICKETS
    """
    df = session.sql(query).to_pandas()
    df.columns = df.columns.str.lower()
    return df

@st.cache_data(ttl=600)
def load_cell_tower_data():
    """Load cell tower performance data"""
    query = """
    SELECT 
        cell_id,
        msisdn,
        call_release_code,
        ROUND(cell_latitude, 4) AS latitude,
        ROUND(cell_longitude, 4) AS longitude,
        SUM(CASE WHEN call_release_code = 0 THEN 1 ELSE 0 END) AS total_success,
        COUNT(*) AS total_calls,
        ROUND((SUM(CASE WHEN call_release_code != 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2) AS failure_rate
    FROM TELCO_NETWORK_OPTIMIZATION_PROD.RAW.CELL_TOWER
    GROUP BY cell_id, msisdn, call_release_code, latitude, longitude
    """
    df = session.sql(query).to_pandas()
    df.columns = df.columns.str.lower()
    return df

# Load data
with st.spinner("Loading customer impact data..."):
    loyalty_df = load_customer_loyalty()
    tickets_df = load_support_tickets()
    cell_tower_df = load_cell_tower_data()

# Page header
st.title("👥 Customer Impact Dashboard")
st.markdown("**Analyze how network performance impacts customers across different loyalty tiers**")

# Sidebar filters
st.sidebar.header("🔧 Filters & Controls")

with st.sidebar.expander("Time Period", expanded=True):
    # Note: Since we don't have actual date filtering in the sample data, we'll show this for demo
    date_range = st.selectbox(
        "Analysis Period",
        ["Last 30 Days", "Last 90 Days", "Last 6 Months", "Last Year", "All Time"],
        index=4  # Default to "All Time"
    )

with st.sidebar.expander("Customer Segments", expanded=True):
    loyalty_statuses = st.multiselect(
        "Loyalty Status",
        options=sorted(loyalty_df['status'].unique()),
        default=sorted(loyalty_df['status'].unique())
    )

with st.sidebar.expander("Issue Types", expanded=True):
    service_types = st.multiselect(
        "Service Types",
        options=sorted(tickets_df['service_type'].unique()),
        default=sorted(tickets_df['service_type'].unique())
    )

# Filter data based on sidebar selections
filtered_loyalty = loyalty_df[loyalty_df['status'].isin(loyalty_statuses)]
filtered_tickets = tickets_df[tickets_df['service_type'].isin(service_types)]

# Merge data for analysis
# Join loyalty with cell tower data on phone number
loyalty_network = pd.merge(
    filtered_loyalty, 
    cell_tower_df, 
    left_on='phone_number', 
    right_on='msisdn', 
    how='inner'
)

# Join with support tickets on customer phone number/ID
# Note: We'll use cell_id as a proxy for linking customers
customer_impact = pd.merge(
    loyalty_network,
    filtered_tickets,
    on='cell_id',
    how='left'
)

# Key Metrics Overview
st.markdown("## 📊 Executive Summary")

col1, col2, col3, col4 = st.columns(4)

total_customers = len(filtered_loyalty)
customers_with_issues = len(customer_impact.dropna(subset=['ticket_id']))
avg_sentiment = customer_impact['sentiment_score'].mean() if not customer_impact['sentiment_score'].isna().all() else 0
avg_failure_rate = customer_impact['failure_rate'].mean() if not customer_impact['failure_rate'].isna().all() else 0

col1.metric("Total Customers", f"{total_customers:,}")
col2.metric("Customers with Issues", f"{customers_with_issues:,}")
col3.metric("Avg Sentiment Score", f"{avg_sentiment:.2f}")
col4.metric("Avg Network Failure Rate", f"{avg_failure_rate:.1f}%")

# Impact by Loyalty Tier
st.markdown("## 🏆 Impact Analysis by Loyalty Tier")

# Calculate metrics by loyalty status
loyalty_impact = customer_impact.groupby('status').agg({
    'phone_number': 'nunique',
    'ticket_id': 'count',
    'sentiment_score': 'mean',
    'failure_rate': 'mean',
    'points': 'mean'
}).round(2)

loyalty_impact.columns = ['Customer Count', 'Total Tickets', 'Avg Sentiment', 'Avg Failure Rate (%)', 'Avg Loyalty Points']
loyalty_impact = loyalty_impact.reset_index()
loyalty_impact['Tickets per Customer'] = (loyalty_impact['Total Tickets'] / loyalty_impact['Customer Count']).round(2)

col1, col2 = st.columns(2)

with col1:
    # Loyalty tier distribution chart
    loyalty_counts = filtered_loyalty['status'].value_counts().reset_index()
    loyalty_counts.columns = ['Loyalty Status', 'Customer Count']
    
    # Define colors for loyalty tiers
    colors = {'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}
    color_sequence = [colors.get(status, '#1f77b4') for status in loyalty_counts['Loyalty Status']]
    
    fig_loyalty = px.pie(
        loyalty_counts, 
        values='Customer Count', 
        names='Loyalty Status',
        title='Customer Distribution by Loyalty Status',
        color_discrete_sequence=color_sequence
    )
    st.plotly_chart(fig_loyalty, use_container_width=True)

with col2:
    # Tickets per customer by loyalty tier
    if not loyalty_impact.empty:
        fig_tickets = px.bar(
            loyalty_impact,
            x='status',
            y='Tickets per Customer',
            title='Average Tickets per Customer by Loyalty Tier',
            color='status',
            color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}
        )
        fig_tickets.update_layout(showlegend=False)
        st.plotly_chart(fig_tickets, use_container_width=True)

# Detailed loyalty impact table
st.markdown("### 📋 Loyalty Tier Impact Summary")
st.dataframe(loyalty_impact, use_container_width=True)

# Network Performance Impact
st.markdown("## 📡 Network Performance vs Customer Satisfaction")

col1, col2 = st.columns(2)

with col1:
    # Sentiment vs Failure Rate scatter plot
    if not customer_impact.empty and not customer_impact['sentiment_score'].isna().all():
        fig_scatter = px.scatter(
            customer_impact.dropna(subset=['sentiment_score', 'failure_rate']),
            x='failure_rate',
            y='sentiment_score',
            color='status',
            title='Customer Sentiment vs Network Failure Rate',
            labels={'failure_rate': 'Network Failure Rate (%)', 'sentiment_score': 'Sentiment Score'},
            color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("No sentiment data available for correlation analysis")

with col2:
    # Service type impact analysis
    if not customer_impact.empty:
        service_impact = customer_impact.groupby(['service_type', 'status']).agg({
            'sentiment_score': 'mean',
            'ticket_id': 'count'
        }).reset_index()
        
        if not service_impact.empty:
            fig_service = px.bar(
                service_impact,
                x='service_type',
                y='sentiment_score',
                color='status',
                title='Average Sentiment by Service Type & Loyalty',
                barmode='group',
                color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}
            )
            st.plotly_chart(fig_service, use_container_width=True)
        else:
            st.info("No service type data available")

# Geographic Impact Analysis
st.markdown("## 🗺️ Geographic Impact Analysis")

if not customer_impact.empty and not customer_impact[['latitude', 'longitude']].isna().all().all():
    # Cell tower impact heatmap
    geo_impact = customer_impact.groupby(['cell_id', 'latitude', 'longitude']).agg({
        'ticket_id': 'count',
        'sentiment_score': 'mean',
        'phone_number': 'nunique'
    }).reset_index()
    
    geo_impact.columns = ['cell_id', 'latitude', 'longitude', 'ticket_count', 'avg_sentiment', 'customer_count']
    
    # Create impact severity score
    geo_impact['impact_score'] = (
        geo_impact['ticket_count'] * 0.4 + 
        (1 - geo_impact['avg_sentiment']) * 0.6 * 10  # Normalize sentiment impact
    )
    
    fig_map = px.scatter_mapbox(
        geo_impact.head(100),  # Limit to top 100 for performance
        lat='latitude',
        lon='longitude',
        size='customer_count',
        color='impact_score',
        hover_name='cell_id',
        hover_data=['ticket_count', 'avg_sentiment'],
        color_continuous_scale='Reds',
        title='Customer Impact by Geographic Location',
        mapbox_style='open-street-map',
        zoom=6
    )
    fig_map.update_layout(height=500)
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("Geographic data not available for mapping")

# Issue Priority Analysis
st.markdown("## ⚠️ Issue Priority & Resolution Analysis")

if not customer_impact.empty and 'priority' in customer_impact.columns:
    col1, col2 = st.columns(2)
    
    with col1:
        # Priority distribution by loyalty tier
        priority_analysis = customer_impact.groupby(['status', 'priority']).size().reset_index(name='count')
        
        fig_priority = px.bar(
            priority_analysis,
            x='priority',
            y='count',
            color='status',
            title='Issue Priority Distribution by Loyalty Tier',
            barmode='group',
            color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}
        )
        st.plotly_chart(fig_priority, use_container_width=True)
    
    with col2:
        # Resolution status analysis
        if 'ticket_status' in customer_impact.columns:
            resolution_analysis = customer_impact.groupby(['status', 'ticket_status']).size().reset_index(name='count')
            
            fig_resolution = px.bar(
                resolution_analysis,
                x='ticket_status',
                y='count',
                color='status',
                title='Ticket Resolution Status by Loyalty Tier',
                barmode='group',
                color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}
            )
            st.plotly_chart(fig_resolution, use_container_width=True)

# Action Items and Recommendations
st.markdown("## 🎯 Recommendations & Action Items")

# Calculate key insights
high_impact_customers = customer_impact[
    (customer_impact['status'] == 'Gold') & 
    (customer_impact['sentiment_score'] < 0)
] if not customer_impact.empty and not customer_impact['sentiment_score'].isna().all() else pd.DataFrame()

problem_cells = customer_impact.groupby('cell_id').agg({
    'ticket_id': 'count',
    'sentiment_score': 'mean'
}).reset_index()
problem_cells = problem_cells[
    (problem_cells['ticket_id'] > problem_cells['ticket_id'].quantile(0.8)) |
    (problem_cells['sentiment_score'] < problem_cells['sentiment_score'].quantile(0.2))
] if not problem_cells.empty else pd.DataFrame()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🚨 High Priority Actions")
    if not high_impact_customers.empty:
        st.error(f"**{len(high_impact_customers)} Gold customers** with negative sentiment require immediate attention")
    else:
        st.success("No high-priority customer issues detected")
    
    if not problem_cells.empty:
        st.warning(f"**{len(problem_cells)} cell towers** showing high impact patterns")
    else:
        st.success("No problematic cell towers identified")

with col2:
    st.markdown("### 📞 Proactive Outreach")
    
    if not customer_impact.empty:
        medium_risk = customer_impact[
            (customer_impact['status'].isin(['Silver', 'Gold'])) & 
            (customer_impact['sentiment_score'] < 0.5) &
            (customer_impact['sentiment_score'] >= 0)
        ] if not customer_impact['sentiment_score'].isna().all() else pd.DataFrame()
        
        if not medium_risk.empty:
            st.info(f"**{len(medium_risk)} premium customers** showing declining satisfaction")
        else:
            st.success("Premium customers showing stable satisfaction")

with col3:
    st.markdown("### 📈 Loyalty Impact")
    
    if not loyalty_impact.empty:
        avg_tickets_gold = loyalty_impact[loyalty_impact['status'] == 'Gold']['Tickets per Customer'].iloc[0] if 'Gold' in loyalty_impact['status'].values else 0
        avg_tickets_bronze = loyalty_impact[loyalty_impact['status'] == 'Bronze']['Tickets per Customer'].iloc[0] if 'Bronze' in loyalty_impact['status'].values else 0
        
        if avg_tickets_gold > avg_tickets_bronze:
            st.warning("Gold customers experiencing more issues than Bronze customers")
        else:
            st.success("Premium customers receiving better service quality")

# Summary statistics
st.markdown("## 📋 Summary Statistics")

summary_stats = {
    "Total Customers Analyzed": len(filtered_loyalty),
    "Customers with Network Issues": customers_with_issues,
    "Average Sentiment Score": f"{avg_sentiment:.2f}",
    "Network Failure Rate": f"{avg_failure_rate:.1f}%",
    "Gold Tier Customers": len(filtered_loyalty[filtered_loyalty['status'] == 'Gold']),
    "Silver Tier Customers": len(filtered_loyalty[filtered_loyalty['status'] == 'Silver']),
    "Bronze Tier Customers": len(filtered_loyalty[filtered_loyalty['status'] == 'Bronze'])
}

summary_df = pd.DataFrame(list(summary_stats.items()), columns=['Metric', 'Value'])
st.dataframe(summary_df, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.caption(f"Data last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} | Source: Snowflake TELCO_NETWORK_OPTIMIZATION_PROD") 