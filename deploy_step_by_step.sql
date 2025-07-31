-- ===================================================================
-- STEP-BY-STEP DEPLOYMENT - TELCO NETWORK OPTIMIZATION SUITE
-- ===================================================================
-- Run each section separately to troubleshoot any issues

-- STEP 1: Verify database access
USE DATABASE TELCO_NETWORK_OPTIMIZATION_PROD;
SHOW TABLES IN SCHEMA RAW;

-- STEP 2: Create schema for Streamlit apps
CREATE SCHEMA IF NOT EXISTS STREAMLIT_APPS;
USE SCHEMA STREAMLIT_APPS;

-- STEP 3: Create and verify the stage
CREATE OR REPLACE STAGE APP_STAGE
  COMMENT = 'Stage for Telco Network Optimization Streamlit application files';

-- Verify stage creation
DESC STAGE APP_STAGE;
SHOW STAGES;

-- STEP 4: Test stage permissions
-- List the stage (should be empty initially)
LIST @APP_STAGE;

-- STEP 5: Grant permissions to your current role
-- Replace SYSADMIN with your actual role if different
GRANT USAGE ON SCHEMA STREAMLIT_APPS TO ROLE SYSADMIN;
GRANT ALL ON STAGE APP_STAGE TO ROLE SYSADMIN;

-- STEP 6: Create the Streamlit application
CREATE OR REPLACE STREAMLIT TELCO_NETWORK_OPTIMIZATION_SUITE
  ROOT_LOCATION = '@APP_STAGE'
  MAIN_FILE = '/main.py'
  QUERY_WAREHOUSE = 'COMPUTE_WH'  -- ⚠️ UPDATE THIS TO YOUR WAREHOUSE NAME
  COMMENT = 'Telco Network Optimization Suite - Comprehensive network performance analytics dashboard';

-- STEP 7: Grant permissions on the Streamlit app
GRANT ALL ON STREAMLIT TELCO_NETWORK_OPTIMIZATION_SUITE TO ROLE SYSADMIN;

-- STEP 8: Verify everything was created
SHOW STREAMLITS;

-- STEP 9: Get the access URL
SELECT 
    'https://' || CURRENT_ACCOUNT() || '.snowflakecomputing.com/streamlit/' ||
    CURRENT_DATABASE() || '/' || CURRENT_SCHEMA() || '/TELCO_NETWORK_OPTIMIZATION_SUITE' as STREAMLIT_URL;

-- ===================================================================
-- NEXT STEPS:
-- 1. Upload your files using the upload script
-- 2. Access the URL generated above
-- ===================================================================