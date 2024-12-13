import pandas as pd
from fuzzywuzzy import process
import hashlib
import logging
import hashlib

def generate_unique_id(full_name):
    """Generates a unique ID by hashing the full name."""
    return hashlib.sha256(full_name.encode('utf-8')).hexdigest()[:8]

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fuzzy_match_names(df1, df2):
    """Matches names between two DataFrames using fuzzy matching."""
    matched = []
    unmatched_df1 = []
    unmatched_df2 = []

    for i, name1 in df1['FULL NAME'].items():
        result = process.extractOne(name1, df2['FULL NAME'])
        if result and len(result) >= 2 and result[1] >= 85:  # Match threshold
            best_match, score = result[:2]  # Unpack only the first two values
            matched.append((i, df2[df2['FULL NAME'] == best_match].index[0]))
        else:
            unmatched_df1.append(i)

    # Initialize the MATCHED columns safely
    df1['MATCHED'] = False
    df2['MATCHED'] = False

    for idx1, idx2 in matched:
        df1.loc[idx1, 'MATCHED'] = True
        df2.loc[idx2, 'MATCHED'] = True

    unmatched_df1 = df1[~df1['MATCHED']].drop(columns=['MATCHED'])
    unmatched_df2 = df2[~df2['MATCHED']].drop(columns=['MATCHED'])

    return df1[df1['MATCHED']], df2[df2['MATCHED']], unmatched_df1, unmatched_df2

def compare_premiums(matched_df1, matched_df2):
    """Compares premiums and calculates status and issues."""
    combined = pd.merge(matched_df1, matched_df2, on=['FIRST NAME', 'LAST NAME'], how='outer')
    combined['STATUS'] = 'Invalid'  # Default to Invalid
    combined['ISSUE'] = None  # Default to no issue

    for idx, row in combined.iterrows():
        ee_nav = row.get('PREMIUM TOTAL', None)
        principal = row.get('PRINCIPAL PREMIUM', None)

        if pd.isna(ee_nav) or pd.isna(principal):
            # One of the columns is missing
            combined.loc[idx, 'STATUS'] = 'Invalid'
            if pd.isna(ee_nav) and pd.isna(principal):
                combined.loc[idx, 'ISSUE'] = 'Missing Both Premiums'
            elif pd.isna(ee_nav):
                combined.loc[idx, 'ISSUE'] = 'Missing EE Nav Premium'
            elif pd.isna(principal):
                combined.loc[idx, 'ISSUE'] = 'Missing Principal Premium'
        elif abs(ee_nav - principal) > 0.01:  # Allow for small floating-point differences
            # Both columns are present but don't match
            combined.loc[idx, 'STATUS'] = 'Invalid'
            combined.loc[idx, 'ISSUE'] = 'Premium Mismatch'
        else:
            # Both columns are present and match
            combined.loc[idx, 'STATUS'] = 'Valid'
            combined.loc[idx, 'ISSUE'] = None

    return combined



# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def preprocess_names(df, first_name_col, last_name_col):
    """Strips whitespace and standardizes case for first and last name columns."""
    df[first_name_col] = df[first_name_col].str.strip().str.upper()
    df[last_name_col] = df[last_name_col].str.strip().str.upper()
    return df

def clean_eenav_file(file_path, output_path, validate_total_premium=True):
    """Cleans the EE Nav test file."""
    df = pd.read_excel(file_path)

    # Standardize column names
    df.columns = df.columns.str.strip().str.upper()

    # Rename columns dynamically
    df.rename(columns={'TOTAL PREMIUM': 'PREMIUM TOTAL'}, inplace=True)

    # Validate required columns
    required_columns = ['LAST NAME', 'FIRST NAME', 'PREMIUM TOTAL']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Missing required columns in eenav_test file: {missing_columns}")

    # Ensure numeric columns
    df['PREMIUM TOTAL'] = pd.to_numeric(df['PREMIUM TOTAL'], errors='coerce').fillna(0)

    # Preprocess names
    df = preprocess_names(df, 'FIRST NAME', 'LAST NAME')

    # Retain relevant columns
    df = df[['FIRST NAME', 'LAST NAME', 'PREMIUM TOTAL']]

    # Save cleaned file
    df.to_excel(output_path, index=False, engine='openpyxl')
    return df

