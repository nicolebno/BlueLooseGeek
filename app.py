import streamlit as st
import pandas as pd
from main import clean_eenav_file, clean_principal_file, compare_files

st.title("Premium Comparison App")

# File upload widgets
uploaded_file_ee = st.file_uploader("Upload EE Nav File (CSV/Excel)", type=["csv", "xlsx"])
uploaded_file_principal = st.file_uploader("Upload Principal File (CSV/Excel)", type=["csv", "xlsx"])

# Process files when the button is clicked
if st.button("Process Files"):
    if uploaded_file_ee and uploaded_file_principal:
        try:
            # Read EE Nav file
            if uploaded_file_ee.name.endswith("xlsx"):
                df_ee = pd.read_excel(uploaded_file_ee)
            else:
                df_ee = pd.read_csv(uploaded_file_ee)

            # Read Principal file
            if uploaded_file_principal.name.endswith("xlsx"):
                df_principal = pd.read_excel(uploaded_file_principal)
            else:
                df_principal = pd.read_csv(uploaded_file_principal)

            # Clean both files
            df_ee_cleaned = clean_eenav_file(df_ee)
            df_principal_cleaned = clean_principal_file(df_principal)

            # Compare the files
            result_df = compare_files(df_ee_cleaned, df_principal_cleaned)

            # Display results in the app
            st.success("Files processed successfully!")
            st.dataframe(result_df)

            # Provide download option for the results
            csv = result_df.to_csv(index=False)
            st.download_button(
                label="Download Results",
                data=csv,
                file_name="comparison_results.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.error("Please upload both files.")
