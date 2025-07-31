-- ===================================================================
-- QUICK FIX - STREAMLIT DEPLOYMENT WITH STAGE ISSUE RESOLVED
-- ===================================================================

-- Set context
USE DATABASE TELCO_NETWORK_OPTIMIZATION_PROD;

-- Drop and recreate schema to start fresh
DROP SCHEMA IF EXISTS STREAMLIT_APPS CASCADE;
CREATE SCHEMA STREAMLIT_APPS;
USE SCHEMA STREAMLIT_APPS;

-- Create stage with explicit permissions
CREATE OR REPLACE STAGE APP_STAGE
  COMMENT = 'Stage for Telco Network Optimization Streamlit application files';

-- Grant permissions to current role (adjust as needed)
GRANT ALL ON STAGE APP_STAGE TO ROLE SYSADMIN;
GRANT ALL ON STAGE APP_STAGE TO ROLE ACCOUNTADMIN;

-- Wait a moment for permissions to propagate, then verify
SELECT 'Stage created successfully' as STATUS;
LIST @APP_STAGE;

-- Create Streamlit app (replace COMPUTE_WH with your warehouse)
CREATE OR REPLACE STREAMLIT TELCO_NETWORK_OPTIMIZATION_SUITE
  ROOT_LOCATION = '@APP_STAGE'
  MAIN_FILE = '/main.py'
  QUERY_WAREHOUSE = 'COMPUTE_WH'  -- ⚠️ CHANGE THIS TO YOUR WAREHOUSE
  COMMENT = 'Telco Network Optimization Suite - Network performance analytics';

-- Grant permissions on Streamlit app
GRANT ALL ON STREAMLIT TELCO_NETWORK_OPTIMIZATION_SUITE TO ROLE SYSADMIN;
GRANT ALL ON STREAMLIT TELCO_NETWORK_OPTIMIZATION_SUITE TO ROLE ACCOUNTADMIN;

-- Verify creation
SHOW STREAMLITS;

-- Display access URL
SELECT 
    'SUCCESS! Access your app at: https://' || 
    CURRENT_ACCOUNT() || '.snowflakecomputing.com/streamlit/' ||
    CURRENT_DATABASE() || '/' || CURRENT_SCHEMA() || 
    '/TELCO_NETWORK_OPTIMIZATION_SUITE' as ACCESS_URL;

-- ===================================================================
-- ALTERNATIVE WAREHOUSE NAMES TO TRY:
-- Common warehouse names: COMPUTE_WH, WH, WAREHOUSE, TEST_WH, DEV_WH
-- 
-- To see available warehouses: SHOW WAREHOUSES;
-- ===================================================================