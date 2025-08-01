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
    page_title="Loyalty Status Impact",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling for loyalty tiers
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #007acc;
        margin: 1rem 0;
    }
    .risk-high { border-left-color: #dc3545 !important; }
    .risk-medium { border-left-color: #ffc107 !important; }
    .risk-low { border-left-color: #28a745 !important; }
    .tier-header {
        text-align: center;
        font-size: 1.2em;
        font-weight: bold;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Snowpark session
@st.cache_resource
def init_session():
    return get_active_session()

session = init_session()

# Data loading functions
@st.cache_data(ttl=600)
def load_loyalty_data():
    """Load comprehensive customer loyalty data"""
    query = """
    SELECT 
        phone_number,
        status,
        points,
        CASE 
            WHEN status = 'Gold' THEN 1000
            WHEN status = 'Silver' THEN 500  
            WHEN status = 'Bronze' THEN 200
            ELSE 100
        END as estimated_monthly_value
    FROM TELCO_NETWORK_OPTIMIZATION_PROD.RAW.CUSTOMER_LOYALTY
    """
    df = session.sql(query).to_pandas()
    df.columns = df.columns.str.lower()
    return df

@st.cache_data(ttl=600)
def load_support_data():
    """Load support tickets with additional metrics"""
    query = """
    SELECT 
        ticket_id,
        cell_id,
        customer_name,
        customer_email,
        service_type,
        sentiment_score,
        request,
        contact_preference
    FROM TELCO_NETWORK_OPTIMIZATION_PROD.RAW.SUPPORT_TICKETS
    """
    df = session.sql(query).to_pandas()
    df.columns = df.columns.str.lower()
    return df

@st.cache_data(ttl=600)
def load_cell_tower_performance():
    """Load cell tower performance metrics"""
    query = """
    SELECT 
        cell_id,
        msisdn as phone_number,
        call_release_code,
        ROUND(cell_latitude, 4) AS latitude,
        ROUND(cell_longitude, 4) AS longitude
    FROM TELCO_NETWORK_OPTIMIZATION_PROD.RAW.CELL_TOWER
    """
    df = session.sql(query).to_pandas()
    df.columns = df.columns.str.lower()
    return df

# Load all data
with st.spinner("🔄 Loading loyalty and support data..."):
    loyalty_df = load_loyalty_data()
    support_df = load_support_data()
    cell_tower_df = load_cell_tower_performance()

# Page header
st.title("🥇 Loyalty Status Impact Analysis")
st.markdown("**Deep dive into how network performance and support issues impact customers across loyalty tiers**")

# Executive Overview Cards
st.markdown("## 📊 Loyalty Program Overview")

# Calculate key loyalty metrics
total_customers = len(loyalty_df)
gold_customers = len(loyalty_df[loyalty_df['status'] == 'Gold'])
silver_customers = len(loyalty_df[loyalty_df['status'] == 'Silver'])
bronze_customers = len(loyalty_df[loyalty_df['status'] == 'Bronze'])
total_value_at_risk = loyalty_df['estimated_monthly_value'].sum()

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Customers", f"{total_customers:,}")
col2.metric("🥇 Gold Tier", f"{gold_customers:,}", f"{gold_customers/total_customers*100:.1f}%")
col3.metric("🥈 Silver Tier", f"{silver_customers:,}", f"{silver_customers/total_customers*100:.1f}%")
col4.metric("🥉 Bronze Tier", f"{bronze_customers:,}", f"{bronze_customers/total_customers*100:.1f}%")
col5.metric("💰 Monthly Value at Risk", f"${total_value_at_risk:,.0f}")

# Loyalty Distribution Visualization
st.markdown("### 🏆 Loyalty Tier Distribution & Value Analysis")

col1, col2 = st.columns(2)

with col1:
    # Pie chart of loyalty distribution
    loyalty_counts = loyalty_df['status'].value_counts().reset_index()
    loyalty_counts.columns = ['Loyalty Status', 'Customer Count']
    
    colors = {'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}
    color_sequence = [colors.get(status, '#1f77b4') for status in loyalty_counts['Loyalty Status']]
    
    fig_pie = px.pie(
        loyalty_counts,
        values='Customer Count',
        names='Loyalty Status',
        title='Customer Distribution by Loyalty Tier',
        color_discrete_sequence=color_sequence
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    # Value analysis by tier
    value_analysis = loyalty_df.groupby('status').agg({
        'estimated_monthly_value': ['sum', 'mean'],
        'points': 'mean',
        'days_in_tier': 'mean'
    }).round(2)
    
    value_analysis.columns = ['Total Monthly Value', 'Avg Monthly Value', 'Avg Points', 'Avg Days in Tier']
    value_analysis = value_analysis.reset_index()
    
    fig_value = px.bar(
        value_analysis,
        x='status',
        y='Total Monthly Value',
        title='Total Monthly Value by Loyalty Tier',
        color='status',
        color_discrete_map=colors,
        text='Total Monthly Value'
    )
    fig_value.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig_value.update_layout(showlegend=False)
    st.plotly_chart(fig_value, use_container_width=True)

# Merge data for comprehensive analysis
merged_data = pd.merge(loyalty_df, support_df, left_on='phone_number', right_on='customer_id', how='left')
network_impact = pd.merge(merged_data, cell_tower_df, on='phone_number', how='left')

# Support Ticket Analysis by Loyalty Tier
st.markdown("## 🎫 Support Ticket Analysis by Loyalty Tier")

# Calculate support metrics by loyalty tier
support_metrics = merged_data.groupby('status').agg({
    'ticket_id': 'count',
    'phone_number': 'nunique',
    'sentiment_score': 'mean',
    'resolution_hours': 'mean',
    'priority': lambda x: (x == 'High').sum(),
    'estimated_monthly_value': 'sum'
}).round(2)

support_metrics.columns = ['Total Tickets', 'Customers with Tickets', 'Avg Sentiment', 'Avg Resolution Hours', 'High Priority Tickets', 'Value at Risk']
support_metrics = support_metrics.reset_index()
support_metrics['Tickets per Customer'] = (support_metrics['Total Tickets'] / support_metrics['Customers with Tickets']).round(2)
support_metrics['Risk Score'] = (
    support_metrics['Tickets per Customer'] * 0.3 + 
    (1 - support_metrics['Avg Sentiment']) * 0.4 + 
    (support_metrics['High Priority Tickets'] / support_metrics['Total Tickets']) * 0.3
).round(3)

col1, col2 = st.columns(2)

with col1:
    # Tickets per customer by tier
    fig_tickets = px.bar(
        support_metrics,
        x='status',
        y='Tickets per Customer',
        title='Average Support Tickets per Customer',
        color='status',
        color_discrete_map=colors,
        text='Tickets per Customer'
    )
    fig_tickets.update_traces(textposition='outside')
    fig_tickets.update_layout(showlegend=False)
    st.plotly_chart(fig_tickets, use_container_width=True)

with col2:
    # Sentiment analysis by tier
    fig_sentiment = px.bar(
        support_metrics,
        x='status',
        y='Avg Sentiment',
        title='Average Customer Sentiment by Tier',
        color='status',
        color_discrete_map=colors,
        text='Avg Sentiment'
    )
    fig_sentiment.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_sentiment.update_layout(showlegend=False)
    st.plotly_chart(fig_sentiment, use_container_width=True)

# Detailed Support Metrics Table
st.markdown("### 📋 Detailed Support Metrics by Loyalty Tier")
st.dataframe(support_metrics, use_container_width=True, hide_index=True)

# Service Type Analysis
st.markdown("## 🔧 Service Type Impact Analysis")

if not merged_data.empty:
    service_analysis = merged_data.groupby(['status', 'service_type']).agg({
        'ticket_id': 'count',
        'sentiment_score': 'mean',
        'resolution_hours': 'mean'
    }).reset_index()
    
    service_analysis.columns = ['Loyalty Status', 'Service Type', 'Ticket Count', 'Avg Sentiment', 'Avg Resolution Hours']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Service type distribution by loyalty tier
        fig_service = px.bar(
            service_analysis,
            x='Service Type',
            y='Ticket Count',
            color='Loyalty Status',
            title='Support Tickets by Service Type & Loyalty Tier',
            barmode='group',
            color_discrete_map=colors
        )
        st.plotly_chart(fig_service, use_container_width=True)
    
    with col2:
        # Resolution time by service type and tier
        fig_resolution = px.box(
            merged_data.dropna(subset=['resolution_hours']),
            x='service_type',
            y='resolution_hours',
            color='status',
            title='Resolution Time Distribution by Service Type',
            color_discrete_map=colors
        )
        st.plotly_chart(fig_resolution, use_container_width=True)

# Priority Analysis
st.markdown("## ⚠️ Priority & Escalation Analysis")

if 'priority' in merged_data.columns:
    priority_analysis = merged_data.groupby(['status', 'priority']).size().reset_index(name='count')
    priority_total = merged_data.groupby('status').size().reset_index(name='total')
    priority_analysis = priority_analysis.merge(priority_total, on='status')
    priority_analysis['percentage'] = (priority_analysis['count'] / priority_analysis['total'] * 100).round(1)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Priority distribution
        fig_priority = px.bar(
            priority_analysis,
            x='priority',
            y='count',
            color='status',
            title='Issue Priority Distribution by Loyalty Tier',
            barmode='group',
            color_discrete_map=colors
        )
        st.plotly_chart(fig_priority, use_container_width=True)
    
    with col2:
        # High priority percentage by tier
        high_priority = priority_analysis[priority_analysis['priority'] == 'High']
        if not high_priority.empty:
            fig_high_priority = px.bar(
                high_priority,
                x='status',
                y='percentage',
                title='High Priority Tickets (% of Total) by Tier',
                color='status',
                color_discrete_map=colors,
                text='percentage'
            )
            fig_high_priority.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_high_priority.update_layout(showlegend=False)
            st.plotly_chart(fig_high_priority, use_container_width=True)

# Network Performance Impact
st.markdown("## 📡 Network Performance Impact on Loyalty Tiers")

if not network_impact.empty:
    # Calculate network failure rates by loyalty tier
    network_metrics = network_impact.groupby('status').agg({
        'call_release_code': lambda x: (x != 0).sum(),
        'phone_number': 'count',
        'sentiment_score': 'mean'
    }).reset_index()
    
    network_metrics['failure_rate'] = (network_metrics['call_release_code'] / network_metrics['phone_number'] * 100).round(2)
    network_metrics.columns = ['Loyalty Status', 'Failed Calls', 'Total Calls', 'Avg Sentiment', 'Failure Rate (%)']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Network failure rate by tier
        fig_failure = px.bar(
            network_metrics,
            x='Loyalty Status',
            y='Failure Rate (%)',
            title='Network Failure Rate by Loyalty Tier',
            color='Loyalty Status',
            color_discrete_map=colors,
            text='Failure Rate (%)'
        )
        fig_failure.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_failure.update_layout(showlegend=False)
        st.plotly_chart(fig_failure, use_container_width=True)
    
    with col2:
        # Correlation between failure rate and sentiment
        if not network_impact[['sentiment_score', 'call_release_code']].isna().all().all():
            fig_correlation = px.scatter(
                network_impact.dropna(subset=['sentiment_score']),
                x='call_release_code',
                y='sentiment_score',
                color='status',
                title='Network Performance vs Customer Sentiment',
                color_discrete_map=colors,
                labels={'call_release_code': 'Call Release Code (0=Success)', 'sentiment_score': 'Sentiment Score'}
            )
            st.plotly_chart(fig_correlation, use_container_width=True)

# Risk Assessment
st.markdown("## 🚨 Loyalty Risk Assessment")

# Calculate risk indicators
risk_indicators = support_metrics.copy()
risk_indicators['Churn Risk'] = 'Low'
risk_indicators.loc[risk_indicators['Risk Score'] > 0.6, 'Churn Risk'] = 'High'
risk_indicators.loc[(risk_indicators['Risk Score'] > 0.3) & (risk_indicators['Risk Score'] <= 0.6), 'Churn Risk'] = 'Medium'

col1, col2, col3 = st.columns(3)

# Risk cards for each tier
tiers = ['Gold', 'Silver', 'Bronze']
tier_colors = ['#FFD700', '#C0C0C0', '#CD7F32']
risk_colors = {'High': '#dc3545', 'Medium': '#ffc107', 'Low': '#28a745'}

for i, tier in enumerate(tiers):
    tier_data = risk_indicators[risk_indicators['status'] == tier]
    if not tier_data.empty:
        risk_level = tier_data.iloc[0]['Churn Risk']
        risk_score = tier_data.iloc[0]['Risk Score']
        value_at_risk = tier_data.iloc[0]['Value at Risk']
        
        col = [col1, col2, col3][i]
        
        col.markdown(f"""
        <div class="metric-card risk-{risk_level.lower()}">
            <div class="tier-header" style="color: {tier_colors[i]};">🏆 {tier} Tier</div>
            <p><strong>Risk Level:</strong> <span style="color: {risk_colors[risk_level]};">{risk_level}</span></p>
            <p><strong>Risk Score:</strong> {risk_score:.3f}</p>
            <p><strong>Value at Risk:</strong> ${value_at_risk:,.0f}</p>
            <p><strong>Avg Tickets:</strong> {tier_data.iloc[0]['Tickets per Customer']}</p>
            <p><strong>Avg Sentiment:</strong> {tier_data.iloc[0]['Avg Sentiment']:.2f}</p>
        </div>
        """, unsafe_allow_html=True)

# Recommendations
st.markdown("## 🎯 Strategic Recommendations")

# Generate tier-specific recommendations
recommendations = {
    'Gold': [],
    'Silver': [],
    'Bronze': []
}

for tier in tiers:
    tier_data = risk_indicators[risk_indicators['status'] == tier]
    if not tier_data.empty:
        data = tier_data.iloc[0]
        
        if data['Churn Risk'] == 'High':
            recommendations[tier].append("🚨 **IMMEDIATE ACTION REQUIRED** - High churn risk detected")
            recommendations[tier].append("📞 Implement proactive outreach program")
            recommendations[tier].append("🎁 Consider loyalty rewards or service credits")
        
        if data['Avg Resolution Hours'] > 24:
            recommendations[tier].append(f"⏱️ Reduce resolution time (currently {data['Avg Resolution Hours']:.1f}h)")
        
        if data['Avg Sentiment'] < 0.5:
            recommendations[tier].append("😔 Improve customer satisfaction through better service quality")
        
        if data['High Priority Tickets'] > data['Total Tickets'] * 0.2:
            recommendations[tier].append("⚠️ Address high-priority issue patterns")

col1, col2, col3 = st.columns(3)

for i, tier in enumerate(tiers):
    col = [col1, col2, col3][i]
    col.markdown(f"### {tier} Tier Actions")
    
    if recommendations[tier]:
        for rec in recommendations[tier]:
            col.markdown(f"- {rec}")
    else:
        col.success("✅ No immediate actions required")

# Summary Statistics
st.markdown("## 📊 Executive Summary")

summary_data = {
    'Metric': [
        'Total Customers',
        'High-Value Customers (Gold)',
        'Customers with Support Issues',
        'Average Resolution Time (hours)',
        'Overall Customer Sentiment',
        'Total Monthly Value at Risk',
        'High-Risk Tier Customers'
    ],
    'Value': [
        f"{total_customers:,}",
        f"{gold_customers:,} ({gold_customers/total_customers*100:.1f}%)",
        f"{support_metrics['Customers with Tickets'].sum():,.0f}",
        f"{support_metrics['Avg Resolution Hours'].mean():.1f}",
        f"{support_metrics['Avg Sentiment'].mean():.2f}",
        f"${total_value_at_risk:,.0f}",
        f"{len(risk_indicators[risk_indicators['Churn Risk'] == 'High']):,} tiers"
    ]
}

summary_df = pd.DataFrame(summary_data)
st.dataframe(summary_df, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.caption(f"💡 **Insight:** Loyalty tier analysis updated {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} | Data source: Snowflake TELCO_NETWORK_OPTIMIZATION_PROD")
st.caption("🎯 **Focus Areas:** Customer retention, service quality improvement, and loyalty program optimization")