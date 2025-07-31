-- ===================================================================
-- TROUBLESHOOTING SCRIPT - STREAMLIT IN SNOWFLAKE DEPLOYMENT
-- ===================================================================

-- Check current context
SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_SCHEMA();

-- Check if database exists and you have access
USE DATABASE TELCO_NETWORK_OPTIMIZATION_PROD;
SHOW SCHEMAS;

-- Check if STREAMLIT_APPS schema exists
SHOW SCHEMAS LIKE 'STREAMLIT_APPS';

-- Use the schema
USE SCHEMA STREAMLIT_APPS;

-- Check if APP_STAGE exists
SHOW STAGES LIKE 'APP_STAGE';

-- If stage doesn't exist, create it
CREATE STAGE IF NOT EXISTS APP_STAGE;

-- Check stage permissions
DESC STAGE APP_STAGE;

-- Try to list the stage
LIST @APP_STAGE;

-- Check your current role's privileges
SHOW GRANTS TO ROLE SYSADMIN;  -- Replace with your current role

-- Check what warehouses you have access to
SHOW WAREHOUSES;

-- Check if any Streamlit apps exist
SHOW STREAMLITS;

-- If you need to drop and recreate everything:
-- DROP STREAMLIT IF EXISTS TELCO_NETWORK_OPTIMIZATION_SUITE;
-- DROP STAGE IF EXISTS APP_STAGE;

-- Alternative: Create with different permissions
-- CREATE OR REPLACE STAGE APP_STAGE 
--   ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
--   COMMENT = 'Stage for Streamlit apps';

-- Grant permissions to additional roles if needed
-- GRANT USAGE ON SCHEMA STREAMLIT_APPS TO ROLE PUBLIC;
-- GRANT READ, WRITE ON STAGE APP_STAGE TO ROLE PUBLIC;

-- ===================================================================
-- COMMON SOLUTIONS:
-- 
-- 1. If stage doesn't exist:
--    - Run the stage creation section above
--
-- 2. If permission denied:
--    - Check your current role has SYSADMIN or similar privileges
--    - Ask your Snowflake admin to grant permissions
--
-- 3. If warehouse not found:
--    - Update QUERY_WAREHOUSE to a warehouse you have access to
--    - Use SHOW WAREHOUSES to see available warehouses
-- ===================================================================