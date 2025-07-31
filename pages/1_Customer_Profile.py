import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Page configuration
st.set_page_config(
    page_title="Customer Profile",
    page_icon="👤",
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

st.title("👤 Customer Profile Analysis")

# Customer selection
customers_df = data['customers']
services_df = data['services']
billing_df = data['billing']
tickets_df = data['support_tickets']
usage_df = data['usage']
metrics_df = data['customer_metrics']
nps_df = data['nps_surveys']

# Customer selector
customer_options = customers_df.apply(
    lambda x: f"{x['customer_id']} - {x['first_name']} {x['last_name']} ({x['email']})", 
    axis=1
).tolist()

selected_customer = st.selectbox("Select a customer:", customer_options)
customer_id = selected_customer.split(' - ')[0]

# Get customer data
customer = customers_df[customers_df['customer_id'] == customer_id].iloc[0]
customer_services = services_df[services_df['customer_id'] == customer_id]
customer_billing = billing_df[billing_df['customer_id'] == customer_id]
customer_tickets = tickets_df[tickets_df['customer_id'] == customer_id]
customer_usage = usage_df[usage_df['customer_id'] == customer_id]
customer_metrics = metrics_df[metrics_df['customer_id'] == customer_id].iloc[0]
customer_nps = nps_df[nps_df['customer_id'] == customer_id]

# Customer Header
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown(f"""
    ## {customer['first_name']} {customer['last_name']}
    **Customer ID:** {customer['customer_id']}  
    **Email:** {customer['email']}  
    **Phone:** {customer['phone_number']}  
    **Segment:** {customer['customer_segment']}  
    **Status:** {customer['account_status']}
    """)

with col2:
    st.metric("Monthly Revenue", f"${customer_metrics['monthly_revenue']:.2f}")
    st.metric("Tenure", f"{customer_metrics['tenure_months']} months")

with col3:
    # Churn risk color coding
    risk = customer_metrics['churn_risk_score']
    risk_color = "🟢" if risk < 30 else "🟡" if risk < 70 else "🔴"
    st.metric("Churn Risk", f"{risk_color} {risk}%")
    st.metric("Upsell Score", f"{customer_metrics['upsell_score']}%")

st.markdown("---")

# Customer Details Section
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📋 Customer Information")
    info_data = {
        "Date of Birth": customer['date_of_birth'],
        "Gender": customer['gender'],
        "Address": customer['address'],
        "City": customer['city'],
        "State": customer['state'],
        "Account Created": customer['account_creation_date'],
        "Preferred Contact": customer['preferred_contact_method'],
        "Credit Score": customer['credit_score'],
        "Annual Income": f"${customer['annual_income']:,}"
    }
    for key, value in info_data.items():
        st.write(f"**{key}:** {value}")

with col2:
    st.markdown("### 📊 Account Summary")
    summary_data = {
        "Total Services": customer_metrics['total_services'],
        "Active Services": customer_metrics['active_services'],
        "Lifetime Value": f"${customer_metrics['total_lifetime_value']:.2f}",
        "Support Tickets": customer_metrics['support_tickets_count'],
        "Avg Resolution Time": f"{customer_metrics['avg_resolution_time_hours']:.1f} hours",
        "Avg Satisfaction": f"{customer_metrics['avg_satisfaction_rating']:.1f}/5",
        "Latest NPS Score": customer_metrics['latest_nps_score'] if pd.notna(customer_metrics['latest_nps_score']) else "N/A"
    }
    for key, value in summary_data.items():
        st.write(f"**{key}:** {value}")

# Services Section
st.markdown("### 🛜 Current Services")
if len(customer_services) > 0:
    services_display = customer_services[['plan_name', 'service_type', 'monthly_fee', 'service_status', 'service_start_date']].copy()
    services_display.columns = ['Plan Name', 'Service Type', 'Monthly Fee ($)', 'Status', 'Start Date']
    st.dataframe(services_display, use_container_width=True)
else:
    st.info("No services found for this customer.")

# Billing and Usage Analysis
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 💳 Billing History")
    if len(customer_billing) > 0:
        billing_df_plot = customer_billing.copy()
        billing_df_plot['bill_date'] = pd.to_datetime(billing_df_plot['bill_date'])
        billing_df_plot = billing_df_plot.sort_values('bill_date')
        
        fig_billing = px.line(billing_df_plot, x='bill_date', y='amount_due',
                             title='Monthly Bills Over Time',
                             labels={'amount_due': 'Amount ($)', 'bill_date': 'Date'})
        st.plotly_chart(fig_billing, use_container_width=True)
        
        # Payment status summary
        payment_summary = customer_billing['payment_status'].value_counts()
        st.write("**Payment History:**")
        for status, count in payment_summary.items():
            st.write(f"- {status}: {count} bills")
    else:
        st.info("No billing history available.")

with col2:
    st.markdown("### 📱 Usage Patterns")
    if len(customer_usage) > 0:
        usage_df_plot = customer_usage.copy()
        
        # Mobile usage
        mobile_usage = usage_df_plot[usage_df_plot['service_id'].isin(
            customer_services[customer_services['service_type'] == 'Mobile']['service_id']
        )]
        
        if len(mobile_usage) > 0:
            fig_usage = px.bar(mobile_usage, x='usage_month', y='data_used_gb',
                              title='Mobile Data Usage (GB)',
                              labels={'data_used_gb': 'Data Used (GB)', 'usage_month': 'Month'})
            st.plotly_chart(fig_usage, use_container_width=True)
        else:
            st.info("No mobile usage data available.")
    else:
        st.info("No usage data available.")

# Support Tickets Section
st.markdown("### 🎫 Support History")
if len(customer_tickets) > 0:
    tickets_display = customer_tickets[['ticket_id', 'creation_date', 'issue_type', 'priority', 'status', 'satisfaction_rating']].copy()
    tickets_display.columns = ['Ticket ID', 'Date', 'Issue Type', 'Priority', 'Status', 'Satisfaction']
    st.dataframe(tickets_display, use_container_width=True)
    
    # Support metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        avg_resolution = customer_tickets['resolution_time_hours'].mean()
        st.metric("Avg Resolution Time", f"{avg_resolution:.1f} hours")
    with col2:
        avg_satisfaction = customer_tickets['satisfaction_rating'].mean()
        st.metric("Avg Satisfaction", f"{avg_satisfaction:.1f}/5")
    with col3:
        open_tickets = len(customer_tickets[customer_tickets['status'].isin(['Open', 'In Progress'])])
        st.metric("Open Tickets", open_tickets)
else:
    st.info("No support tickets found for this customer.")

# NPS History
st.markdown("### 😊 Customer Satisfaction (NPS)")
if len(customer_nps) > 0:
    nps_df_plot = customer_nps.copy()
    nps_df_plot['survey_date'] = pd.to_datetime(nps_df_plot['survey_date'])
    nps_df_plot = nps_df_plot.sort_values('survey_date')
    
    fig_nps = px.line(nps_df_plot, x='survey_date', y='nps_score',
                     title='NPS Score Over Time',
                     labels={'nps_score': 'NPS Score (0-10)', 'survey_date': 'Date'})
    fig_nps.add_hline(y=9, line_dash="dash", line_color="green", 
                     annotation_text="Promoter (9-10)")
    fig_nps.add_hline(y=7, line_dash="dash", line_color="orange", 
                     annotation_text="Passive (7-8)")
    st.plotly_chart(fig_nps, use_container_width=True)
    
    # Latest feedback
    if len(customer_nps) > 0:
        latest_nps = customer_nps.loc[customer_nps['survey_date'].idxmax()]
        if pd.notna(latest_nps['feedback']):
            st.markdown("**Latest Feedback:**")
            st.write(f"*\"{latest_nps['feedback']}\"*")
else:
    st.info("No NPS survey data available for this customer.")

# Sales Opportunities
st.markdown("### 🎯 Sales Opportunities")

opportunities = []

# Check for upselling opportunities
if customer_metrics['upsell_score'] > 50:
    if len(customer_services[customer_services['service_type'] == 'Mobile']) == 0:
        opportunities.append("📱 **Mobile Service**: Customer has no mobile service - high opportunity")
    if len(customer_services[customer_services['service_type'] == 'Internet']) == 0:
        opportunities.append("🌐 **Internet Service**: Customer has no internet service - consider bundling")
    if len(customer_services[customer_services['service_type'] == 'TV']) == 0:
        opportunities.append("📺 **TV Service**: Customer has no TV service - bundle opportunity")

# Check for upgrade opportunities
basic_services = customer_services[customer_services['plan_name'].str.contains('Basic', na=False)]
if len(basic_services) > 0:
    opportunities.append("⬆️ **Plan Upgrade**: Customer has basic plans - consider premium upgrades")

if customer_metrics['monthly_revenue'] < 100:
    opportunities.append("💰 **Revenue Growth**: Low ARPU customer - explore additional services")

if opportunities:
    for opp in opportunities:
        st.markdown(opp)
else:
    st.info("No immediate sales opportunities identified.")

# Action Items
st.markdown("### ⚡ Recommended Actions")
actions = []

if customer_metrics['churn_risk_score'] > 70:
    actions.append("🚨 **HIGH PRIORITY**: Customer at high risk of churn - schedule retention call")
elif customer_metrics['churn_risk_score'] > 40:
    actions.append("⚠️ **MEDIUM PRIORITY**: Customer showing churn signals - proactive outreach recommended")

if customer_metrics['support_tickets_count'] > 3:
    actions.append("📞 **Follow-up**: Customer has multiple support tickets - check satisfaction")

if customer_metrics['avg_satisfaction_rating'] < 4:
    actions.append("😔 **Satisfaction**: Low satisfaction scores - investigate and address concerns")

if customer_metrics['upsell_score'] > 70:
    actions.append("💡 **Sales Opportunity**: High upsell potential - schedule consultation")

if actions:
    for action in actions:
        st.markdown(action)
else:
    st.success("✅ No immediate actions required - customer appears stable")