def profile_dataframe(df):
    """Return basic statistics for a pandas DataFrame.

    Unique value counts exclude null values. A constant column contains
    exactly one unique non-null value, so all-null columns are excluded.
    """
    unique_counts = df.nunique(dropna=True)

    return {
        "num_rows": df.shape[0],
        "num_columns": df.shape[1],
        "column_names": df.columns.tolist(),
        "data_types": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isna().sum().to_dict(),
        "unique_values": unique_counts.to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "constant_columns": unique_counts[unique_counts == 1].index.tolist(),
    }
