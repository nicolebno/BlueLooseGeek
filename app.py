import streamlit as st
import pandas as pd
from main import clean_eenav_file, clean_principal_file, compare_files  # Import backend logic

def main():
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

                # Debugging: Display column names
                st.write("EE Nav File Columns:", df_ee.columns)
                st.write("Principal File Columns:", df_principal.columns)

                # Validate required columns
                required_columns_ee = ['FIRST NAME', 'LAST NAME', 'Plan Cost']  # Updated column
                missing_columns_ee = [col for col in required_columns_ee if col not in df_ee.columns]
                if missing_columns_ee:
                    st.error(f"EE Nav file is missing required columns: {missing_columns_ee}")
                    return

                required_columns_principal = ['FIRST NAME', 'LAST NAME', 'PRINCIPAL PREMIUM']
                missing_columns_principal = [col for col in required_columns_principal if col not in df_principal.columns]
                if missing_columns_principal:
                    st.error(f"Principal file is missing required columns: {missing_columns_principal}")
                    return

                # Clean files
                df_ee_cleaned = clean_eenav_file(df_ee)
                df_principal_cleaned = clean_principal_file(df_principal)

                # Compare files
                comparison_results = compare_files(df_ee_cleaned, df_principal_cleaned)

                # Display results
                st.success("Files processed successfully!")
                st.write(comparison_results)

                # Download button
                @st.cache_data
                def convert_df(df):
                    return df.to_csv(index=False).encode("utf-8")

                csv = convert_df(comparison_results)

                st.download_button(
                    label="Download Results",
                    data=csv,
                    file_name="comparison_results.csv",
                    mime="text/csv",
                )

            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.error("Please upload both files.")

if __name__ == "__main__":
    main()
