import pandas as pd
import hashlib
import logging
import re
from fuzzywuzzy import process

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_employee_navigator_file(file_path):
    logging.info(f"Cleaning Employee Navigator file: {file_path}...")
    try:
        df = pd.read_excel(file_path)
        logging.info(f"File '{file_path}' loaded successfully with {len(df)} rows.")

        # Standardize column names
        df.columns = df.columns.str.strip().str.upper().str.replace(" ", "_")

        # Clean and standardize name columns
        if 'LAST_NAME' in df.columns and 'FIRST_NAME' in df.columns:
            df['LAST_NAME'] = df['LAST_NAME'].str.strip().str.upper()
            df['FIRST_NAME'] = df['FIRST_NAME'].str.strip().str.upper()

        # Remove rows with missing critical fields (e.g., name)
        df = df.dropna(subset=['LAST_NAME', 'FIRST_NAME'])

        # Strip all string columns
        str_columns = df.select_dtypes(include=['object']).columns
        df[str_columns] = df[str_columns].apply(lambda col: col.str.strip())

        logging.info(f"Employee Navigator file cleaned successfully.")
        return df

    except Exception as e:
        logging.error(f"Error cleaning Employee Navigator file: {e}")
        raise


def clean_carrier_file(file_path):
    logging.info(f"Cleaning Carrier file: {file_path}...")
    try:
        df = pd.read_excel(file_path)
        logging.info(f"File '{file_path}' loaded successfully with {len(df)} rows.")

        # Standardize column names
        df.columns = df.columns.str.strip().str.upper().str.replace(" ", "_")

        # Standardize Member Name column
        if 'MEMBER_NAME' in df.columns:
            df['MEMBER_NAME'] = df['MEMBER_NAME'].str.strip().str.upper()

        # Ensure numeric columns are properly typed
        numeric_columns = ['AGE', 'VTL_EE_BENEFIT', 'DENTAL_EE_PREMIUM', 'VISION_EE_PREMIUM']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Handle Bill Month (convert to datetime for validation)
        if 'BILL_MONTH' in df.columns:
            df['BILL_MONTH'] = pd.to_datetime(df['BILL_MONTH'], errors='coerce')
            logging.info(f"Unique Bill Month values: {df['BILL_MONTH'].unique()}")

        # Remove rows with missing critical fields (e.g., Member Name)
        df = df.dropna(subset=['MEMBER_NAME'])

        # Strip all string columns
        str_columns = df.select_dtypes(include=['object']).columns
        df[str_columns] = df[str_columns].apply(lambda col: col.str.strip())

        logging.info(f"Carrier file cleaned successfully.")
        return df

    except Exception as e:
        logging.error(f"Error cleaning Carrier file: {e}")
        raise


def verify_and_map_columns(df, column_map):
    """Verifies and maps the columns in the input DataFrame to standardized column names."""
    logging.info("Verifying and mapping columns...")
    mapped_columns = {}
    for standard_col, variations in column_map.items():
        for col in variations:
            if col in df.columns:
                mapped_columns[standard_col] = col
                break
        else:
            logging.warning(f"Missing column for '{standard_col}'. Attempting to infer columns from data.")
    df = df.rename(columns=mapped_columns)
    logging.info("Columns mapped successfully.")
    return df

def load_excel(file_path):
    """Load an Excel file into a Pandas DataFrame with error handling."""
    try:
        df = pd.read_excel(file_path)
        logging.info(f"File '{file_path}' loaded successfully with {len(df)} rows.")
        print(df.head())  # Debugging: Print first few rows of the loaded data
        return df
    except Exception as e:
        logging.error(f"Error loading file '{file_path}': {e}")
        raise

def normalize_name(name):
    """
    Normalize names by:
    - Lowercasing
    - Removing special characters and extra spaces
    - Stripping leading/trailing whitespace
    """
    import unicodedata
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
    name = re.sub(r"[^a-zA-Z\s]", "", name)  # Remove non-alphabetic characters
    name = " ".join(name.lower().split())  # Remove extra spaces and lowercase
    return name

