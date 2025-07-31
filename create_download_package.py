#!/usr/bin/env python3
"""
Create a downloadable package for Streamlit in Snowflake deployment
"""
import os
import zipfile
from pathlib import Path

def create_streamlit_package():
    """Create a ZIP file with all necessary files for Streamlit in Snowflake upload"""
    
    # Define the package name
    package_name = "telco_network_optimization_streamlit_package.zip"
    
    # Files to include in the package
    files_to_include = [
        # Main application file
        "main.py",
        
        # All dashboard pages
        "pages/2_Cell_Tower_Lookup.py",
        "pages/3_Geospatial_Analysis.py", 
        "pages/4_Correlation_Analytics.py",
        "pages/5_Customer_Impact_Dashboard.py",
        "pages/6_Loyalty_Status_Impact_View.py",
        "pages/7_Time_Series_Analysis.py",
        "pages/8_Service_Type_Performance_Breakdown.py",
        "pages/9_Issue_Prioritization_Matrix.py",
        "pages/10_Problematic_Cell_Towers.py",
        
        # Documentation and guides
        "STREAMLIT_UPLOAD_PACKAGE.md",
        "STREAMLIT_IN_SNOWFLAKE_DEPLOYMENT_GUIDE.md",
        "STREAMLIT_IN_SNOWFLAKE_PACKAGES.txt",
        
        # SQL deployment scripts
        "deploy_streamlit_in_snowflake.sql",
        "quick_fix_deployment.sql",
        "deploy_step_by_step.sql",
        "troubleshoot_deployment.sql",
        "upload_files_to_snowflake.sql"
    ]
    
    # Create the ZIP file
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files_to_include:
            if os.path.exists(file_path):
                # Add file to ZIP maintaining folder structure
                zipf.write(file_path, file_path)
                print(f"✅ Added: {file_path}")
            else:
                print(f"⚠️  File not found: {file_path}")
    
    # Get package size
    package_size = os.path.getsize(package_name) / 1024  # Size in KB
    
    print(f"\n🎉 Package created successfully!")
    print(f"📦 File: {package_name}")
    print(f"📊 Size: {package_size:.1f} KB")
    print(f"📁 Contains {len(files_to_include)} files")
    
    print(f"\n📋 Next Steps:")
    print(f"1. Download the {package_name} file")
    print(f"2. Extract the ZIP file")
    print(f"3. Follow STREAMLIT_UPLOAD_PACKAGE.md for upload instructions")
    print(f"4. Upload files to Snowflake Streamlit interface")
    
    return package_name

if __name__ == "__main__":
    create_streamlit_package()