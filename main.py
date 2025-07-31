import streamlit as st
import snowflake.snowpark.context

# Page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="Telco Network Optimization Suite",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Snowflake session
@st.cache_resource
def init_session():
    return snowflake.snowpark.context.get_active_session()

session = init_session()

# Main page content
st.title("📡 Telco Network Optimization Suite")
st.markdown("""
### Solve Your Toughest Network Challenges
Today's telco operations are overwhelmed by vast network data, customer complaints, and sprawling infrastructure. Our Telco Network Optimization Suite cuts through the noise to deliver clarity and action.
#### We solve your core problems by providing:
- **Rapid Insight**: Instantly pinpoint cell towers driving the most trouble tickets.
- **Proactive Monitoring**: Visualize live customer sentiment and ticket-density hotbeds with dynamic heatmaps.
- **Actionable Analytics**: Directly correlate network performance metrics with real-time customer complaints.
- **Reduced MTTR (Mean Time To Resolution)**: Quickly identify root causes of issues and accelerate problem-solving.
- **Enhanced Customer Satisfaction**: Address issues proactively and improve service quality based on real-time feedback.
- **Optimized Network Spend**: Intelligently allocate resources to areas of highest impact, avoiding unnecessary infrastructure upgrades.
- **Future-Proof Scalability**: Built on Snowflake, this solution scales effortlessly with your growing data volumes and network demands.

All this is powered by Snowflake's elastic data platform and a user-friendly Streamlit front-end, requiring no bespoke coding. Get the intelligence you need to prioritize, optimize, and ensure operational excellence.


Use the sidebar to navigate between different analysis views.
""")

st.image(
    "https://quickstarts.snowflake.com/guide/optimizing-network-operations-with-cortex-ai-call-transcripts-and-tower-data-analysis/img/dad88af756439cbf.png",
    caption="Optimizing Network Operations with Cortex AI", 
    width=1000
)

# Display some key network stats on the home page
st.markdown("""
### Getting Started
Select a page from the sidebar to begin your analysis.
""")

# Display some key network stats on the home page
col1, col2, col3 = st.columns(3)

# Count of cell towers
total_cells = session.sql("""
    SELECT COUNT(DISTINCT cell_id) as total_cells
    FROM TELCO_NETWORK_OPTIMIZATION_PROD.RAW.CELL_TOWER
""").collect()[0]["TOTAL_CELLS"]

# Average failure rate
avg_failure = session.sql("""
    SELECT ROUND(AVG(CASE WHEN call_release_code != 0 THEN 1 ELSE 0 END) * 100, 2) as failure_rate
    FROM TELCO_NETWORK_OPTIMIZATION_PROD.RAW.CELL_TOWER
""").collect()[0]["FAILURE_RATE"]

# Count of support tickets
ticket_count = session.sql("""
    SELECT COUNT(*) as ticket_count
    FROM TELCO_NETWORK_OPTIMIZATION_PROD.RAW.SUPPORT_TICKETS
""").collect()[0]["TICKET_COUNT"]

col1.metric("Total Cell Towers", f"{total_cells:,}")
col2.metric("Average Failure Rate", f"{avg_failure}%")
col3.metric("Support Tickets", f"{ticket_count:,}") 