import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import os

# Page configuration
st.set_page_config(
    page_title="Revenue Analytics",
    page_icon="💰",
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

st.title("💰 Revenue Analytics")

# Get data
customers_df = data['customers']
services_df = data['services']
billing_df = data['billing']
metrics_df = data['customer_metrics']

# Prepare billing data
billing_df['bill_date'] = pd.to_datetime(billing_df['bill_date'])
billing_df['month'] = billing_df['bill_date'].dt.to_period('M')

# Key Revenue Metrics
st.markdown("## 📊 Key Revenue Metrics")

col1, col2, col3, col4 = st.columns(4)

total_revenue = billing_df['amount_paid'].sum()
monthly_revenue = billing_df.groupby('month')['amount_paid'].sum().mean()
avg_arpu = metrics_df['monthly_revenue'].mean()
total_customers = len(customers_df[customers_df['account_status'] == 'Active'])

col1.metric("Total Revenue (12M)", f"${total_revenue:,.0f}")
col2.metric("Avg Monthly Revenue", f"${monthly_revenue:,.0f}")
col3.metric("Average ARPU", f"${avg_arpu:.2f}")
col4.metric("Active Customers", f"{total_customers:,}")

# Revenue Trends
st.markdown("## 📈 Revenue Trends")

col1, col2 = st.columns(2)

with col1:
    # Monthly revenue trend
    monthly_revenue_df = billing_df.groupby('month')['amount_paid'].sum().reset_index()
    monthly_revenue_df['month'] = monthly_revenue_df['month'].dt.to_timestamp()
    
    fig_monthly = px.line(monthly_revenue_df, x='month', y='amount_paid',
                         title='Monthly Revenue Trend',
                         labels={'amount_paid': 'Revenue ($)', 'month': 'Month'})
    fig_monthly.update_traces(line_color='#2E8B57', line_width=3)
    st.plotly_chart(fig_monthly, use_container_width=True)

with col2:
    # Revenue by service type
    service_revenue = billing_df.merge(services_df[['service_id', 'service_type']], on='service_id')
    service_revenue_sum = service_revenue.groupby('service_type')['amount_paid'].sum().reset_index()
    
    fig_service = px.pie(service_revenue_sum, values='amount_paid', names='service_type',
                        title='Revenue by Service Type')
    st.plotly_chart(fig_service, use_container_width=True)

# Customer Segment Analysis
st.markdown("## 👥 Customer Segment Revenue Analysis")

# Merge customer data with metrics for segment analysis
segment_analysis = customers_df.merge(metrics_df, on='customer_id')

col1, col2 = st.columns(2)

with col1:
    # Revenue by customer segment
    segment_revenue = segment_analysis.groupby('customer_segment').agg({
        'monthly_revenue': ['sum', 'mean', 'count']
    }).round(2)
    
    segment_revenue.columns = ['Total Monthly Revenue', 'Avg ARPU', 'Customer Count']
    segment_revenue = segment_revenue.reset_index()
    
    fig_segment = px.bar(segment_revenue, x='customer_segment', y='Total Monthly Revenue',
                        title='Monthly Revenue by Customer Segment',
                        labels={'customer_segment': 'Segment', 'Total Monthly Revenue': 'Revenue ($)'})
    st.plotly_chart(fig_segment, use_container_width=True)

with col2:
    # ARPU by segment
    fig_arpu = px.box(segment_analysis, x='customer_segment', y='monthly_revenue',
                     title='ARPU Distribution by Segment',
                     labels={'customer_segment': 'Segment', 'monthly_revenue': 'Monthly Revenue ($)'})
    st.plotly_chart(fig_arpu, use_container_width=True)

# Segment summary table
st.markdown("### 📋 Segment Summary")
segment_summary = segment_analysis.groupby('customer_segment').agg({
    'monthly_revenue': ['sum', 'mean', 'median'],
    'customer_id': 'count',
    'total_lifetime_value': 'mean'
}).round(2)

segment_summary.columns = ['Total Monthly Revenue ($)', 'Mean ARPU ($)', 'Median ARPU ($)', 
                          'Customer Count', 'Avg Lifetime Value ($)']
st.dataframe(segment_summary, use_container_width=True)

# Top Revenue Customers
st.markdown("## 🌟 Top Revenue Customers")

col1, col2 = st.columns(2)

with col1:
    # Top customers by monthly revenue
    top_monthly = metrics_df.nlargest(10, 'monthly_revenue').merge(
        customers_df[['customer_id', 'first_name', 'last_name', 'customer_segment']], 
        on='customer_id'
    )
    
    display_cols = ['first_name', 'last_name', 'customer_segment', 'monthly_revenue', 'active_services']
    top_monthly_display = top_monthly[display_cols].copy()
    top_monthly_display.columns = ['First Name', 'Last Name', 'Segment', 'Monthly Revenue ($)', 'Services']
    
    st.markdown("### 📊 Top 10 by Monthly Revenue")
    st.dataframe(top_monthly_display, use_container_width=True)

with col2:
    # Top customers by lifetime value
    top_lifetime = metrics_df.nlargest(10, 'total_lifetime_value').merge(
        customers_df[['customer_id', 'first_name', 'last_name', 'customer_segment']], 
        on='customer_id'
    )
    
    display_cols = ['first_name', 'last_name', 'customer_segment', 'total_lifetime_value', 'tenure_months']
    top_lifetime_display = top_lifetime[display_cols].copy()
    top_lifetime_display.columns = ['First Name', 'Last Name', 'Segment', 'Lifetime Value ($)', 'Tenure (Months)']
    
    st.markdown("### 🏆 Top 10 by Lifetime Value")
    st.dataframe(top_lifetime_display, use_container_width=True)

# Revenue Opportunities
st.markdown("## 🎯 Revenue Opportunities")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📈 Upselling Opportunities")
    
    # High upsell score customers with low revenue
    upsell_opportunities = segment_analysis[
        (segment_analysis['upsell_score'] > 60) & 
        (segment_analysis['monthly_revenue'] < avg_arpu)
    ].nlargest(10, 'upsell_score')
    
    if len(upsell_opportunities) > 0:
        upsell_display = upsell_opportunities[['first_name', 'last_name', 'monthly_revenue', 'upsell_score', 'active_services']].copy()
        upsell_display.columns = ['First Name', 'Last Name', 'Current Revenue ($)', 'Upsell Score', 'Services']
        st.dataframe(upsell_display, use_container_width=True)
        
        potential_revenue = len(upsell_opportunities) * (avg_arpu - upsell_opportunities['monthly_revenue'].mean())
        st.metric("Potential Monthly Revenue Uplift", f"${potential_revenue:,.0f}")
    else:
        st.info("No high-potential upselling opportunities identified.")

with col2:
    st.markdown("### 🔄 Cross-selling Prospects")
    
    # Customers with only one service
    single_service_customers = segment_analysis[segment_analysis['active_services'] == 1]
    
    if len(single_service_customers) > 0:
        # Sort by monthly revenue to prioritize high-value customers
        cross_sell_opportunities = single_service_customers.nlargest(10, 'monthly_revenue')
        
        cross_sell_display = cross_sell_opportunities[['first_name', 'last_name', 'monthly_revenue', 'customer_segment']].copy()
        cross_sell_display.columns = ['First Name', 'Last Name', 'Revenue ($)', 'Segment']
        st.dataframe(cross_sell_display, use_container_width=True)
        
        avg_additional_revenue = 50  # Estimated additional revenue per service
        potential_cross_sell = len(single_service_customers) * avg_additional_revenue
        st.metric("Potential Cross-sell Revenue", f"${potential_cross_sell:,.0f}")
    else:
        st.info("All customers have multiple services.")

# Payment Analysis
st.markdown("## 💳 Payment Behavior Analysis")

col1, col2 = st.columns(2)

with col1:
    # Payment status distribution
    payment_status_counts = billing_df['payment_status'].value_counts()
    fig_payment = px.pie(values=payment_status_counts.values, names=payment_status_counts.index,
                        title='Payment Status Distribution')
    st.plotly_chart(fig_payment, use_container_width=True)

with col2:
    # Late payment impact
    late_payments = billing_df[billing_df['payment_status'] == 'Late']
    unpaid_bills = billing_df[billing_df['payment_status'] == 'Unpaid']
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Late Payments", f"{len(late_payments):,}")
        st.metric("Late Payment Revenue", f"${late_payments['amount_due'].sum():,.0f}")
    with col_b:
        st.metric("Unpaid Bills", f"{len(unpaid_bills):,}")
        st.metric("Outstanding Revenue", f"${unpaid_bills['amount_due'].sum():,.0f}")

# Revenue Forecasting
st.markdown("## 🔮 Revenue Forecast")

# Simple linear forecast based on recent trends
recent_months = billing_df[billing_df['bill_date'] >= billing_df['bill_date'].max() - pd.DateOffset(months=6)]
monthly_trend = recent_months.groupby('month')['amount_paid'].sum().reset_index()
monthly_trend['month_num'] = range(len(monthly_trend))

if len(monthly_trend) >= 3:
    # Calculate trend
    slope = np.polyfit(monthly_trend['month_num'], monthly_trend['amount_paid'], 1)[0]
    
    # Forecast next 6 months
    last_month = monthly_trend['month'].max()
    forecast_months = pd.date_range(start=last_month.to_timestamp() + pd.DateOffset(months=1), 
                                   periods=6, freq='M')
    
    last_revenue = monthly_trend['amount_paid'].iloc[-1]
    forecast_values = [last_revenue + slope * (i + 1) for i in range(6)]
    
    forecast_df = pd.DataFrame({
        'month': forecast_months,
        'amount_paid': forecast_values,
        'type': 'Forecast'
    })
    
    # Combine historical and forecast
    historical_df = monthly_trend.copy()
    historical_df['month'] = historical_df['month'].dt.to_timestamp()
    historical_df['type'] = 'Historical'
    
    combined_df = pd.concat([
        historical_df[['month', 'amount_paid', 'type']],
        forecast_df
    ])
    
    fig_forecast = px.line(combined_df, x='month', y='amount_paid', color='type',
                          title='6-Month Revenue Forecast',
                          labels={'amount_paid': 'Revenue ($)', 'month': 'Month'})
    st.plotly_chart(fig_forecast, use_container_width=True)
    
    # Forecast summary
    forecast_total = sum(forecast_values)
    current_total = monthly_trend['amount_paid'].sum()
    growth_rate = (slope / monthly_trend['amount_paid'].mean()) * 100
    
    col1, col2, col3 = st.columns(3)
    col1.metric("6-Month Forecast", f"${forecast_total:,.0f}")
    col2.metric("Monthly Growth Rate", f"{growth_rate:.1f}%")
    col3.metric("Next Month Forecast", f"${forecast_values[0]:,.0f}")
else:
    st.info("Insufficient data for revenue forecasting.")

st.markdown("---")
st.markdown("💡 **Insights**: Focus on upselling opportunities and reducing payment delays to maximize revenue growth.")