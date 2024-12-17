import streamlit as st
import pandas as pd
import hashlib

# Debugging helper function
def debug_print(message, df=None):
    """Helper function to print debug messages and DataFrame previews."""
    print(f"[DEBUG] {message}")
    if df is not None:
        print(df.head())
        print(f"Columns: {list(df.columns)}\n")

# Function to validate input files for required columns
def validate_input_file(df, required_columns, file_name):
    """
    Ensure the input file contains the required columns.
    Normalizes column names by stripping whitespace.
    """
    # Normalize column names to ensure whitespace is ignored
    df.columns = df.columns.str.strip().str.upper()
    
    # Check for missing columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"{file_name} is missing required columns: {missing_columns}")

# Function to compare files
def compare_files(df_ee, df_principal):
    """
    Compare EE Nav and Principal files, and return a combined DataFrame.
    """
    debug_print("Comparing files: EE Nav file:", df_ee)
    debug_print("Comparing files: Principal file:", df_principal)

    # Merge dataframes on 'FIRST NAME' and 'LAST NAME'
    combined = pd.merge(
        df_ee,
        df_principal,
        on=["FIRST NAME", "LAST NAME"],
        how="outer",
        suffixes=('_ee', '_principal')
    )

    # Add Status and Issue columns
    combined['STATUS'] = 'Valid'
    combined['ISSUE'] = None

    for idx, row in combined.iterrows():
        if pd.isna(row['TOTAL PREMIUM']) and pd.isna(row['PRINCIPAL PREMIUM']):
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Missing Both Premiums'
        elif pd.isna(row['TOTAL PREMIUM']):
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Missing EE Nav Premium'
        elif pd.isna(row['PRINCIPAL PREMIUM']):
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Missing Principal Premium'
        elif row['TOTAL PREMIUM'] != row['PRINCIPAL PREMIUM']:
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Premium Mismatch'

    # Generate unique IDs for each row
    combined['UNIQUE ID'] = combined.apply(
        lambda x: hashlib.sha256(f"{x['FIRST NAME']}{x['LAST NAME']}".encode()).hexdigest()[:8]
        if pd.notna(x['FIRST NAME']) and pd.notna(x['LAST NAME']) else None,
        axis=1
    )

    # Reorder columns for better readability
    combined = combined[['UNIQUE ID', 'FIRST NAME', 'LAST NAME', 'TOTAL PREMIUM', 'PRINCIPAL PREMIUM', 'STATUS', 'ISSUE']]
    debug_print("Comparison result:", combined)
    return combined

# Streamlit main function
def main():
    st.title("Premium Comparison App")
    
    # File upload widgets
    st.write("Upload EE Nav File")
    ee_file = st.file_uploader("Upload EE Nav File", type=["xlsx"], key="ee_file")
    
    st.write("Upload Principal File")
    principal_file = st.file_uploader("Upload Principal File", type=["xlsx"], key="principal_file")
    
    # Process files if both are uploaded
    if ee_file and principal_file:
        try:
            # Read the uploaded files
            df_ee = pd.read_excel(ee_file)
            df_principal = pd.read_excel(principal_file)
            
            # Define required columns
            required_ee_columns = ['FIRST NAME', 'LAST NAME', 'TOTAL PREMIUM']
            required_principal_columns = ['FIRST NAME', 'LAST NAME', 'PRINCIPAL PREMIUM']
            
            # Normalize column names (strip whitespace, uppercase)
            df_ee.columns = df_ee.columns.str.strip().str.upper()
            df_principal.columns = df_principal.columns.str.strip().str.upper()
            
            # Validate the column names
            validate_input_file(df_ee, required_ee_columns, "EE Nav File")
            validate_input_file(df_principal, required_principal_columns, "Principal File")
            
            # Compare the files
            result = compare_files(df_ee, df_principal)
            
            # Display the results
            st.success("Comparison completed successfully!")
            st.dataframe(result)
            
            # Provide a download link for the results
            csv = result.to_csv(index=False)
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name="comparison_result.csv",
                mime="text/csv"
            )
        
        except KeyError as e:
            st.error(f"Validation error: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()

