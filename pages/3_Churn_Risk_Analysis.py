import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import os

# Page configuration
st.set_page_config(
    page_title="Churn Risk Analysis",
    page_icon="⚠️",
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

st.title("⚠️ Churn Risk Analysis")

# Get data
customers_df = data['customers']
services_df = data['services']
billing_df = data['billing']
tickets_df = data['support_tickets']
metrics_df = data['customer_metrics']
nps_df = data['nps_surveys']

# Churn Risk Overview
st.markdown("## 🎯 Churn Risk Overview")

col1, col2, col3, col4 = st.columns(4)

# Calculate risk segments
high_risk = len(metrics_df[metrics_df['churn_risk_score'] >= 70])
medium_risk = len(metrics_df[(metrics_df['churn_risk_score'] >= 40) & (metrics_df['churn_risk_score'] < 70)])
low_risk = len(metrics_df[metrics_df['churn_risk_score'] < 40])
total_customers = len(metrics_df)

col1.metric("High Risk (70%+)", f"{high_risk:,}")
col2.metric("Medium Risk (40-69%)", f"{medium_risk:,}")
col3.metric("Low Risk (<40%)", f"{low_risk:,}")
col4.metric("Total Customers", f"{total_customers:,}")

# Risk distribution chart
st.markdown("## 📊 Risk Distribution")

col1, col2 = st.columns(2)

with col1:
    # Risk level pie chart
    risk_data = pd.DataFrame({
        'Risk Level': ['High Risk', 'Medium Risk', 'Low Risk'],
        'Count': [high_risk, medium_risk, low_risk],
        'Color': ['#FF4B4B', '#FFA500', '#00C851']
    })
    
    fig_risk_pie = px.pie(risk_data, values='Count', names='Risk Level',
                         title='Customer Risk Distribution',
                         color_discrete_map={'High Risk': '#FF4B4B', 'Medium Risk': '#FFA500', 'Low Risk': '#00C851'})
    st.plotly_chart(fig_risk_pie, use_container_width=True)

with col2:
    # Risk score histogram
    fig_hist = px.histogram(metrics_df, x='churn_risk_score', nbins=20,
                           title='Churn Risk Score Distribution',
                           labels={'churn_risk_score': 'Churn Risk Score', 'count': 'Number of Customers'})
    fig_hist.update_traces(marker_color='#1f77b4')
    st.plotly_chart(fig_hist, use_container_width=True)

# High Risk Customers
st.markdown("## 🚨 High Risk Customers (70%+ Risk Score)")

high_risk_customers = metrics_df[metrics_df['churn_risk_score'] >= 70].merge(
    customers_df[['customer_id', 'first_name', 'last_name', 'customer_segment', 'email', 'phone_number']], 
    on='customer_id'
).sort_values('churn_risk_score', ascending=False)

if len(high_risk_customers) > 0:
    # Display top 20 high risk customers
    display_cols = ['first_name', 'last_name', 'customer_segment', 'email', 'phone_number',
                   'churn_risk_score', 'monthly_revenue', 'tenure_months', 'support_tickets_count']
    high_risk_display = high_risk_customers.head(20)[display_cols].copy()
    high_risk_display.columns = ['First Name', 'Last Name', 'Segment', 'Email', 'Phone',
                                'Risk Score', 'Monthly Revenue ($)', 'Tenure (Months)', 'Support Tickets']
    
    st.dataframe(high_risk_display, use_container_width=True)
    
    # Calculate potential revenue at risk
    potential_loss = high_risk_customers['monthly_revenue'].sum() * 12  # Annual revenue
    st.error(f"💰 **Revenue at Risk**: ${potential_loss:,.0f} annually from high-risk customers")
else:
    st.success("🎉 No customers currently in high-risk category!")

# Risk Factors Analysis
st.markdown("## 🔍 Risk Factors Analysis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📞 Support Ticket Impact")
    
    # Group customers by support ticket count
    ticket_groups = metrics_df.copy()
    ticket_groups['ticket_category'] = pd.cut(ticket_groups['support_tickets_count'], 
                                            bins=[-1, 0, 2, 5, float('inf')], 
                                            labels=['No Tickets', '1-2 Tickets', '3-5 Tickets', '6+ Tickets'])
    
    ticket_risk = ticket_groups.groupby('ticket_category')['churn_risk_score'].mean().reset_index()
    
    fig_tickets = px.bar(ticket_risk, x='ticket_category', y='churn_risk_score',
                        title='Avg Churn Risk by Support Ticket Count',
                        labels={'ticket_category': 'Support Tickets', 'churn_risk_score': 'Avg Risk Score'})
    fig_tickets.update_traces(marker_color='#FF6B6B')
    st.plotly_chart(fig_tickets, use_container_width=True)

with col2:
    st.markdown("### 💳 Payment Behavior Impact")
    
    # Analyze payment issues
    customer_payment_issues = billing_df.groupby('customer_id').agg({
        'payment_status': lambda x: (x.isin(['Late', 'Unpaid'])).sum()
    }).reset_index()
    customer_payment_issues.columns = ['customer_id', 'payment_issues']
    
    payment_risk = metrics_df.merge(customer_payment_issues, on='customer_id')
    payment_risk['payment_category'] = pd.cut(payment_risk['payment_issues'], 
                                            bins=[-1, 0, 2, 5, float('inf')], 
                                            labels=['No Issues', '1-2 Issues', '3-5 Issues', '6+ Issues'])
    
    payment_risk_summary = payment_risk.groupby('payment_category')['churn_risk_score'].mean().reset_index()
    
    fig_payment = px.bar(payment_risk_summary, x='payment_category', y='churn_risk_score',
                        title='Avg Churn Risk by Payment Issues',
                        labels={'payment_category': 'Payment Issues', 'churn_risk_score': 'Avg Risk Score'})
    fig_payment.update_traces(marker_color='#FFA500')
    st.plotly_chart(fig_payment, use_container_width=True)

# Customer Satisfaction Impact
st.markdown("### 😊 Customer Satisfaction Impact")

col1, col2 = st.columns(2)

with col1:
    # NPS impact
    nps_risk = metrics_df[metrics_df['latest_nps_score'].notna()].copy()
    nps_risk['nps_category'] = pd.cut(nps_risk['latest_nps_score'], 
                                    bins=[-1, 6, 8, 10], 
                                    labels=['Detractor (0-6)', 'Passive (7-8)', 'Promoter (9-10)'])
    
    if len(nps_risk) > 0:
        nps_risk_summary = nps_risk.groupby('nps_category')['churn_risk_score'].mean().reset_index()
        
        fig_nps = px.bar(nps_risk_summary, x='nps_category', y='churn_risk_score',
                        title='Avg Churn Risk by NPS Category',
                        labels={'nps_category': 'NPS Category', 'churn_risk_score': 'Avg Risk Score'})
        fig_nps.update_traces(marker_color='#17A2B8')
        st.plotly_chart(fig_nps, use_container_width=True)
    else:
        st.info("No NPS data available for analysis.")

with col2:
    # Support satisfaction impact
    satisfaction_risk = metrics_df.copy()
    satisfaction_risk['satisfaction_category'] = pd.cut(satisfaction_risk['avg_satisfaction_rating'], 
                                                      bins=[0, 3, 4, 5], 
                                                      labels=['Low (1-3)', 'Medium (3-4)', 'High (4-5)'])
    
    satisfaction_risk_summary = satisfaction_risk.groupby('satisfaction_category')['churn_risk_score'].mean().reset_index()
    
    fig_satisfaction = px.bar(satisfaction_risk_summary, x='satisfaction_category', y='churn_risk_score',
                            title='Avg Churn Risk by Support Satisfaction',
                            labels={'satisfaction_category': 'Satisfaction Level', 'churn_risk_score': 'Avg Risk Score'})
    fig_satisfaction.update_traces(marker_color='#28A745')
    st.plotly_chart(fig_satisfaction, use_container_width=True)

# Risk by Customer Segment
st.markdown("## 👥 Risk by Customer Segment")

segment_risk = metrics_df.merge(customers_df[['customer_id', 'customer_segment']], on='customer_id')
segment_summary = segment_risk.groupby('customer_segment').agg({
    'churn_risk_score': ['mean', 'count'],
    'monthly_revenue': 'sum'
}).round(2)

segment_summary.columns = ['Avg Risk Score', 'Customer Count', 'Total Monthly Revenue']
segment_summary = segment_summary.reset_index()

col1, col2 = st.columns(2)

with col1:
    fig_segment_risk = px.bar(segment_summary, x='customer_segment', y='Avg Risk Score',
                             title='Average Risk Score by Segment',
                             labels={'customer_segment': 'Segment', 'Avg Risk Score': 'Risk Score'})
    st.plotly_chart(fig_segment_risk, use_container_width=True)

with col2:
    # Risk vs Revenue scatter
    fig_scatter = px.scatter(segment_risk, x='monthly_revenue', y='churn_risk_score', 
                           color='customer_segment',
                           title='Risk Score vs Monthly Revenue',
                           labels={'monthly_revenue': 'Monthly Revenue ($)', 'churn_risk_score': 'Risk Score'})
    st.plotly_chart(fig_scatter, use_container_width=True)

# Retention Action Plan
st.markdown("## 🎯 Retention Action Plan")

# Categorize customers for different retention strategies
action_plan = metrics_df.merge(customers_df[['customer_id', 'first_name', 'last_name', 'customer_segment']], on='customer_id')

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🚨 Immediate Action Required")
    immediate_action = action_plan[
        (action_plan['churn_risk_score'] >= 70) & 
        (action_plan['monthly_revenue'] >= action_plan['monthly_revenue'].median())
    ].nlargest(10, 'monthly_revenue')
    
    if len(immediate_action) > 0:
        immediate_display = immediate_action[['first_name', 'last_name', 'customer_segment', 
                                           'monthly_revenue', 'churn_risk_score']].copy()
        immediate_display.columns = ['First Name', 'Last Name', 'Segment', 'Monthly Revenue ($)', 'Risk Score']
        st.dataframe(immediate_display, use_container_width=True)
        
        st.markdown("**Recommended Actions:**")
        st.markdown("- 📞 Priority retention call within 24 hours")
        st.markdown("- 🎁 Offer retention incentives or discounts")
        st.markdown("- 🔧 Address any outstanding technical issues")
        st.markdown("- 📋 Schedule account review meeting")
    else:
        st.info("No high-value customers requiring immediate action.")

with col2:
    st.markdown("### ⚠️ Proactive Outreach")
    proactive_outreach = action_plan[
        (action_plan['churn_risk_score'] >= 40) & 
        (action_plan['churn_risk_score'] < 70)
    ].nlargest(10, 'monthly_revenue')
    
    if len(proactive_outreach) > 0:
        proactive_display = proactive_outreach[['first_name', 'last_name', 'customer_segment', 
                                              'monthly_revenue', 'churn_risk_score']].copy()
        proactive_display.columns = ['First Name', 'Last Name', 'Segment', 'Monthly Revenue ($)', 'Risk Score']
        st.dataframe(proactive_display, use_container_width=True)
        
        st.markdown("**Recommended Actions:**")
        st.markdown("- 📧 Send satisfaction survey")
        st.markdown("- 🎯 Offer service upgrades or add-ons")
        st.markdown("- 💬 Check in via preferred communication channel")
        st.markdown("- 🏆 Highlight loyalty benefits and rewards")
    else:
        st.info("No customers requiring proactive outreach.")

# Risk Mitigation ROI
st.markdown("## 💰 Risk Mitigation ROI")

col1, col2, col3 = st.columns(3)

# Calculate potential savings
high_risk_revenue = high_risk_customers['monthly_revenue'].sum() if len(high_risk_customers) > 0 else 0
medium_risk_revenue = metrics_df[
    (metrics_df['churn_risk_score'] >= 40) & 
    (metrics_df['churn_risk_score'] < 70)
]['monthly_revenue'].sum()

# Assume 30% of high risk and 10% of medium risk will churn without intervention
potential_monthly_loss = (high_risk_revenue * 0.3) + (medium_risk_revenue * 0.1)
potential_annual_loss = potential_monthly_loss * 12

# Assume retention program can reduce churn by 50%
potential_savings = potential_annual_loss * 0.5

col1.metric("Potential Monthly Loss", f"${potential_monthly_loss:,.0f}")
col2.metric("Potential Annual Loss", f"${potential_annual_loss:,.0f}")
col3.metric("Retention Program Savings", f"${potential_savings:,.0f}")

st.markdown("---")
st.markdown("💡 **Key Insights**: Focus retention efforts on high-value customers with multiple risk factors. Proactive engagement can significantly reduce churn and protect revenue.")