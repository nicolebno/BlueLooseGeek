import streamlit as st
import pandas as pd

st.title("Premium Comparison App")

# File upload
uploaded_file_ee = st.file_uploader("Upload EE Nav File", type=["csv", "xlsx"])
uploaded_file_principal = st.file_uploader("Upload Principal File", type=["csv", "xlsx"])

if st.button("Process Files"):
    if uploaded_file_ee and uploaded_file_principal:
        # Load files into pandas
        df_ee = pd.read_excel(uploaded_file_ee) if uploaded_file_ee.name.endswith("xlsx") else pd.read_csv(uploaded_file_ee)
        df_principal = pd.read_excel(uploaded_file_principal) if uploaded_file_principal.name.endswith("xlsx") else pd.read_csv(uploaded_file_principal)
        
        # Process files (replace with your processing logic)
        st.write("Files processed successfully!")
        
        # Example results
        data = {"Unique ID": ["1a2b", "3c4d"], "Status": ["Valid", "Invalid"]}
        results_df = pd.DataFrame(data)
        
        # Display results
        st.dataframe(results_df)
        
        # Download button
        csv = results_df.to_csv(index=False)
        st.download_button(label="Download Results", data=csv, file_name="results.csv", mime="text/csv")
    else:
        st.error("Please upload both files.")
