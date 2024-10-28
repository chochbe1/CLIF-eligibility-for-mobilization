import json
import os
import duckdb
import pandas as pd

def load_config():
    json_path = '../config/config.json'
    
    with open(json_path, 'r') as file:
        config = json.load(file)
    print("Loaded configuration from config.json")
    
    return config

def load_data(table,sample_size=None):
    """
    Load the patient data from a file in the specified directory.

    Returns:
        pd.DataFrame: DataFrame containing patient data.
    """
    file_name = f"{table}.{helper['file_type']}"
    file_path = os.path.join(helper['tables_path'], file_name)
    
    # Load the data based on filetype
    if os.path.exists(file_path):
        if helper['file_type'] == 'csv':
            df = duckdb.read_csv(file_path,sample_size=sample_size).df()
        elif helper['file_type'] == 'parquet':
            df = duckdb.read_parquet(file_path).df()
        else:
            raise ValueError("Unsupported filetype. Only 'csv' and 'parquet' are supported.")
        print(f"Data loaded successfully from {file_path}")
        return df
    else:
        raise FileNotFoundError(f"The file {file_path} does not exist in the specified directory.")
    
def deftime(df):
    
    # Count entries with both hours and minutes
    has_hr_min = df.notna() & (df.dt.hour.notna() & df.dt.minute.notna())
    count_with_hr_min = has_hr_min.sum()

    # Count entries without hours and minutes
    count_without_hr_min = (~has_hr_min).sum()

    # Print the results
    print(f"Count with hours and minutes: {count_with_hr_min}")
    print(f"Count without hours and minutes: {count_without_hr_min}")

def getdttm(df):
    return pd.to_datetime(df).dt.ceil('min')

def qc_check(df, table_name, expected_columns, expected_categories=None):
    """
    Perform QC checks on the dataframe.

    Parameters:
        df (pd.DataFrame): The dataframe to check.
        table_name (str): The name of the table.
        expected_columns (dict): Expected columns and their data types.
        expected_categories (dict): Expected categories for categorical variables.

    Returns:
        qc_report (dict): A report of the QC results.
    """
    qc_report = {'table_name': table_name, 
                 'missing_columns': [], 
                 'wrong_dtypes': {}, 
                 'missingness': {}, 
                 'category_mismatches': {}}

    # Check for missing columns and data types
    for col, expected_dtype in expected_columns.items():
        if col not in df.columns:
            qc_report['missing_columns'].append(col)
        else:
            actual_dtype = str(df[col].dtype)
            if expected_dtype == 'varchar' and not pd.api.types.is_string_dtype(df[col]):
                qc_report['wrong_dtypes'][col] = actual_dtype
            elif expected_dtype == 'datetime' and not pd.api.types.is_datetime64_any_dtype(df[col]):
                qc_report['wrong_dtypes'][col] = actual_dtype
            elif expected_dtype == 'int' and not pd.api.types.is_integer_dtype(df[col]):
                qc_report['wrong_dtypes'][col] = actual_dtype

    # Compute percentage missingness
    for col in expected_columns.keys():
        if col in df.columns:
            missing_percentage = df[col].isna().mean() * 100
            qc_report['missingness'][col] = missing_percentage

    # Check categories
    if expected_categories:
        for col, categories in expected_categories.items():
            if col in df.columns:
                unique_values = df[col].dropna().unique()
                mismatches = set(unique_values) - set(categories)
                if mismatches:
                    qc_report['category_mismatches'][col] = list(mismatches)

    return qc_report

helper = load_config()
print(helper)