def clean_principal_file(file_path, output_path):
    """Cleans the Principal test file."""
    df = pd.read_excel(file_path)

    # Standardize column names
    df.columns = df.columns.str.strip().str.upper()

    # Validate required columns
    required_columns = ['MEMBER NAME', 'TOTAL PREMIUM']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Missing required columns in principal_test file: {missing_columns}")

    # Split MEMBER NAME into FIRST NAME and LAST NAME
    name_split = df['MEMBER NAME'].str.split(',', expand=True)
    df['LAST NAME'] = name_split[0].str.strip().str.upper()
    df['FIRST NAME'] = name_split[1].str.strip().str.upper() if name_split.shape[1] > 1 else None

    # Rename TOTAL PREMIUM
    df.rename(columns={'TOTAL PREMIUM': 'PRINCIPAL PREMIUM'}, inplace=True)

    # Preprocess names
    df = preprocess_names(df, 'FIRST NAME', 'LAST NAME')

    # Retain relevant columns
    df = df[['FIRST NAME', 'LAST NAME', 'PRINCIPAL PREMIUM']]

    # Save cleaned file
    df.to_excel(output_path, index=False, engine='openpyxl')
    return df

def finalize_output(combined_df):
    """Finalizes the output file."""
    # Debugging: Check available columns
    print("Available columns in combined_df:", combined_df.columns)

    # Dynamically drop unnecessary columns if they exist
    columns_to_drop = ['FULL NAME_X', 'FULL NAME_Y', 'MATCHED_X', 'MATCHED_Y']
    existing_columns = [col for col in columns_to_drop if col in combined_df.columns]
    combined_df.drop(columns=existing_columns, inplace=True)

    # Reorder columns to make UNIQUE ID the first column
    columns_order = ['UNIQUE ID', 'FIRST NAME', 'LAST NAME', 'PREMIUM TOTAL', 'PRINCIPAL PREMIUM', 'STATUS', 'ISSUE']
    combined_df = combined_df[[col for col in columns_order if col in combined_df.columns]]

    return combined_df
def save_final_output(df, output_path):
    """Saves the final DataFrame to an Excel file."""
    df.to_excel(output_path, index=False, engine='openpyxl')
    logging.info(f"Discrepancy report saved to {output_path}")

def main():
    ee_nav_file = "eenav_test.xlsx"
    principal_file = "principal_test.xlsx"
    ee_nav_clean_file = "eenav_clean.xlsx"
    principal_clean_file = "principal_clean.xlsx"
    output_file = "discrepancies.xlsx"

    # Clean files
    ee_nav_cleaned = clean_eenav_file(ee_nav_file, ee_nav_clean_file)
    principal_cleaned = clean_principal_file(principal_file, principal_clean_file)

    # Prepare full names for matching
    ee_nav_cleaned['FULL NAME'] = ee_nav_cleaned['FIRST NAME'] + ' ' + ee_nav_cleaned['LAST NAME']
    principal_cleaned['FULL NAME'] = principal_cleaned['FIRST NAME'] + ' ' + principal_cleaned['LAST NAME']

    # Fuzzy match
    matched_ee_nav, matched_principal, _, _ = fuzzy_match_names(ee_nav_cleaned, principal_cleaned)

    # Assign unique IDs
    matched_ee_nav['UNIQUE ID'] = (
        matched_ee_nav['FIRST NAME'] + ' ' + matched_ee_nav['LAST NAME']
    ).apply(generate_unique_id)

    # Compare premiums
    discrepancies = compare_premiums(matched_ee_nav, matched_principal)

    # Finalize and save output
    finalized_df = finalize_output(discrepancies)
    save_final_output(finalized_df, output_file)

if __name__ == "__main__":
    main()
