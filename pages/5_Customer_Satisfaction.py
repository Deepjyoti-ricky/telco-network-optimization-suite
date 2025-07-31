import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import os

# Page configuration
st.set_page_config(
    page_title="Customer Satisfaction",
    page_icon="😊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data function
@st.cache_data
def load_data():
    """Load all customer data from CSV files"""
    data_dir = "data"
    data = {}
    
    try:
        for file in os.listdir(data_dir):
            if file.endswith('.csv'):
                table_name = file.replace('.csv', '')
                data[table_name] = pd.read_csv(f"{data_dir}/{file}")
        return data
    except FileNotFoundError:
        st.error("Data files not found. Please run data_generator.py first.")
        return None

# Load the data
data = load_data()
if data is None:
    st.stop()

st.title("😊 Customer Satisfaction Analysis")

# Get data
customers_df = data['customers']
services_df = data['services']
tickets_df = data['support_tickets']
metrics_df = data['customer_metrics']
nps_df = data['nps_surveys']

# Customer Satisfaction Overview
st.markdown("## 📊 Satisfaction Overview")

col1, col2, col3, col4 = st.columns(4)

# Calculate key satisfaction metrics
avg_satisfaction = metrics_df['avg_satisfaction_rating'].mean()
nps_responses = len(nps_df)
avg_nps = nps_df['nps_score'].mean() if len(nps_df) > 0 else 0
total_tickets = len(tickets_df)

col1.metric("Avg Support Satisfaction", f"{avg_satisfaction:.1f}/5")
col2.metric("NPS Responses", f"{nps_responses:,}")
col3.metric("Average NPS Score", f"{avg_nps:.1f}/10")
col4.metric("Total Support Tickets", f"{total_tickets:,}")

# NPS Analysis
st.markdown("## 📈 Net Promoter Score (NPS) Analysis")

if len(nps_df) > 0:
    col1, col2 = st.columns(2)
    
    with col1:
        # NPS distribution
        nps_categories = nps_df['category'].value_counts()
        colors = {'Promoter': '#00C851', 'Passive': '#FFA500', 'Detractor': '#FF4B4B'}
        
        fig_nps_dist = px.pie(values=nps_categories.values, names=nps_categories.index,
                             title='NPS Score Distribution',
                             color_discrete_map=colors)
        st.plotly_chart(fig_nps_dist, use_container_width=True)
        
        # Calculate NPS score
        promoters = len(nps_df[nps_df['category'] == 'Promoter'])
        detractors = len(nps_df[nps_df['category'] == 'Detractor'])
        total_responses = len(nps_df)
        
        nps_score = ((promoters - detractors) / total_responses) * 100
        
        if nps_score >= 50:
            color = "success"
            interpretation = "Excellent"
        elif nps_score >= 0:
            color = "normal"
            interpretation = "Good"
        else:
            color = "error"
            interpretation = "Needs Improvement"
            
        st.metric("Net Promoter Score", f"{nps_score:.1f}", help=f"Interpretation: {interpretation}")
    
    with col2:
        # NPS trend over time
        nps_df_trend = nps_df.copy()
        nps_df_trend['survey_date'] = pd.to_datetime(nps_df_trend['survey_date'])
        nps_df_trend['month'] = nps_df_trend['survey_date'].dt.to_period('M')
        
        monthly_nps = nps_df_trend.groupby('month')['nps_score'].mean().reset_index()
        monthly_nps['month'] = monthly_nps['month'].dt.to_timestamp()
        
        fig_nps_trend = px.line(monthly_nps, x='month', y='nps_score',
                               title='NPS Trend Over Time',
                               labels={'nps_score': 'Average NPS Score', 'month': 'Month'})
        fig_nps_trend.add_hline(y=9, line_dash="dash", line_color="green", annotation_text="Promoter Threshold")
        fig_nps_trend.add_hline(y=7, line_dash="dash", line_color="orange", annotation_text="Passive Threshold")
        st.plotly_chart(fig_nps_trend, use_container_width=True)
    
    # NPS by Customer Segment
    st.markdown("### 👥 NPS by Customer Segment")
    
    nps_segment = nps_df.merge(customers_df[['customer_id', 'customer_segment']], on='customer_id')
    segment_nps = nps_segment.groupby('customer_segment').agg({
        'nps_score': ['mean', 'count'],
        'category': lambda x: (x == 'Promoter').sum()
    }).round(2)
    
    segment_nps.columns = ['Avg NPS Score', 'Response Count', 'Promoter Count']
    segment_nps = segment_nps.reset_index()
    segment_nps['Promoter Rate %'] = (segment_nps['Promoter Count'] / segment_nps['Response Count'] * 100).round(1)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_segment_nps = px.bar(segment_nps, x='customer_segment', y='Avg NPS Score',
                                title='Average NPS Score by Segment',
                                labels={'customer_segment': 'Segment', 'Avg NPS Score': 'NPS Score'})
        st.plotly_chart(fig_segment_nps, use_container_width=True)
    
    with col2:
        st.markdown("#### 📋 Segment NPS Summary")
        st.dataframe(segment_nps, use_container_width=True)

else:
    st.info("No NPS survey data available.")

# Support Ticket Satisfaction
st.markdown("## 🎫 Support Ticket Satisfaction")

col1, col2 = st.columns(2)

with col1:
    # Satisfaction rating distribution
    satisfaction_counts = tickets_df['satisfaction_rating'].value_counts().sort_index()
    
    fig_satisfaction = px.bar(x=satisfaction_counts.index, y=satisfaction_counts.values,
                             title='Support Satisfaction Rating Distribution',
                             labels={'x': 'Satisfaction Rating (1-5)', 'y': 'Number of Tickets'})
    fig_satisfaction.update_traces(marker_color='#17A2B8')
    st.plotly_chart(fig_satisfaction, use_container_width=True)

with col2:
    # Satisfaction by issue type
    issue_satisfaction = tickets_df.groupby('issue_type')['satisfaction_rating'].mean().reset_index()
    
    fig_issue_sat = px.bar(issue_satisfaction, x='issue_type', y='satisfaction_rating',
                          title='Average Satisfaction by Issue Type',
                          labels={'issue_type': 'Issue Type', 'satisfaction_rating': 'Avg Satisfaction'})
    fig_issue_sat.update_traces(marker_color='#28A745')
    st.plotly_chart(fig_issue_sat, use_container_width=True)

# Resolution Time vs Satisfaction
st.markdown("### ⏱️ Resolution Time Impact on Satisfaction")

col1, col2 = st.columns(2)

with col1:
    # Scatter plot of resolution time vs satisfaction
    fig_scatter = px.scatter(tickets_df, x='resolution_time_hours', y='satisfaction_rating',
                           title='Resolution Time vs Satisfaction Rating',
                           labels={'resolution_time_hours': 'Resolution Time (Hours)', 
                                  'satisfaction_rating': 'Satisfaction Rating'})
    st.plotly_chart(fig_scatter, use_container_width=True)

with col2:
    # Resolution time categories vs satisfaction
    tickets_df['resolution_category'] = pd.cut(tickets_df['resolution_time_hours'], 
                                             bins=[0, 4, 24, 72, float('inf')], 
                                             labels=['<4 hours', '4-24 hours', '1-3 days', '>3 days'])
    
    resolution_satisfaction = tickets_df.groupby('resolution_category')['satisfaction_rating'].mean().reset_index()
    
    fig_resolution = px.bar(resolution_satisfaction, x='resolution_category', y='satisfaction_rating',
                           title='Satisfaction by Resolution Time Category',
                           labels={'resolution_category': 'Resolution Time', 'satisfaction_rating': 'Avg Satisfaction'})
    st.plotly_chart(fig_resolution, use_container_width=True)

# Customer Satisfaction Segments
st.markdown("## 🎯 Customer Satisfaction Segments")

# Merge satisfaction data with customer metrics
satisfaction_segments = metrics_df.merge(
    customers_df[['customer_id', 'customer_segment']], on='customer_id'
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 😢 Low Satisfaction Customers")
    
    low_satisfaction = satisfaction_segments[satisfaction_segments['avg_satisfaction_rating'] < 3]
    
    if len(low_satisfaction) > 0:
        low_sat_display = low_satisfaction.merge(
            customers_df[['customer_id', 'first_name', 'last_name']], on='customer_id'
        )[['first_name', 'last_name', 'customer_segment', 'avg_satisfaction_rating', 
           'support_tickets_count', 'monthly_revenue']].copy()
        
        low_sat_display.columns = ['First Name', 'Last Name', 'Segment', 'Avg Satisfaction', 
                                  'Ticket Count', 'Monthly Revenue ($)']
        
        st.dataframe(low_sat_display.head(10), use_container_width=True)
        
        # Impact analysis
        revenue_at_risk = low_satisfaction['monthly_revenue'].sum()
        st.error(f"💰 **Revenue at Risk**: ${revenue_at_risk:,.0f}/month from {len(low_satisfaction)} dissatisfied customers")
    else:
        st.success("🎉 No customers with low satisfaction ratings!")

with col2:
    st.markdown("### 🌟 High Satisfaction Customers")
    
    high_satisfaction = satisfaction_segments[satisfaction_segments['avg_satisfaction_rating'] >= 4.5]
    
    if len(high_satisfaction) > 0:
        high_sat_display = high_satisfaction.merge(
            customers_df[['customer_id', 'first_name', 'last_name']], on='customer_id'
        )[['first_name', 'last_name', 'customer_segment', 'avg_satisfaction_rating', 
           'monthly_revenue', 'upsell_score']].copy()
        
        high_sat_display.columns = ['First Name', 'Last Name', 'Segment', 'Avg Satisfaction', 
                                   'Monthly Revenue ($)', 'Upsell Score']
        
        st.dataframe(high_sat_display.head(10), use_container_width=True)
        
        # Opportunity analysis
        upsell_opportunities = len(high_satisfaction[high_satisfaction['upsell_score'] >= 60])
        st.success(f"🎯 **Upsell Opportunities**: {upsell_opportunities} highly satisfied customers ready for upselling")
    else:
        st.info("No customers with high satisfaction ratings identified.")

# Satisfaction Drivers Analysis
st.markdown("## 🔍 Satisfaction Drivers Analysis")

# Correlation analysis
correlation_data = metrics_df[['avg_satisfaction_rating', 'avg_resolution_time_hours', 
                              'support_tickets_count', 'tenure_months', 'active_services']].corr()

col1, col2 = st.columns(2)

with col1:
    # Correlation heatmap
    fig_corr = px.imshow(correlation_data, 
                        title='Satisfaction Correlation Matrix',
                        labels=dict(color="Correlation"),
                        color_continuous_scale='RdBu_r')
    st.plotly_chart(fig_corr, use_container_width=True)

with col2:
    # Key insights
    st.markdown("### 💡 Key Insights")
    
    # Calculate key correlations
    resolution_corr = correlation_data.loc['avg_satisfaction_rating', 'avg_resolution_time_hours']
    tickets_corr = correlation_data.loc['avg_satisfaction_rating', 'support_tickets_count']
    tenure_corr = correlation_data.loc['avg_satisfaction_rating', 'tenure_months']
    
    insights = []
    
    if resolution_corr < -0.3:
        insights.append("📉 **Strong negative correlation** between resolution time and satisfaction")
    elif resolution_corr < -0.1:
        insights.append("📊 **Moderate negative correlation** between resolution time and satisfaction")
    
    if tickets_corr < -0.3:
        insights.append("🎫 **Multiple support tickets** strongly impact satisfaction")
    elif tickets_corr < -0.1:
        insights.append("🎫 **Support ticket frequency** moderately impacts satisfaction")
    
    if tenure_corr > 0.1:
        insights.append("⏳ **Longer tenure** customers tend to be more satisfied")
    
    for insight in insights:
        st.markdown(insight)
    
    if not insights:
        st.markdown("📊 No strong correlations identified in current data")

# Feedback Analysis
if len(nps_df[nps_df['feedback'].notna()]) > 0:
    st.markdown("## 💬 Customer Feedback Analysis")
    
    # Show recent feedback
    recent_feedback = nps_df[nps_df['feedback'].notna()].sort_values('survey_date', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 😊 Positive Feedback (Promoters)")
        promoter_feedback = recent_feedback[recent_feedback['category'] == 'Promoter'].head(5)
        
        for _, feedback in promoter_feedback.iterrows():
            st.write(f"**{feedback['nps_score']}/10** - *\"{feedback['feedback']}\"*")
    
    with col2:
        st.markdown("### 😟 Critical Feedback (Detractors)")
        detractor_feedback = recent_feedback[recent_feedback['category'] == 'Detractor'].head(5)
        
        for _, feedback in detractor_feedback.iterrows():
            st.write(f"**{feedback['nps_score']}/10** - *\"{feedback['feedback']}\"*")

# Action Plan
st.markdown("## ⚡ Satisfaction Improvement Action Plan")

action_items = []

# Low satisfaction customers
low_sat_count = len(satisfaction_segments[satisfaction_segments['avg_satisfaction_rating'] < 3])
if low_sat_count > 0:
    action_items.append(f"🚨 **Immediate**: Follow up with {low_sat_count} customers with low satisfaction scores")

# Long resolution times
long_resolution = len(tickets_df[tickets_df['resolution_time_hours'] > 48])
if long_resolution > 0:
    action_items.append(f"⏱️ **Process**: Review {long_resolution} cases with >48hr resolution time")

# Frequent support contacts
frequent_tickets = len(metrics_df[metrics_df['support_tickets_count'] > 3])
if frequent_tickets > 0:
    action_items.append(f"🎫 **Proactive**: Identify root causes for {frequent_tickets} customers with 4+ tickets")

# NPS detractors
if len(nps_df) > 0:
    detractor_count = len(nps_df[nps_df['category'] == 'Detractor'])
    if detractor_count > 0:
        action_items.append(f"😟 **Retention**: Develop retention plan for {detractor_count} NPS detractors")

# General improvements
action_items.append("📈 **Training**: Implement satisfaction-focused training for support team")
action_items.append("📊 **Monitoring**: Set up real-time satisfaction monitoring dashboard")

for i, item in enumerate(action_items, 1):
    st.markdown(f"{i}. {item}")

# Satisfaction Goals
st.markdown("## 🎯 Satisfaction Goals & Targets")

col1, col2, col3 = st.columns(3)

current_nps = nps_score if len(nps_df) > 0 else 0
target_nps = current_nps + 10

current_support_sat = avg_satisfaction
target_support_sat = min(5.0, current_support_sat + 0.5)

col1.metric(
    "Current NPS", 
    f"{current_nps:.1f}", 
    f"Target: {target_nps:.1f}"
)

col2.metric(
    "Current Support Satisfaction", 
    f"{current_support_sat:.1f}/5", 
    f"Target: {target_support_sat:.1f}/5"
)

resolution_time_target = tickets_df['resolution_time_hours'].median() * 0.8
col3.metric(
    "Target Resolution Time", 
    f"{resolution_time_target:.1f} hrs",
    "20% improvement"
)

st.markdown("---")
st.markdown("💡 **Strategy**: Focus on reducing resolution times and proactive outreach to at-risk customers to drive satisfaction improvements.")