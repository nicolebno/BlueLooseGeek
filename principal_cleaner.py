import pandas as pd

def clean_principal_file(input_file, output_file="principal_clean.xlsx"):
    """
    Cleans the Principal file by splitting Member Name into Last Name and First Name,
    and keeping relevant columns.

    Parameters:
        input_file (str): Path to the Principal input file.
        output_file (str): Path to save the cleaned Principal file.

    Returns:
        None
    """
    # Load the Excel file
    print(f"Cleaning file: {input_file}")
    df = pd.read_excel(input_file)

    # Split 'Member Name' into 'Last Name' and 'First Name'
    df[['Last Name', 'First Name']] = df['Member Name'].str.split(', ', expand=True)

    # Keep only relevant columns
    df = df[['Last Name', 'First Name', 'Total Premium']]

    # Save cleaned file
    df.to_excel(output_file, index=False)
    print(f"Cleaned file saved as '{output_file}'")
