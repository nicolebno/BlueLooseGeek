import pandas as pd
import hashlib


# Debugging helper function
def debug_print(message, df=None):
    """Helper function to print debug messages and DataFrame previews."""
    print(f"[DEBUG] {message}")
    if df is not None:
        print(df.head())
        print(f"Columns: {list(df.columns)}\n")


# Function to normalize names (remove spaces, dashes, and make lowercase)
def normalize_name(name):
    """Normalize names by removing spaces, dashes, and converting to lowercase."""
    if pd.isna(name):
        return None
    return ''.join(name.split()).replace('-', '').lower()


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
    Compare EE Nav and Principal files, consolidate matches, and return a combined DataFrame.
    """
    debug_print("Comparing files: EE Nav file:", df_ee)
    debug_print("Comparing files: Principal file:", df_principal)

    # Normalize names in both dataframes
    df_ee['NORMALIZED FIRST NAME'] = df_ee['FIRST NAME'].apply(normalize_name)
    df_ee['NORMALIZED LAST NAME'] = df_ee['LAST NAME'].apply(normalize_name)

    df_principal['NORMALIZED FIRST NAME'] = df_principal['FIRST NAME'].apply(normalize_name)
    df_principal['NORMALIZED LAST NAME'] = df_principal['LAST NAME'].apply(normalize_name)

    # Merge dataframes on normalized names
    combined = pd.merge(
        df_ee,
        df_principal,
        on=['NORMALIZED FIRST NAME', 'NORMALIZED LAST NAME'],
        how='outer',
        suffixes=('_ee', '_principal'),
        indicator=True
    )

    # Remove rows where both normalized names are missing
    combined = combined[~(combined['NORMALIZED FIRST NAME'].isna() & combined['NORMALIZED LAST NAME'].isna())]

    # Generate unique IDs based on normalized names
    combined['UNIQUE ID'] = combined.apply(
        lambda x: hashlib.sha256(
            f"{x['NORMALIZED FIRST NAME']}{x['NORMALIZED LAST NAME']}".encode()
        ).hexdigest()[:8]
        if pd.notna(x['NORMALIZED FIRST NAME']) and pd.notna(x['NORMALIZED LAST NAME']) else None,
        axis=1
    )

    # Add Status and Issue columns
    combined['STATUS'] = None
    combined['ISSUE'] = None

    for idx, row in combined.iterrows():
        if pd.isna(row['UNIQUE ID']):
            # Skip validation for rows without unique IDs
            continue

        if row['_merge'] == 'left_only':  # EE Nav only
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Missing Principal Premium'
        elif row['_merge'] == 'right_only':  # Principal file only
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Missing EE Nav Premium'
        elif pd.isna(row['TOTAL PREMIUM']) or pd.isna(row['PRINCIPAL PREMIUM']):
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Missing Premium Data'
        elif row['TOTAL PREMIUM'] != row['PRINCIPAL PREMIUM']:
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Premium Mismatch'

    # Drop unnecessary columns
    combined.drop(columns=['_merge', 'NORMALIZED FIRST NAME', 'NORMALIZED LAST NAME'], inplace=True)

    # Reorder columns for better readability
    combined = combined[['UNIQUE ID', 'FIRST NAME', 'LAST NAME', 'TOTAL PREMIUM', 'PRINCIPAL PREMIUM', 'STATUS', 'ISSUE']]
    debug_print("Final Comparison Result:", combined)

    return combined


# Main function for testing purposes
def main():
    # Load example files (replace with your file paths for testing)
    try:
        df_ee = pd.read_excel("ee_nav_file.xlsx")
        debug_print("Loaded EE Nav file:", df_ee)

        df_principal = pd.read_excel("principal_file.xlsx")
        debug_print("Loaded Principal file:", df_principal)
    except Exception as e:
        print(f"[ERROR] Failed to load files: {e}")
        return

    # Define required columns
    required_ee_columns = ['FIRST NAME', 'LAST NAME', 'TOTAL PREMIUM']
    required_principal_columns = ['FIRST NAME', 'LAST NAME', 'PRINCIPAL PREMIUM']

    # Validate input files
    try:
        validate_input_file(df_ee, required_ee_columns, "EE Nav File")
        validate_input_file(df_principal, required_principal_columns, "Principal File")
    except KeyError as e:
        print(f"[ERROR] Validation error: {e}")
        return
    except Exception as e:
        print(f"[ERROR] Unexpected error during validation: {e}")
        return

    # Perform comparison
    try:
        result = compare_files(df_ee, df_principal)
        result.to_csv("comparison_result.csv", index=False)
        print("[SUCCESS] Comparison completed. Results saved to 'comparison_result.csv'.")
    except Exception as e:
        print(f"[ERROR] Failed to compare files: {e}")


if __name__ == "__main__":
    main()
