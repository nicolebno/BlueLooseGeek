import pandas as pd

def compare_files(principal_file, eenav_file, output_file="discrepancies.xlsx"):
    """
    Compare two cleaned Excel files and identify discrepancies based on
    Last Name, First Name, and Total Premium.

    Parameters:
        principal_file (str): Path to the cleaned Principal file.
        eenav_file (str): Path to the cleaned Employee Navigator file.
        output_file (str): Path to save discrepancies.

    Returns:
        None
    """
    # Load the cleaned files
    print(f"Loading files: {principal_file} and {eenav_file}")
    principal_df = pd.read_excel(principal_file)
    eenav_df = pd.read_excel(eenav_file)

    # Merge the DataFrames on Last Name and First Name
    merged = pd.merge(
        principal_df, eenav_df,
        on=['Last Name', 'First Name'],
        how='outer',
        suffixes=('_Principal', '_Eenav')
    )

    # Check for premium matches
    merged['Premium Match'] = merged['Total Premium_Principal'] == merged['Total Premium_Eenav']

    # Filter for discrepancies
    discrepancies = merged[
        ~merged['Premium Match'] |
        merged['Total Premium_Principal'].isna() |
        merged['Total Premium_Eenav'].isna()
    ]

    # Save discrepancies to an Excel file
    discrepancies.to_excel(output_file, index=False)
    print(f"Discrepancy report saved as '{output_file}'")
