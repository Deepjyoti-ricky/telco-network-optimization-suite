import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import os

# Page configuration
st.set_page_config(
    page_title="Sales Opportunities",
    page_icon="🎯",
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

st.title("🎯 Sales Opportunities")

# Get data
customers_df = data['customers']
services_df = data['services']
billing_df = data['billing']
metrics_df = data['customer_metrics']
plans_df = data['plans']
tickets_df = data['support_tickets']
nps_df = data['nps_surveys']

# Sales Opportunity Overview
st.markdown("## 📊 Sales Opportunity Overview")

col1, col2, col3, col4 = st.columns(4)

# Calculate opportunity metrics
high_upsell = len(metrics_df[metrics_df['upsell_score'] >= 70])
cross_sell_opportunities = len(metrics_df[metrics_df['active_services'] == 1])
avg_upsell_score = metrics_df['upsell_score'].mean()
total_opportunity_value = metrics_df[metrics_df['upsell_score'] >= 50]['monthly_revenue'].sum() * 0.3  # 30% potential uplift

col1.metric("High Upsell Potential", f"{high_upsell:,}")
col2.metric("Cross-sell Prospects", f"{cross_sell_opportunities:,}")
col3.metric("Avg Upsell Score", f"{avg_upsell_score:.1f}")
col4.metric("Opportunity Value/Month", f"${total_opportunity_value:,.0f}")

# Upselling Opportunities
st.markdown("## ⬆️ Upselling Opportunities")

upsell_customers = metrics_df[metrics_df['upsell_score'] >= 60].merge(
    customers_df[['customer_id', 'first_name', 'last_name', 'customer_segment', 'email', 'phone_number']], 
    on='customer_id'
).sort_values('upsell_score', ascending=False)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🌟 Top Upselling Prospects")
    if len(upsell_customers) > 0:
        top_upsell = upsell_customers.head(15)
        
        display_cols = ['first_name', 'last_name', 'customer_segment', 'monthly_revenue', 
                       'upsell_score', 'active_services', 'tenure_months']
        upsell_display = top_upsell[display_cols].copy()
        upsell_display.columns = ['First Name', 'Last Name', 'Segment', 'Current Revenue ($)', 
                                'Upsell Score', 'Services', 'Tenure (Months)']
        
        st.dataframe(upsell_display, use_container_width=True)
        
        potential_upsell_revenue = len(top_upsell) * 25  # Estimated $25 additional monthly revenue per customer
        st.success(f"💰 **Potential Monthly Uplift**: ${potential_upsell_revenue:,.0f}")
    else:
        st.info("No high-potential upselling opportunities identified.")

with col2:
    st.markdown("### 📈 Upsell Score Distribution")
    
    fig_upsell_dist = px.histogram(metrics_df, x='upsell_score', nbins=20,
                                  title='Upsell Score Distribution',
                                  labels={'upsell_score': 'Upsell Score', 'count': 'Number of Customers'})
    fig_upsell_dist.update_traces(marker_color='#28A745')
    st.plotly_chart(fig_upsell_dist, use_container_width=True)

# Cross-selling Opportunities
st.markdown("## 🔄 Cross-selling Opportunities")

# Identify customers with single services
single_service_customers = metrics_df[metrics_df['active_services'] == 1].merge(
    customers_df[['customer_id', 'first_name', 'last_name', 'customer_segment']], 
    on='customer_id'
)

# Get their current service types
customer_current_services = single_service_customers.merge(
    services_df[services_df['service_status'] == 'Active'][['customer_id', 'service_type']], 
    on='customer_id'
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📱 Service Gap Analysis")
    
    # Count customers by their current single service
    service_gaps = customer_current_services['service_type'].value_counts()
    
    fig_gaps = px.bar(x=service_gaps.index, y=service_gaps.values,
                     title='Customers with Single Service by Type',
                     labels={'x': 'Current Service Type', 'y': 'Number of Customers'})
    fig_gaps.update_traces(marker_color='#17A2B8')
    st.plotly_chart(fig_gaps, use_container_width=True)

with col2:
    st.markdown("### 🎯 Cross-sell Recommendations")
    
    # Suggest complementary services
    cross_sell_recommendations = []
    
    mobile_only = len(customer_current_services[customer_current_services['service_type'] == 'Mobile'])
    internet_only = len(customer_current_services[customer_current_services['service_type'] == 'Internet'])
    tv_only = len(customer_current_services[customer_current_services['service_type'] == 'TV'])
    
    if mobile_only > 0:
        cross_sell_recommendations.append(f"📱➕🌐 {mobile_only} Mobile-only customers → Add Internet")
        cross_sell_recommendations.append(f"📱➕📺 {mobile_only} Mobile-only customers → Add TV")
    
    if internet_only > 0:
        cross_sell_recommendations.append(f"🌐➕📱 {internet_only} Internet-only customers → Add Mobile")
        cross_sell_recommendations.append(f"🌐➕📺 {internet_only} Internet-only customers → Add TV")
    
    if tv_only > 0:
        cross_sell_recommendations.append(f"📺➕📱 {tv_only} TV-only customers → Add Mobile")
        cross_sell_recommendations.append(f"📺➕🌐 {tv_only} TV-only customers → Add Internet")
    
    for recommendation in cross_sell_recommendations:
        st.write(f"• {recommendation}")
    
    # Potential cross-sell revenue
    avg_service_revenue = services_df[services_df['service_status'] == 'Active']['monthly_fee'].mean()
    potential_cross_sell = len(single_service_customers) * avg_service_revenue
    st.metric("Potential Cross-sell Revenue", f"${potential_cross_sell:,.0f}/month")

# Premium Upgrade Opportunities
st.markdown("## ⭐ Premium Upgrade Opportunities")

# Find customers with basic plans
basic_plan_customers = services_df[
    (services_df['service_status'] == 'Active') & 
    (services_df['plan_name'].str.contains('Basic', na=False))
]['customer_id'].unique()

upgrade_opportunities = metrics_df[
    metrics_df['customer_id'].isin(basic_plan_customers) & 
    (metrics_df['upsell_score'] >= 50)
].merge(customers_df[['customer_id', 'first_name', 'last_name', 'customer_segment']], on='customer_id')

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 Basic Plan Upgrade Prospects")
    
    if len(upgrade_opportunities) > 0:
        top_upgrades = upgrade_opportunities.nlargest(10, 'upsell_score')
        
        # Get their current basic plans
        upgrade_plans = top_upgrades.merge(
            services_df[services_df['plan_name'].str.contains('Basic', na=False)][
                ['customer_id', 'plan_name', 'monthly_fee']
            ], on='customer_id'
        )
        
        display_cols = ['first_name', 'last_name', 'plan_name', 'monthly_fee', 'upsell_score']
        upgrade_display = upgrade_plans[display_cols].copy()
        upgrade_display.columns = ['First Name', 'Last Name', 'Current Plan', 'Current Fee ($)', 'Upsell Score']
        
        st.dataframe(upgrade_display, use_container_width=True)
    else:
        st.info("No basic plan customers identified for upgrades.")

with col2:
    st.markdown("### 💰 Upgrade Revenue Potential")
    
    if len(upgrade_opportunities) > 0:
        # Calculate potential upgrade value
        basic_plans = plans_df[plans_df['plan_name'].str.contains('Basic')]
        premium_plans = plans_df[~plans_df['plan_name'].str.contains('Basic')]
        
        avg_basic_fee = basic_plans['monthly_fee'].mean()
        avg_premium_fee = premium_plans['monthly_fee'].mean()
        upgrade_difference = avg_premium_fee - avg_basic_fee
        
        st.metric("Avg Basic Plan Fee", f"${avg_basic_fee:.2f}")
        st.metric("Avg Premium Plan Fee", f"${avg_premium_fee:.2f}")
        st.metric("Avg Upgrade Value", f"${upgrade_difference:.2f}/month")
        
        total_upgrade_potential = len(upgrade_opportunities) * upgrade_difference
        st.success(f"**Total Upgrade Potential**: ${total_upgrade_potential:,.0f}/month")
    else:
        st.info("No upgrade potential calculated.")

# Customer Segment Opportunities
st.markdown("## 👥 Opportunities by Customer Segment")

segment_opportunities = metrics_df.merge(
    customers_df[['customer_id', 'customer_segment']], 
    on='customer_id'
)

segment_summary = segment_opportunities.groupby('customer_segment').agg({
    'upsell_score': 'mean',
    'monthly_revenue': ['mean', 'sum'],
    'active_services': 'mean',
    'customer_id': 'count'
}).round(2)

segment_summary.columns = ['Avg Upsell Score', 'Avg Monthly Revenue', 'Total Revenue', 'Avg Services', 'Customer Count']
segment_summary = segment_summary.reset_index()

col1, col2 = st.columns(2)

with col1:
    fig_segment_upsell = px.bar(segment_summary, x='customer_segment', y='Avg Upsell Score',
                               title='Average Upsell Score by Segment',
                               labels={'customer_segment': 'Segment', 'Avg Upsell Score': 'Upsell Score'})
    fig_segment_upsell.update_traces(marker_color='#FF6B6B')
    st.plotly_chart(fig_segment_upsell, use_container_width=True)

with col2:
    st.markdown("### 📋 Segment Opportunity Summary")
    st.dataframe(segment_summary, use_container_width=True)

# Targeted Sales Campaigns
st.markdown("## 📢 Targeted Sales Campaign Recommendations")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎯 Campaign 1: Mobile Bundle Push")
    mobile_only_high_value = customer_current_services[
        (customer_current_services['service_type'] == 'Mobile') & 
        (customer_current_services['customer_id'].isin(
            metrics_df[metrics_df['monthly_revenue'] > metrics_df['monthly_revenue'].median()]['customer_id']
        ))
    ]
    
    st.write(f"**Target Audience**: {len(mobile_only_high_value)} high-value mobile-only customers")
    st.write("**Offer**: Internet + TV bundle with 20% discount for first 6 months")
    st.write("**Expected Conversion**: 15-25%")
    
    potential_mobile_bundle = len(mobile_only_high_value) * 0.2 * 75  # 20% conversion at $75/month
    st.metric("Potential Monthly Revenue", f"${potential_mobile_bundle:,.0f}")

with col2:
    st.markdown("### 🎯 Campaign 2: Premium Upgrade Drive")
    basic_high_satisfaction = upgrade_opportunities[
        upgrade_opportunities['customer_id'].isin(
            metrics_df[metrics_df['avg_satisfaction_rating'] >= 4]['customer_id']
        )
    ]
    
    st.write(f"**Target Audience**: {len(basic_high_satisfaction)} satisfied customers with basic plans")
    st.write("**Offer**: Premium plan upgrade with 1 month free")
    st.write("**Expected Conversion**: 25-35%")
    
    potential_premium_upgrade = len(basic_high_satisfaction) * 0.3 * 25  # 30% conversion at $25 uplift
    st.metric("Potential Monthly Revenue", f"${potential_premium_upgrade:,.0f}")

# Sales Prioritization Matrix
st.markdown("## 📊 Sales Prioritization Matrix")

# Create priority matrix based on revenue potential and likelihood
priority_customers = metrics_df.merge(
    customers_df[['customer_id', 'first_name', 'last_name', 'customer_segment']], 
    on='customer_id'
)

# Calculate priority score: (upsell_score * monthly_revenue potential)
priority_customers['priority_score'] = (
    priority_customers['upsell_score'] * 
    (priority_customers['monthly_revenue'] + 25) / 100  # Normalized priority
)

# Categorize priorities
priority_customers['priority_level'] = pd.cut(
    priority_customers['priority_score'], 
    bins=[0, 20, 40, float('inf')], 
    labels=['Low Priority', 'Medium Priority', 'High Priority']
)

col1, col2 = st.columns(2)

with col1:
    # Priority distribution
    priority_counts = priority_customers['priority_level'].value_counts()
    fig_priority = px.pie(values=priority_counts.values, names=priority_counts.index,
                         title='Sales Priority Distribution',
                         color_discrete_map={'High Priority': '#FF4B4B', 'Medium Priority': '#FFA500', 'Low Priority': '#00C851'})
    st.plotly_chart(fig_priority, use_container_width=True)

with col2:
    # High priority customers
    st.markdown("### 🚀 High Priority Prospects")
    high_priority = priority_customers[priority_customers['priority_level'] == 'High Priority'].nlargest(10, 'priority_score')
    
    if len(high_priority) > 0:
        priority_display = high_priority[['first_name', 'last_name', 'customer_segment', 
                                        'monthly_revenue', 'upsell_score']].copy()
        priority_display.columns = ['First Name', 'Last Name', 'Segment', 'Revenue ($)', 'Upsell Score']
        st.dataframe(priority_display, use_container_width=True)
    else:
        st.info("No high priority prospects identified.")

# Action Items for Sales Team
st.markdown("## ⚡ Sales Action Items")

action_items = []

# High-value upsell opportunities
high_value_upsell = len(metrics_df[(metrics_df['upsell_score'] >= 70) & (metrics_df['monthly_revenue'] >= 100)])
if high_value_upsell > 0:
    action_items.append(f"🎯 **Priority**: Contact {high_value_upsell} high-value customers with 70+ upsell scores")

# Cross-sell opportunities
if cross_sell_opportunities > 0:
    action_items.append(f"📞 **Cross-sell**: Reach out to {cross_sell_opportunities} single-service customers")

# Basic plan upgrades
basic_upgrade_count = len(upgrade_opportunities)
if basic_upgrade_count > 0:
    action_items.append(f"⭐ **Upgrades**: Promote premium plans to {basic_upgrade_count} basic plan customers")

# Campaign launches
action_items.append("📢 **Campaigns**: Launch mobile bundle and premium upgrade campaigns")
action_items.append("📊 **Analytics**: Track conversion rates and adjust targeting")

for i, item in enumerate(action_items, 1):
    st.markdown(f"{i}. {item}")

st.markdown("---")
st.markdown("💡 **Sales Strategy**: Focus on high-priority prospects with proven satisfaction and engagement. Bundle offerings create higher value and reduce churn.")