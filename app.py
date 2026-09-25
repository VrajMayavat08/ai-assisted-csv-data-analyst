import pandas as pd
import streamlit as st

from src.profiler import profile_dataframe

st.title("AI-Assisted CSV Data Analyst")
st.write("Upload a CSV file to preview your data.")

uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError, OSError):
        st.error("Could not read the CSV file. Please upload a valid UTF-8 CSV file.")
    else:
        profile = profile_dataframe(df)

        st.write("First 10 rows:")
        st.dataframe(df.head(10))

        rows, columns = df.shape
        st.write(f"Rows: {rows}")
        st.write(f"Columns: {columns}")

        st.subheader("Data Quality")
        st.write(f"Duplicate rows: {profile['duplicate_rows']}")
        total_missing = sum(profile["missing_values"].values())
        st.write(f"Total missing values: {total_missing}")

        constant_columns = profile["constant_columns"]
        if constant_columns:
            st.write("Columns with only one unique non-null value: " + ", ".join(constant_columns))
        else:
            st.write("No columns contain only one unique non-null value.")
