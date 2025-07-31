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
    page_title="Service Type Performance Breakdown",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling for service type analysis
st.markdown("""
    <style>
    .service-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #007acc;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .performance-excellent { border-left-color: #28a745 !important; background-color: #f8fff9 !important; }
    .performance-good { border-left-color: #17a2b8 !important; background-color: #f0fdff !important; }
    .performance-fair { border-left-color: #ffc107 !important; background-color: #fffcf0 !important; }
    .performance-poor { border-left-color: #dc3545 !important; background-color: #fff5f5 !important; }
    
    .metric-highlight {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .service-type-header {
        font-size: 1.1em;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    
    .kpi-container {
        display: flex;
        justify-content: space-around;
        background-color: #f1f3f4;
        padding: 1rem;
        border-radius: 8px;
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
def load_service_performance_data():
    """Load comprehensive service type performance data"""
    query = """
    WITH service_metrics AS (
        SELECT 
            st.service_type,
            st.ticket_id,
            st.cell_id,
            st.customer_id,
            st.priority,
            st.status as ticket_status,
            st.sentiment_score,
            st.created_date,
            st.resolved_date,
            CASE 
                WHEN st.resolved_date IS NOT NULL AND st.created_date IS NOT NULL 
                THEN DATEDIFF(hour, st.created_date, st.resolved_date)
                ELSE NULL 
            END as resolution_hours,
            cl.status as loyalty_status,
            cl.points as loyalty_points,
            ct.call_release_code,
            ct.cell_latitude,
            ct.cell_longitude,
            ct.msisdn
        FROM TELCO_NETWORK_OPTIMIZATION_PROD.RAW.SUPPORT_TICKETS st
        LEFT JOIN TELCO_NETWORK_OPTIMIZATION_PROD.RAW.CUSTOMER_LOYALTY cl 
            ON st.customer_id = cl.phone_number
        LEFT JOIN TELCO_NETWORK_OPTIMIZATION_PROD.RAW.CELL_TOWER ct 
            ON st.cell_id = ct.cell_id
    )
    SELECT * FROM service_metrics
    """
    df = session.sql(query).to_pandas()
    df.columns = df.columns.str.lower()
    return df

@st.cache_data(ttl=600)
def load_network_performance_by_service():
    """Load network performance metrics by service type"""
    query = """
    SELECT 
        st.service_type,
        ct.cell_id,
        COUNT(*) as total_calls,
        SUM(CASE WHEN ct.call_release_code = 0 THEN 1 ELSE 0 END) as successful_calls,
        ROUND(AVG(CASE WHEN ct.call_release_code != 0 THEN 1 ELSE 0 END) * 100, 2) as failure_rate,
        ROUND(ct.cell_latitude, 4) AS latitude,
        ROUND(ct.cell_longitude, 4) AS longitude,
        COUNT(DISTINCT ct.msisdn) as unique_customers
    FROM TELCO_NETWORK_OPTIMIZATION_PROD.RAW.CELL_TOWER ct
    JOIN TELCO_NETWORK_OPTIMIZATION_PROD.RAW.SUPPORT_TICKETS st ON ct.cell_id = st.cell_id
    GROUP BY st.service_type, ct.cell_id, ct.cell_latitude, ct.cell_longitude
    """
    df = session.sql(query).to_pandas()
    df.columns = df.columns.str.lower()
    return df

@st.cache_data(ttl=600)
def load_service_summary_stats():
    """Load summary statistics for all service types"""
    query = """
    SELECT 
        service_type,
        COUNT(*) as total_tickets,
        COUNT(DISTINCT customer_id) as unique_customers,
        COUNT(DISTINCT cell_id) as affected_cells,
        AVG(sentiment_score) as avg_sentiment,
        COUNT(CASE WHEN priority = 'High' THEN 1 END) as high_priority_tickets,
        COUNT(CASE WHEN status = 'Resolved' THEN 1 END) as resolved_tickets
    FROM TELCO_NETWORK_OPTIMIZATION_PROD.RAW.SUPPORT_TICKETS
    GROUP BY service_type
    """
    df = session.sql(query).to_pandas()
    df.columns = df.columns.str.lower()
    return df

# Load all data
with st.spinner("🔄 Loading service type performance data..."):
    service_data = load_service_performance_data()
    network_data = load_network_performance_by_service()
    summary_stats = load_service_summary_stats()

# Page header
st.title("🔄 Service Type Performance Breakdown")
st.markdown("**Comprehensive analysis of network service performance across different service types and customer segments**")

# Sidebar filters
st.sidebar.header("🔧 Analysis Filters")

# Service type filter
service_types = sorted(service_data['service_type'].dropna().unique()) if not service_data.empty else []
selected_services = st.sidebar.multiselect(
    "Select Service Types",
    options=service_types,
    default=service_types
)

# Loyalty tier filter
loyalty_tiers = sorted(service_data['loyalty_status'].dropna().unique()) if not service_data.empty else []
selected_loyalty = st.sidebar.multiselect(
    "Loyalty Tiers",
    options=loyalty_tiers,
    default=loyalty_tiers
)

# Performance threshold
performance_threshold = st.sidebar.slider(
    "Performance Threshold (%)",
    min_value=50,
    max_value=100,
    value=85,
    help="Define what constitutes good performance"
)

# Filter data
filtered_data = service_data[
    (service_data['service_type'].isin(selected_services)) &
    (service_data['loyalty_status'].isin(selected_loyalty))
] if not service_data.empty else pd.DataFrame()

# Executive Summary
st.markdown("## 📊 Service Type Performance Overview")

if not summary_stats.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    total_service_types = len(summary_stats)
    total_tickets = summary_stats['total_tickets'].sum()
    avg_sentiment = summary_stats['avg_sentiment'].mean()
    resolution_rate = (summary_stats['resolved_tickets'].sum() / summary_stats['total_tickets'].sum() * 100)
    
    col1.metric("Service Types", f"{total_service_types}")
    col2.metric("Total Support Tickets", f"{total_tickets:,}")
    col3.metric("Average Sentiment", f"{avg_sentiment:.2f}")
    col4.metric("Resolution Rate", f"{resolution_rate:.1f}%")

# Service Type Performance Matrix
st.markdown("### 🎯 Service Performance Matrix")

if not summary_stats.empty:
    # Calculate performance scores
    summary_stats['resolution_rate'] = (summary_stats['resolved_tickets'] / summary_stats['total_tickets'] * 100).round(1)
    summary_stats['priority_ratio'] = (summary_stats['high_priority_tickets'] / summary_stats['total_tickets'] * 100).round(1)
    
    # Performance classification
    def classify_performance(row):
        if row['avg_sentiment'] >= 0.7 and row['resolution_rate'] >= 90:
            return 'Excellent'
        elif row['avg_sentiment'] >= 0.5 and row['resolution_rate'] >= 80:
            return 'Good'
        elif row['avg_sentiment'] >= 0.3 and row['resolution_rate'] >= 70:
            return 'Fair'
        else:
            return 'Poor'
    
    summary_stats['performance_rating'] = summary_stats.apply(classify_performance, axis=1)
    
    # Create performance matrix visualization
    fig_matrix = px.scatter(
        summary_stats,
        x='resolution_rate',
        y='avg_sentiment',
        size='total_tickets',
        color='performance_rating',
        hover_name='service_type',
        hover_data=['unique_customers', 'high_priority_tickets'],
        title='Service Type Performance Matrix',
        labels={
            'resolution_rate': 'Resolution Rate (%)',
            'avg_sentiment': 'Average Sentiment Score'
        },
        color_discrete_map={
            'Excellent': '#28a745',
            'Good': '#17a2b8', 
            'Fair': '#ffc107',
            'Poor': '#dc3545'
        }
    )
    fig_matrix.add_hline(y=0.5, line_dash="dash", line_color="gray", annotation_text="Sentiment Threshold")
    fig_matrix.add_vline(x=80, line_dash="dash", line_color="gray", annotation_text="Resolution Threshold")
    st.plotly_chart(fig_matrix, use_container_width=True)

# Detailed Service Type Analysis
st.markdown("## 🔍 Detailed Service Type Analysis")

col1, col2 = st.columns(2)

with col1:
    # Support ticket volume by service type
    if not summary_stats.empty:
        fig_volume = px.bar(
            summary_stats.sort_values('total_tickets', ascending=False),
            x='service_type',
            y='total_tickets',
            title='Support Ticket Volume by Service Type',
            color='performance_rating',
            color_discrete_map={
                'Excellent': '#28a745',
                'Good': '#17a2b8', 
                'Fair': '#ffc107',
                'Poor': '#dc3545'
            }
        )
        fig_volume.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_volume, use_container_width=True)

with col2:
    # Average sentiment by service type
    if not summary_stats.empty:
        fig_sentiment = px.bar(
            summary_stats.sort_values('avg_sentiment', ascending=False),
            x='service_type',
            y='avg_sentiment',
            title='Average Customer Sentiment by Service Type',
            color='avg_sentiment',
            color_continuous_scale='RdYlGn'
        )
        fig_sentiment.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_sentiment, use_container_width=True)

# Network Performance Impact
st.markdown("## 📡 Network Performance Impact by Service Type")

if not network_data.empty:
    # Calculate network metrics by service type
    network_summary = network_data.groupby('service_type').agg({
        'total_calls': 'sum',
        'successful_calls': 'sum',
        'failure_rate': 'mean',
        'unique_customers': 'sum',
        'cell_id': 'nunique'
    }).round(2)
    
    network_summary['success_rate'] = ((network_summary['successful_calls'] / network_summary['total_calls']) * 100).round(1)
    network_summary = network_summary.reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Network success rate by service type
        fig_success = px.bar(
            network_summary.sort_values('success_rate', ascending=False),
            x='service_type',
            y='success_rate',
            title='Network Success Rate by Service Type',
            color='success_rate',
            color_continuous_scale='RdYlGn',
            text='success_rate'
        )
        fig_success.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_success.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_success, use_container_width=True)
    
    with col2:
        # Total calls handled by service type
        fig_calls = px.bar(
            network_summary.sort_values('total_calls', ascending=False),
            x='service_type',
            y='total_calls',
            title='Total Network Calls by Service Type',
            color='total_calls',
            color_continuous_scale='Blues'
        )
        fig_calls.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_calls, use_container_width=True)

# Customer Loyalty Impact
st.markdown("## 🏆 Service Type Impact Across Loyalty Tiers")

if not filtered_data.empty and 'loyalty_status' in filtered_data.columns:
    loyalty_service_analysis = filtered_data.groupby(['service_type', 'loyalty_status']).agg({
        'ticket_id': 'count',
        'sentiment_score': 'mean',
        'resolution_hours': 'mean'
    }).reset_index()
    
    loyalty_service_analysis.columns = ['Service Type', 'Loyalty Status', 'Ticket Count', 'Avg Sentiment', 'Avg Resolution Hours']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Service ticket distribution across loyalty tiers
        fig_loyalty = px.bar(
            loyalty_service_analysis,
            x='Service Type',
            y='Ticket Count',
            color='Loyalty Status',
            title='Service Issues Distribution Across Loyalty Tiers',
            barmode='group',
            color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}
        )
        fig_loyalty.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_loyalty, use_container_width=True)
    
    with col2:
        # Sentiment heatmap
        sentiment_pivot = loyalty_service_analysis.pivot(
            index='Service Type', 
            columns='Loyalty Status', 
            values='Avg Sentiment'
        )
        
        fig_heatmap = px.imshow(
            sentiment_pivot,
            title='Customer Sentiment Heatmap: Service Type vs Loyalty Tier',
            color_continuous_scale='RdYlGn',
            aspect='auto'
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)

# Priority Analysis
st.markdown("## ⚠️ Service Type Priority Analysis")

if not filtered_data.empty and 'priority' in filtered_data.columns:
    priority_analysis = filtered_data.groupby(['service_type', 'priority']).size().reset_index(name='count')
    priority_total = filtered_data.groupby('service_type').size().reset_index(name='total')
    priority_analysis = priority_analysis.merge(priority_total, on='service_type')
    priority_analysis['percentage'] = (priority_analysis['count'] / priority_analysis['total'] * 100).round(1)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Priority distribution by service type
        fig_priority = px.bar(
            priority_analysis,
            x='service_type',
            y='count',
            color='priority',
            title='Issue Priority Distribution by Service Type',
            barmode='stack',
            color_discrete_map={'High': '#dc3545', 'Medium': '#ffc107', 'Low': '#28a745'}
        )
        fig_priority.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_priority, use_container_width=True)
    
    with col2:
        # High priority percentage
        high_priority = priority_analysis[priority_analysis['priority'] == 'High']
        if not high_priority.empty:
            fig_high_priority = px.bar(
                high_priority.sort_values('percentage', ascending=False),
                x='service_type',
                y='percentage',
                title='High Priority Issues (% of Total) by Service Type',
                color='percentage',
                color_continuous_scale='Reds',
                text='percentage'
            )
            fig_high_priority.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_high_priority.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_high_priority, use_container_width=True)

# Geographic Analysis
st.markdown("## 🗺️ Geographic Service Performance")

if not network_data.empty and not network_data[['latitude', 'longitude']].isna().all().all():
    # Create geographic performance map
    geo_summary = network_data.groupby(['service_type', 'latitude', 'longitude']).agg({
        'failure_rate': 'mean',
        'unique_customers': 'sum',
        'total_calls': 'sum'
    }).reset_index()
    
    # Select top service type for mapping
    if selected_services:
        top_service = selected_services[0]
        service_geo_data = geo_summary[geo_summary['service_type'] == top_service].head(50)
        
        if not service_geo_data.empty:
            fig_map = px.scatter_mapbox(
                service_geo_data,
                lat='latitude',
                lon='longitude',
                size='unique_customers',
                color='failure_rate',
                hover_name='service_type',
                hover_data=['total_calls', 'unique_customers'],
                color_continuous_scale='RdYlGn_r',
                title=f'Geographic Performance Map: {top_service}',
                mapbox_style='open-street-map',
                zoom=6
            )
            fig_map.update_layout(height=500)
            st.plotly_chart(fig_map, use_container_width=True)

# Service Performance Cards
st.markdown("## 📋 Service Performance Summary Cards")

if not summary_stats.empty:
    # Create performance cards for each service type
    cols_per_row = 3
    rows = (len(summary_stats) + cols_per_row - 1) // cols_per_row
    
    for row in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            service_idx = row * cols_per_row + col_idx
            if service_idx < len(summary_stats):
                service = summary_stats.iloc[service_idx]
                performance_class = service['performance_rating'].lower()
                
                with cols[col_idx]:
                    st.markdown(f"""
                    <div class="service-card performance-{performance_class}">
                        <div class="service-type-header">{service['service_type']}</div>
                        <p><strong>Performance:</strong> {service['performance_rating']}</p>
                        <p><strong>Total Tickets:</strong> {service['total_tickets']:,}</p>
                        <p><strong>Customers Affected:</strong> {service['unique_customers']:,}</p>
                        <p><strong>Resolution Rate:</strong> {service['resolution_rate']:.1f}%</p>
                        <p><strong>Avg Sentiment:</strong> {service['avg_sentiment']:.2f}</p>
                        <p><strong>High Priority:</strong> {service['priority_ratio']:.1f}%</p>
                    </div>
                    """, unsafe_allow_html=True)

# Recommendations Engine
st.markdown("## 🎯 Service Improvement Recommendations")

if not summary_stats.empty:
    # Generate recommendations based on performance
    recommendations = []
    
    for _, service in summary_stats.iterrows():
        service_name = service['service_type']
        
        if service['performance_rating'] == 'Poor':
            recommendations.append({
                'Service': service_name,
                'Priority': 'High',
                'Action': f"🚨 CRITICAL: Immediate intervention required for {service_name}",
                'Details': f"Resolution rate: {service['resolution_rate']:.1f}%, Sentiment: {service['avg_sentiment']:.2f}"
            })
        elif service['performance_rating'] == 'Fair':
            recommendations.append({
                'Service': service_name,
                'Priority': 'Medium', 
                'Action': f"⚠️ MONITOR: Performance improvement needed for {service_name}",
                'Details': f"Focus on customer satisfaction and resolution efficiency"
            })
        elif service['priority_ratio'] > 30:
            recommendations.append({
                'Service': service_name,
                'Priority': 'Medium',
                'Action': f"📈 OPTIMIZE: High priority ticket rate is {service['priority_ratio']:.1f}%",
                'Details': "Implement proactive monitoring and preventive measures"
            })
    
    if recommendations:
        rec_df = pd.DataFrame(recommendations)
        
        # Color code by priority
        def highlight_priority(row):
            if row['Priority'] == 'High':
                return ['background-color: #ffebee'] * len(row)
            elif row['Priority'] == 'Medium':
                return ['background-color: #fff3e0'] * len(row)
            else:
                return ['background-color: #e8f5e8'] * len(row)
        
        styled_rec = rec_df.style.apply(highlight_priority, axis=1)
        st.dataframe(styled_rec, use_container_width=True, hide_index=True)
    else:
        st.success("✅ All services are performing within acceptable parameters!")

# Executive Summary Table
st.markdown("## 📊 Service Type Performance Summary")

if not summary_stats.empty:
    display_summary = summary_stats[['service_type', 'total_tickets', 'unique_customers', 'affected_cells', 
                                   'avg_sentiment', 'resolution_rate', 'priority_ratio', 'performance_rating']].copy()
    display_summary.columns = ['Service Type', 'Total Tickets', 'Customers', 'Affected Cells', 
                              'Avg Sentiment', 'Resolution Rate (%)', 'High Priority (%)', 'Performance']
    
    st.dataframe(display_summary, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.caption(f"🔄 **Service Analysis:** Updated {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} | Data source: Snowflake TELCO_NETWORK_OPTIMIZATION_PROD")
st.caption("📈 **Insights:** Service type performance analysis combining network infrastructure, customer loyalty, and support ticket data")