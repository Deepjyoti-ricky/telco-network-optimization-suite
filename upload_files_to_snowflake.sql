-- ===================================================================
-- UPLOAD APPLICATION FILES TO SNOWFLAKE STAGE
-- ===================================================================

-- Use the correct database and schema
USE DATABASE TELCO_NETWORK_OPTIMIZATION_PROD;
USE SCHEMA STREAMLIT_APPS;

-- Verify stage exists and is accessible
DESC STAGE APP_STAGE;
LIST @APP_STAGE;

-- Upload main application file
PUT file://main.py @APP_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Upload all page files
PUT file://pages/2_Cell_Tower_Lookup.py @APP_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://pages/3_Geospatial_Analysis.py @APP_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://pages/4_Correlation_Analytics.py @APP_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://pages/5_Customer_Impact_Dashboard.py @APP_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://pages/6_Loyalty_Status_Impact_View.py @APP_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://pages/7_Time_Series_Analysis.py @APP_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://pages/8_Service_Type_Performance_Breakdown.py @APP_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://pages/9_Issue_Prioritization_Matrix.py @APP_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://pages/10_Problematic_Cell_Towers.py @APP_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- List uploaded files to verify
LIST @APP_STAGE;

-- Optional: Check file contents
-- SELECT $1 FROM @APP_STAGE/main.py LIMIT 10;

COMMIT;