-- ===================================================================
-- TELCO NETWORK OPTIMIZATION SUITE - STREAMLIT IN SNOWFLAKE DEPLOYMENT
-- ===================================================================

-- Use your database and schema
USE DATABASE TELCO_NETWORK_OPTIMIZATION_PROD;
USE SCHEMA RAW;

-- Create a dedicated schema for the Streamlit application
CREATE SCHEMA IF NOT EXISTS STREAMLIT_APPS;
USE SCHEMA STREAMLIT_APPS;

-- Create a stage for storing the application files FIRST
CREATE OR REPLACE STAGE APP_STAGE
  COMMENT = 'Stage for Telco Network Optimization Streamlit application files';

-- Verify the stage was created
DESC STAGE APP_STAGE;

-- Create the main Streamlit application
CREATE OR REPLACE STREAMLIT TELCO_NETWORK_OPTIMIZATION_SUITE
  ROOT_LOCATION = '@APP_STAGE'
  MAIN_FILE = '/main.py'
  QUERY_WAREHOUSE = 'COMPUTE_WH'  -- Replace with your warehouse name
  COMMENT = 'Telco Network Optimization Suite - Comprehensive network performance analytics dashboard';

-- Grant necessary permissions (adjust roles as needed)
GRANT USAGE ON SCHEMA STREAMLIT_APPS TO ROLE SYSADMIN;
GRANT ALL ON STREAMLIT TELCO_NETWORK_OPTIMIZATION_SUITE TO ROLE SYSADMIN;
GRANT ALL ON STAGE APP_STAGE TO ROLE SYSADMIN;

-- Optional: Grant permissions to additional roles that need access
-- GRANT USAGE ON STREAMLIT TELCO_NETWORK_OPTIMIZATION_SUITE TO ROLE <YOUR_ROLE>;

-- Show the created Streamlit app
SHOW STREAMLITS;

-- Get the URL for accessing the app
SELECT 
    'https://' || CURRENT_ACCOUNT() || '.snowflakecomputing.com/streamlit/TELCO_NETWORK_OPTIMIZATION_PROD/STREAMLIT_APPS/TELCO_NETWORK_OPTIMIZATION_SUITE' as STREAMLIT_URL;