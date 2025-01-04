import streamlit as st
import pandas as pd
import hashlib

def debug_print(message, df=None):
    """Helper function to print debug messages."""
    print(f"[DEBUG] {message}")
    if df is not None:
        print(df.head())
        print(f"Columns: {list(df.columns)}\n")

def validate_input_file(df, required_columns, file_name):
    """Validate that the input file contains required columns."""
    df.columns = df.columns.str.strip().str.upper()
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"{file_name} is missing required columns: {missing_columns}")

def compare_files(df_ee, df_principal):
    """Compare EE Nav and Principal files, consolidate matches, and return a combined DataFrame."""
    # Normalize column names and remove unnecessary spaces or dashes
    df_ee['FIRST NAME'] = df_ee['FIRST NAME'].str.strip().str.replace(r"[\s-]", "", regex=True).str.lower()
    df_ee['LAST NAME'] = df_ee['LAST NAME'].str.strip().str.replace(r"[\s-]", "", regex=True).str.lower()
    df_principal['FIRST NAME'] = df_principal['FIRST NAME'].str.strip().str.replace(r"[\s-]", "", regex=True).str.lower()
    df_principal['LAST NAME'] = df_principal['LAST NAME'].str.strip().str.replace(r"[\s-]", "", regex=True).str.lower()

    # Merge dataframes on normalized names
    combined = pd.merge(
        df_ee,
        df_principal,
        on=["FIRST NAME", "LAST NAME"],
        how="outer",
        suffixes=('_ee', '_principal'),
        indicator=True
    )

    # Remove rows where both names are missing
    combined = combined[~(combined['FIRST NAME'].isna() & combined['LAST NAME'].isna())]

    # Add Status and Issue columns
    combined['STATUS'] = 'Valid'
    combined['ISSUE'] = None

    for idx, row in combined.iterrows():
        if row['_merge'] == 'left_only':
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Missing Principal Premium'
        elif row['_merge'] == 'right_only':
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Missing EE Nav Premium'
        elif pd.isna(row['TOTAL PREMIUM']) or pd.isna(row['PRINCIPAL PREMIUM']):
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Missing Premium Data'
        elif row['TOTAL PREMIUM'] != row['PRINCIPAL PREMIUM']:
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Premium Mismatch'

    # Drop unnecessary rows and columns
    combined.drop(columns=['_merge'], inplace=True)

    # Assign unique IDs
    combined['UNIQUE ID'] = combined.apply(
        lambda x: hashlib.sha256(f"{x['FIRST NAME']}{x['LAST NAME']}".encode()).hexdigest()[:8]
        if pd.notna(x['FIRST NAME']) and pd.notna(x['LAST NAME']) else None,
        axis=1
    )

    # Exclude rows with no unique ID
    combined = combined[~combined['UNIQUE ID'].isna()]

    # Reorder columns for better readability
    combined = combined[['UNIQUE ID', 'FIRST NAME', 'LAST NAME', 'TOTAL PREMIUM', 'PRINCIPAL PREMIUM', 'STATUS', 'ISSUE']]
    return combined

def create_templates():
    """Generate and save template files for user input."""
    ee_template = pd.DataFrame({
        'FIRST NAME': [],
        'LAST NAME': [],
        'TOTAL PREMIUM': []
    })
    principal_template = pd.DataFrame({
        'FIRST NAME': [],
        'LAST NAME': [],
        'PRINCIPAL PREMIUM': []
    })

    ee_template.to_excel("EE_Nav_Template.xlsx", index=False)
    principal_template.to_excel("Principal_Template.xlsx", index=False)

    print("[INFO] Templates created: 'EE_Nav_Template.xlsx' and 'Principal_Template.xlsx'")

def main():
    st.title("Premium Comparison App")

    # File upload
    ee_file = st.file_uploader("Upload EE Nav File", type=["csv", "xlsx"])
    principal_file = st.file_uploader("Upload Carrier File", type=["csv", "xlsx"])

    if ee_file and principal_file:
        try:
            df_ee = pd.read_excel(ee_file) if "xlsx" in ee_file.name else pd.read_csv(ee_file)
            df_principal = pd.read_excel(principal_file) if "xlsx" in principal_file.name else pd.read_csv(principal_file)

            required_ee_columns = ['FIRST NAME', 'LAST NAME', 'TOTAL PREMIUM']
            required_principal_columns = ['FIRST NAME', 'LAST NAME', 'PRINCIPAL PREMIUM']

            validate_input_file(df_ee, required_ee_columns, "EE Nav File")
            validate_input_file(df_principal, required_principal_columns, "Carrier File")

            # Perform comparison
            result = compare_files(df_ee, df_principal)
            st.write("Comparison completed successfully!")
            st.dataframe(result)
            st.download_button("Download Results as CSV", result.to_csv(index=False), file_name="comparison_result.csv")

        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    create_templates()
    main()


