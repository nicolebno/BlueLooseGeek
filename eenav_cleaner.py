import pandas as pd

def clean_eenav_file(input_file, output_file="eenav_clean.xlsx"):
    """
    Cleans the Employee Navigator file by summing cost columns into Total Premium,
    and keeping relevant columns.

    Parameters:
        input_file (str): Path to the Employee Navigator input file.
        output_file (str): Path to save the cleaned Employee Navigator file.

    Returns:
        None
    """
    # Load the Excel file
    print(f"Cleaning file: {input_file}")
    df = pd.read_excel(input_file)

    # Sum the cost columns into a new column 'Total Premium'
    df['Total Premium'] = df[['Dental Plan Cost', 'Vision Plan Cost', 'Voluntary Life Total Cost']].sum(axis=1)

    # Keep only relevant columns
    df = df[['Last Name', 'First Name', 'Total Premium']]

    # Save cleaned file
    df.to_excel(output_file, index=False)
    print(f"Cleaned file saved as '{output_file}'")
if __name__ == "__main__":
    clean_eenav_file("eenav_test.xlsx", "eenav_clean.xlsx")
