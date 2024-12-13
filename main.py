import pandas as pd
import hashlib

# Function to clean EE Nav file
def clean_eenav_file(df):
    """
    Cleans the EE Nav test file by:
    - Normalizing column names (case-insensitive, trims whitespace)
    - Ensuring required columns exist
    - Removing rows with missing names
    - Removing whitespaces and dashes in names
    - Converting premiums to numeric values
    - Assigning unique IDs
    """
    # Normalize column names
    df.columns = df.columns.str.strip().str.upper()

    # Ensure required columns exist
    required_columns = ['FIRST NAME', 'LAST NAME', 'PREMIUM TOTAL']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Missing required columns in EE Nav file: {missing_columns}")

    # Drop rows where first or last name is missing
    df = df[df['FIRST NAME'].notna() & df['LAST NAME'].notna()]

    # Remove whitespaces and dashes from names
    df['FIRST NAME'] = df['FIRST NAME'].str.replace(r"[\s-]", "", regex=True).str.upper()
    df['LAST NAME'] = df['LAST NAME'].str.replace(r"[\s-]", "", regex=True).str.upper()

    # Ensure PREMIUM TOTAL is numeric
    df['PREMIUM TOTAL'] = pd.to_numeric(df['PREMIUM TOTAL'], errors='coerce').fillna(0)

    # Assign unique IDs
    df['UNIQUE ID'] = df.apply(
        lambda row: f"{row['FIRST NAME']}_{row['LAST NAME']}_{hash(row['PREMIUM TOTAL']) % 10000}",
        axis=1
    )

    return df



# Function to clean Principal file
def clean_principal_file(df):
    """
    Cleans the Principal test file by:
    - Normalizing column names (case-insensitive, trims whitespace)
    - Splitting 'MEMBER NAME' into 'FIRST NAME' and 'LAST NAME'
    - Removing whitespaces and dashes in names
    - Removing rows with missing names or premiums
    - Converting premiums to numeric values
    - Assigning unique IDs
    """
    # Normalize column names
    df.columns = df.columns.str.strip().str.upper()

    # Ensure required columns exist
    if 'MEMBER NAME' not in df.columns or 'TOTAL PREMIUM' not in df.columns:
        raise KeyError("Principal file is missing required columns: 'MEMBER NAME', 'TOTAL PREMIUM'")

    # Split 'MEMBER NAME' into 'FIRST NAME' and 'LAST NAME'
    name_split = df['MEMBER NAME'].str.split(',', expand=True)
    df['LAST NAME'] = name_split[0].str.strip().str.replace(r"[\s-]", "", regex=True).str.upper()
    df['FIRST NAME'] = name_split[1].str.strip().str.replace(r"[\s-]", "", regex=True).str.upper() if name_split.shape[1] > 1 else None

    # Ensure 'TOTAL PREMIUM' is numeric and clean rows
    df['PRINCIPAL PREMIUM'] = pd.to_numeric(df['TOTAL PREMIUM'], errors='coerce')
    df = df[df['PRINCIPAL PREMIUM'].notna()]  # Remove rows with non-numeric premiums

    # Drop rows with missing names
    df = df[df['FIRST NAME'].notna() & df['LAST NAME'].notna()]

    # Assign unique IDs
    df['UNIQUE ID'] = df.apply(
        lambda row: f"{row['FIRST NAME']}_{row['LAST NAME']}_{hash(row['PRINCIPAL PREMIUM']) % 10000}",
        axis=1
    )

    # Retain only relevant columns
    return df[['UNIQUE ID', 'FIRST NAME', 'LAST NAME', 'PRINCIPAL PREMIUM']]



# Function to compare files
def compare_files(df_ee_cleaned, df_principal_cleaned):
    """Compare EE Nav and Principal files and return a combined DataFrame."""
    # Merge dataframes on 'FIRST NAME' and 'LAST NAME'
    combined = pd.merge(
        df_ee_cleaned,
        df_principal_cleaned,
        on=["FIRST NAME", "LAST NAME"],
        how="outer",
        suffixes=('_ee', '_principal')
    )

    # Add Status and Issue columns
    combined['STATUS'] = 'Valid'
    combined['ISSUE'] = None

    for idx, row in combined.iterrows():
        if pd.isna(row['PREMIUM TOTAL']) and pd.isna(row['PRINCIPAL PREMIUM']):
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Missing Both Premiums'
        elif pd.isna(row['PREMIUM TOTAL']):
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Missing EE Nav Premium'
        elif pd.isna(row['PRINCIPAL PREMIUM']):
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Missing Principal Premium'
        elif row['PREMIUM TOTAL'] != row['PRINCIPAL PREMIUM']:
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Premium Mismatch'

    # Generate unique IDs for each row
    combined['UNIQUE ID'] = combined.apply(
        lambda x: hashlib.sha256(f"{x['FIRST NAME']}{x['LAST NAME']}".encode()).hexdigest()[:8]
        if pd.notna(x['FIRST NAME']) and pd.notna(x['LAST NAME']) else None,
        axis=1
    )

    # Reorder columns for better readability
    combined = combined[['UNIQUE ID', 'FIRST NAME', 'LAST NAME', 'PREMIUM TOTAL', 'PRINCIPAL PREMIUM', 'STATUS', 'ISSUE']]

    # Return the final combined DataFrame
    return combined
