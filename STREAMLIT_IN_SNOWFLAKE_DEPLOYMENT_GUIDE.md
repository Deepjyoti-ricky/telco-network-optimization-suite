# 🚀 Telco Network Optimization Suite - Streamlit in Snowflake Deployment Guide

## ✅ **Prerequisites**

- Snowflake account with Streamlit capabilities enabled
- Access to `TELCO_NETWORK_OPTIMIZATION_PROD` database
- `SYSADMIN` role or sufficient privileges to create Streamlit apps
- Snowflake CLI or SnowSQL installed (optional but recommended)

## 🚨 **Common Issue: Stage Access Error**

If you encounter the error: **"The specified stage APP_STAGE does not exist or the current role does not have access"**

**Quick Solution:**
1. Use the `quick_fix_deployment.sql` script which handles this automatically
2. Or run `troubleshoot_deployment.sql` to diagnose the specific issue
3. Ensure you have the correct role permissions (SYSADMIN recommended)

---

## 🏗️ **Deployment Steps**

### **Step 1: Prepare Your Snowflake Environment**

1. **Connect to Snowflake** using your preferred method:
   - Snowflake Web UI
   - SnowSQL CLI
   - VS Code Snowflake Extension

2. **Verify database access**:
   ```sql
   USE DATABASE TELCO_NETWORK_OPTIMIZATION_PROD;
   SHOW TABLES IN SCHEMA RAW;
   ```

### **Step 2: Create the Streamlit Application**

⚠️ **IMPORTANT: Choose one of these deployment options:**

**Option A: Quick Fix (Recommended if you have SYSADMIN privileges)**
1. **Run the quick fix script**:
   ```sql
   -- Execute quick_fix_deployment.sql
   -- This handles the stage creation issue automatically
   ```

**Option B: Step-by-Step Deployment**
1. **Run each section of deploy_step_by_step.sql separately**:
   - This helps identify exactly where any issues occur
   - Allows for troubleshooting at each step

**Option C: Troubleshooting Approach**
1. **If you get stage errors, run troubleshoot_deployment.sql first**:
   - This diagnoses permission and access issues
   - Provides solutions for common problems

2. **Verify the application was created**:
   ```sql
   SHOW STREAMLITS;
   ```

### **Step 3: Upload Application Files**

**Option A: Using Snowflake Web UI**
1. Navigate to **Data > Databases > TELCO_NETWORK_OPTIMIZATION_PROD > Schemas > STREAMLIT_APPS > Stages > APP_STAGE**
2. Click **"+ Files"** and upload:
   - `main.py` (to root folder)
   - All files from `pages/` folder (create a `pages` subfolder)

**Option B: Using SnowSQL CLI**
1. **Navigate to your project directory**:
   ```bash
   cd /path/to/your/network_optmise/
   ```

2. **Connect to SnowSQL**:
   ```bash
   snowsql -a <your_account> -u <your_username>
   ```

3. **Run the upload script**:
   ```sql
   -- Execute the upload script
   -- Copy and paste the contents of upload_files_to_snowflake.sql
   ```

**Option C: Using PUT commands individually**
```sql
USE DATABASE TELCO_NETWORK_OPTIMIZATION_PROD;
USE SCHEMA STREAMLIT_APPS;

-- Upload files one by one
PUT file://main.py @APP_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://pages/2_Cell_Tower_Lookup.py @APP_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
-- ... (continue for all page files)
```

### **Step 4: Configure Permissions** (if needed)

```sql
-- Grant access to specific roles
GRANT USAGE ON STREAMLIT TELCO_NETWORK_OPTIMIZATION_SUITE TO ROLE <YOUR_ROLE>;

-- Grant database access to Streamlit app
GRANT USAGE ON DATABASE TELCO_NETWORK_OPTIMIZATION_PROD TO ROLE <STREAMLIT_ROLE>;
GRANT USAGE ON SCHEMA RAW TO ROLE <STREAMLIT_ROLE>;
GRANT SELECT ON ALL TABLES IN SCHEMA RAW TO ROLE <STREAMLIT_ROLE>;
```

### **Step 5: Launch Your Application**

1. **Get the application URL**:
   ```sql
   SELECT 
       'https://' || CURRENT_ACCOUNT() || '.snowflakecomputing.com/streamlit/TELCO_NETWORK_OPTIMIZATION_PROD/STREAMLIT_APPS/TELCO_NETWORK_OPTIMIZATION_SUITE' as STREAMLIT_URL;
   ```

2. **Access the application**:
   - Click the generated URL
   - Or navigate via Snowflake UI: **Projects > Streamlit > TELCO_NETWORK_OPTIMIZATION_SUITE**

---

## 🎯 **Available Dashboard Pages**

Once deployed, your application will include:

| Page | Description |
|------|-------------|
| **📡 Main Dashboard** | Executive overview with key metrics |
| **📱 Cell Tower Lookup** | Interactive cell tower performance analysis |
| **🗺️ Geospatial Analysis** | Geographic network performance mapping |
| **📊 Correlation Analytics** | Network metrics correlation analysis |
| **👥 Customer Impact Dashboard** | Customer loyalty and support impact |
| **🥇 Loyalty Status Impact View** | Deep dive into loyalty tier impacts |
| **📈 Time Series Analysis** | Temporal network performance trends |
| **🔄 Service Type Performance** | Comprehensive service analysis |
| **🎯 Issue Prioritization Matrix** | Strategic issue prioritization |
| **⚠️ Problematic Cell Towers** | Cell tower problem identification |

---

## 🔧 **Troubleshooting**

### **Common Issues & Solutions**

**1. "No module named 'snowflake'" Error**
- ✅ This only occurs in local development
- ✅ Streamlit in Snowflake has all required modules pre-installed

**2. Permission Denied Errors**
```sql
-- Grant necessary permissions
GRANT USAGE ON WAREHOUSE <YOUR_WAREHOUSE> TO ROLE <STREAMLIT_ROLE>;
GRANT SELECT ON ALL TABLES IN SCHEMA RAW TO ROLE <STREAMLIT_ROLE>;
```

**3. File Upload Issues**
- Ensure file paths are correct in PUT commands
- Check that `@APP_STAGE` exists and is accessible
- Verify file sizes are within Snowflake limits

**4. Application Won't Load**
- Check that `main.py` is uploaded to the stage root
- Verify all page files are in the `pages/` subfolder
- Ensure the correct warehouse is assigned and running

### **Updating the Application**

To update the application after making changes:

1. **Upload modified files**:
   ```sql
   PUT file://main.py @APP_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
   ```

2. **Restart the application**:
   - Changes are automatically detected
   - Refresh your browser to see updates

---

## 🎉 **Success!**

Your Telco Network Optimization Suite is now running in Streamlit in Snowflake with:

- ✅ **Live data connections** to your Snowflake database
- ✅ **No local dependency issues**
- ✅ **Scalable performance** with Snowflake compute
- ✅ **Enterprise security** and access controls
- ✅ **Easy sharing** with stakeholders via URL

---

## 📞 **Need Help?**

If you encounter any issues:

1. Check the Snowflake documentation for Streamlit apps
2. Verify your account has Streamlit capabilities enabled
3. Ensure all required permissions are granted
4. Contact your Snowflake administrator if needed

**Happy analyzing!** 🚀📊