def preprocess_and_match_names(df1, df2, threshold=85):
                 """
                 Use fuzzy matching to identify and handle near-duplicate names.
                 Returns DataFrames with matched and unmatched names.
                 """
                 logging.info("Starting fuzzy matching for name resolution...")
                 df1["Full Name"] = df1["First Name"] + " " + df1["Last Name"]
                 df2["Full Name"] = df2["First Name"] + " " + df2["Last Name"]

                 # Normalize names
                 df1["Normalized Name"] = df1["Full Name"].apply(normalize_name)
                 df2["Normalized Name"] = df2["Full Name"].apply(normalize_name)

                 # Use fuzzy matching for names
                 matched = []
                 for i, name1 in df1["Normalized Name"].items():
                     best_match, score = process.extractOne(name1, df2["Normalized Name"])
                     if score >= threshold:
                         logging.info(f"Match found: {name1} <=> {best_match} (Score: {score})")
                         matched.append((i, df2[df2["Normalized Name"] == best_match].index[0]))

                 # Create a mapping for matches
                 df1["Matched"] = False
                 df2["Matched"] = False
                 for idx1, idx2 in matched:
                     df1.at[idx1, "Matched"] = True
                     df2.at[idx2, "Matched"] = True

                 # Separate matched and unmatched rows
                 unmatched_df1 = df1[~df1["Matched"]].drop(columns=["Matched"])
                 unmatched_df2 = df2[~df2["Matched"]].drop(columns=["Matched"])

                 logging.info("Fuzzy matching completed.")
                 return df1, df2, unmatched_df1, unmatched_df2

def generate_unique_id(full_name):
    """Generates a unique ID by hashing the full name."""
    return hashlib.sha256(full_name.encode('utf-8')).hexdigest()[:8]  # Shorten for display

def assign_unique_ids(ee_nav_cleaned, carrier_cleaned):
    """Assigns unique hashed IDs to employees and resolves near-duplicates using fuzzy matching."""
    logging.info("Assigning unique IDs...")

    # Handle matched and unmatched rows
    ee_nav_cleaned, carrier_cleaned, unmatched_nav, unmatched_carrier = preprocess_and_match_names(
        ee_nav_cleaned, carrier_cleaned
    )

    # Assign unique IDs to the matched DataFrames
    ee_nav_cleaned["Unique ID"] = ee_nav_cleaned["Normalized Name"].apply(generate_unique_id)
    carrier_cleaned["Unique ID"] = carrier_cleaned["Normalized Name"].apply(generate_unique_id)

    # Merge matched datasets
    combined = pd.merge(
        ee_nav_cleaned,
        carrier_cleaned,
        on=["First Name", "Last Name"],
        how="outer",
        suffixes=('_EE', '_Carrier')
    )

    # Ensure a consistent Unique ID column
    combined["Unique ID"] = combined.apply(
        lambda row: row["Unique ID_EE"] if pd.notna(row["Unique ID_EE"]) else row["Unique ID_Carrier"],
        axis=1
    )
    combined = combined.drop(columns=["Unique ID_EE", "Unique ID_Carrier"])

    if combined.empty:
        logging.warning("Combined DataFrame is empty after merging.")

    # Log unmatched rows for debugging purposes
    logging.info(f"Unmatched rows in Employee Navigator: {len(unmatched_nav)}")
    logging.info(f"Unmatched rows in Carrier file: {len(unmatched_carrier)}")

    logging.info("Unique IDs assigned successfully.")
    return combined


def compare_files(combined):
    """Compares the cleaned files and identifies the final status."""
    logging.info("Comparing files...")

    def calculate_status(row):
        if pd.isna(row["EE Nav Premium"]) and not pd.isna(row["Carrier Premium"]):
            return "Check Eligibility Status"
        elif pd.isna(row["Carrier Premium"]) and not pd.isna(row["EE Nav Premium"]):
            return "Check Enrollment Status"
        elif not pd.isna(row["EE Nav Premium"]) and not pd.isna(row["Carrier Premium"]):
            return "Valid"
        return "Unknown"

    combined["Status"] = combined.apply(calculate_status, axis=1)
    logging.info("Comparison completed. Status column added successfully.")
    return combined


def save_discrepancy_report(combined, output_file):
    """Saves the discrepancies report to an Excel file."""
    try:
        combined.to_excel(output_file, index=False)
        logging.info(f"Discrepancy report saved to {output_file}")
    except Exception as e:
        logging.error(f"Failed to save discrepancy report: {e}")


def main():
    # Define your input and output file names
    ee_nav_file = "eenav_test.xlsx"
    carrier_file = "principal_test.xlsx"
    output_file = "discrepancies.xlsx"

    try:
        # Clean and standardize the input files
        ee_nav_cleaned = clean_employee_navigator_file(ee_nav_file)
        carrier_cleaned = clean_carrier_file(carrier_file)

        # Match and assign unique IDs
        combined = assign_unique_ids(ee_nav_cleaned, carrier_cleaned)

        # Compare the files and add status
        discrepancies = compare_files(combined)

        # Save the final discrepancies report
        save_discrepancy_report(discrepancies, output_file)
        logging.info("Process completed successfully.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
