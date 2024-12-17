import pandas as pd
import hashlib

# Debugging helper function
def debug_print(message, df=None):
    print(f"[DEBUG] {message}")
    if df is not None:
        print(df.head())
        print(f"Columns: {list(df.columns)}\n")

# Function to validate required columns
def validate_file_columns(df, required_columns, file_name):
    """Ensure the input DataFrame has the required columns."""
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"{file_name} is missing required columns: {missing_columns}")

# Function to clean EE Nav file
def clean_eenav_file(df):
    """
    Cleans the EE Nav file by ensuring relevant columns are present, cleaning data,
    and extracting the required columns for further processing.
    """
    debug_print("Cleaning EE Nav file (raw input):", df)
    validate_file_columns(df, ['FIRST NAME', 'LAST NAME', 'Plan Cost'], "EE Nav File")

    # Ensure 'Plan Cost' is numeric and clean rows
    df['Plan Cost'] = pd.to_numeric(df['Plan Cost'], errors='coerce')  # Convert 'Plan Cost' to numeric
    df = df[df['Plan Cost'].notna()]  # Remove rows with non-numeric 'Plan Cost'

    # Drop rows with missing names
    df = df[df['FIRST NAME'].notna() & df['LAST NAME'].notna()]

    # Assign unique IDs
    df['UNIQUE ID'] = df.apply(
        lambda row: f"{row['FIRST NAME'].strip().lower()}_{row['LAST NAME'].strip().lower()}",
        axis=1
    )

    # Retain only relevant columns
    cleaned_df = df[['UNIQUE ID', 'FIRST NAME', 'LAST NAME', 'Plan Cost']]
    debug_print("EE Nav file cleaned:", cleaned_df)
    return cleaned_df

# Function to clean Principal file
def clean_principal_file(df):
    """
    Cleans the Principal file by normalizing column names,
    splitting 'MEMBER NAME', and ensuring required data integrity.
    """
    debug_print("Cleaning Principal file (raw input):", df)
    # Normalize column names
    df.columns = df.columns.str.strip().str.upper()

    # Ensure required columns exist
    validate_file_columns(df, ['MEMBER NAME', 'TOTAL PREMIUM'], "Principal File")

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
    cleaned_df = df[['UNIQUE ID', 'FIRST NAME', 'LAST NAME', 'PRINCIPAL PREMIUM']]
    debug_print("Principal file cleaned:", cleaned_df)
    return cleaned_df

# Function to compare files
def compare_files(df_ee_cleaned, df_principal_cleaned):
    """
    Compare cleaned EE Nav and Principal files, and return a combined DataFrame.
    """
    debug_print("Comparing files: EE Nav cleaned file:", df_ee_cleaned)
    debug_print("Comparing files: Principal cleaned file:", df_principal_cleaned)

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
        if pd.isna(row['Plan Cost']) and pd.isna(row['PRINCIPAL PREMIUM']):
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Missing Both Premiums'
        elif pd.isna(row['Plan Cost']):
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Missing EE Nav Premium'
        elif pd.isna(row['PRINCIPAL PREMIUM']):
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Missing Principal Premium'
        elif row['Plan Cost'] != row['PRINCIPAL PREMIUM']:
            combined.at[idx, 'STATUS'] = 'Invalid'
            combined.at[idx, 'ISSUE'] = 'Premium Mismatch'

    # Generate unique IDs for each row
    combined['UNIQUE ID'] = combined.apply(
        lambda x: hashlib.sha256(f"{x['FIRST NAME']}{x['LAST NAME']}".encode()).hexdigest()[:8]
        if pd.notna(x['FIRST NAME']) and pd.notna(x['LAST NAME']) else None,
        axis=1
    )

    # Reorder columns for better readability
    combined = combined[['UNIQUE ID', 'FIRST NAME', 'LAST NAME', 'Plan Cost', 'PRINCIPAL PREMIUM', 'STATUS', 'ISSUE']]
    debug_print("Comparison result:", combined)
    return combined

# Main script
def main():
    # Load raw files
    try:
        df_ee_raw = pd.read_excel("ee_nav_file.xlsx")
        df_principal_raw = pd.read_excel("principal_file.xlsx")
    except Exception as e:
        print(f"Error loading files: {e}")
        return

    # Clean files
    try:
        df_ee_cleaned = clean_eenav_file(df_ee_raw)
        df_principal_cleaned = clean_principal_file(df_principal_raw)
    except KeyError as e:
        print(f"Error during cleaning: {e}")
        return
    except Exception as e:
        print(f"Unexpected error during cleaning: {e}")
        return

    # Compare files
    try:
        final_output = compare_files(df_ee_cleaned, df_principal_cleaned)
        final_output.to_csv("comparison_result.csv", index=False)
        print("Comparison completed successfully. Results saved to 'comparison_result.csv'.")
    except Exception as e:
        print(f"Error during comparison: {e}")

if __name__ == "__main__":
    main()

