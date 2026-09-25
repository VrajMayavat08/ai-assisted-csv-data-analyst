import pandas as pd
import streamlit as st

st.title("AI-Assisted CSV Data Analyst")
st.write("Upload a CSV file to preview your data.")

uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError, OSError):
        st.error("Could not read the CSV file. Please upload a valid UTF-8 CSV file.")
    else:
        st.write("First 10 rows:")
        st.dataframe(df.head(10))

        rows, columns = df.shape
        st.write(f"Rows: {rows}")
        st.write(f"Columns: {columns}")
