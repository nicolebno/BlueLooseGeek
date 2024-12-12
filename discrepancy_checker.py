import os
import pandas as pd

# Debug: List files in the directory
print("Current directory files:")
print(os.listdir("."))  # Ensure files are visible

# File names (ensure these match exactly)
file1 = "Book20 (1).xlsx"
file2 = "Book20 (2).xlsx"

# Load the Excel files
try:
    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)
    print("Files loaded successfully!")
except FileNotFoundError as e:
    print(f"File not found: {e}")
    exit()

# Debug: Print loaded data
print("\nDataFrame 1 (Book20 (1).xlsx):")
print(df1.head())
print("\nDataFrame 2 (Book20 (2).xlsx):")
print(df2.head())

# Align columns
df1 = df1.reindex(columns=df2.columns).reset_index(drop=True)
df2 = df2.reindex(columns=df1.columns).reset_index(drop=True)

# Debug: Verify alignment
print("\nAligned DataFrame 1:")
print(df1.head())
print("\nAligned DataFrame 2:")
print(df2.head())

# Compare DataFrames
discrepancies = df1.compare(df2, keep_shape=True, keep_equal=False)

# Debug: Print discrepancies
print("\nDiscrepancies DataFrame:")
print(discrepancies)

# Handle discrepancies
if discrepancies.empty:
    print("\nNo discrepancies found. The files might be identical.")
else:
    print("\nDiscrepancies found:")
    print(discrepancies)

    # Flatten the MultiIndex using stack()
    flattened = discrepancies.stack().reset_index()

    # Assign dynamic column names
    num_columns = len(flattened.columns)
    column_names = ["Row", "Column"] + [f"File{i}_Value" for i in range(1, num_columns - 1)]
    flattened.columns = column_names

    # Debug: Check the flattened discrepancies DataFrame
    print("\nFlattened and Cleaned Discrepancies DataFrame:")
    print(flattened.head())

    # Save to Excel
    flattened.to_excel("discrepancies.xlsx", index=False)
    print("\nDiscrepancies saved to discrepancies.xlsx")