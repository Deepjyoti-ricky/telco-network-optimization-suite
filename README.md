# Customer 360 Sales Dashboard

A comprehensive Streamlit dashboard for telco sales teams to analyze customer data, identify opportunities, and track satisfaction metrics.

## Features

- **📊 Customer Overview**: Key metrics and customer search functionality
- **👤 Customer Profile**: Detailed individual customer analysis with complete 360-degree view
- **💰 Revenue Analytics**: ARPU trends, revenue forecasting, and opportunity analysis
- **⚠️ Churn Risk Analysis**: Predictive customer retention insights and risk scoring
- **🎯 Sales Opportunities**: Upselling and cross-selling prospect identification
- **😊 Customer Satisfaction**: NPS tracking, support satisfaction analysis, and feedback monitoring

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate sample data:**
   ```bash
   python3 data_generator.py
   ```

3. **Run the dashboard:**
   ```bash
   streamlit run main.py
   ```

## Usage

1. **Home Page**: View overall business metrics and search for customers
2. **Customer Profile**: Select and analyze individual customers in detail
3. **Revenue Analytics**: Explore revenue trends, segment performance, and forecasting
4. **Churn Risk Analysis**: Identify at-risk customers and retention opportunities
5. **Sales Opportunities**: Find upselling, cross-selling, and upgrade prospects
6. **Customer Satisfaction**: Monitor NPS scores, support satisfaction, and feedback

## Data

The app uses synthetically generated data including:
- 1,000 customers across Individual, Small Business, and Enterprise segments
- Mobile, Internet, and TV service offerings
- 12 months of billing, usage, and support history
- NPS surveys and customer satisfaction ratings
- Calculated metrics for churn risk and upsell scoring

## Key Metrics

- **Customer Segments**: Individual, Small Business, Enterprise
- **Service Types**: Mobile, Internet, TV with various plan tiers
- **Churn Risk Scoring**: Based on support tickets, payment history, satisfaction, and NPS
- **Upsell Scoring**: Considers current services, satisfaction, tenure, and engagement
- **Revenue Analytics**: ARPU, lifetime value, segment performance, and forecasting

## Dashboard Navigation

Use the sidebar to navigate between different analysis views. Each page provides:
- Interactive visualizations using Plotly
- Actionable insights and recommendations
- Exportable data tables
- Key performance indicators and trends

## Technical Details

- **Framework**: Streamlit
- **Visualization**: Plotly Express & Graph Objects
- **Data Processing**: Pandas, NumPy
- **Data Generation**: Faker library for realistic synthetic data
- **Cache**: Streamlit caching for optimal performance

## Future Enhancements

- Real-time data integration
- Advanced ML models for churn prediction
- Automated campaign recommendations
- Integration with CRM systems
- Mobile-responsive design
- Advanced segmentation capabilities

---

**Note**: This dashboard uses synthetic data for demonstration purposes. In a production environment, connect to your actual customer database and data warehouse.