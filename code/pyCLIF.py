import pandas as pd
import numpy as np
import json
import os
import duckdb
import seaborn as sns
import matplotlib.pyplot as plt

conn = duckdb.connect(database=':memory:')

def load_config():
    json_path = '../config/config.json'
    
    with open(json_path, 'r') as file:
        config = json.load(file)
    print("Loaded configuration from config.json")
    
    return config

def load_data(table, sample_size=None, columns=None, filters=None):
    """
    Load data from a file in the specified directory with the option to select specific columns and apply filters.

    Parameters:
        table (str): The name of the table to load.
        sample_size (int, optional): Number of rows to load.
        columns (list of str, optional): List of column names to load.
        filters (dict, optional): Dictionary of filters to apply.

    Returns:
        pd.DataFrame: DataFrame containing the requested data.
    """
    # Determine the file path based on the directory and filetype
    file_name = f"{table}.{helper['file_type']}"
    file_path = os.path.join(helper['tables_path'], file_name)
    
    # Load the data based on filetype
    if os.path.exists(file_path):
        if helper['file_type'] == 'csv':
            # For CSV, we can use DuckDB to read specific columns and apply filters efficiently
            con = duckdb.connect()
            # Build the SELECT clause
            select_clause = "*" if not columns else ", ".join(columns)
            # Start building the query
            query = f"SELECT {select_clause} FROM read_csv_auto('{file_path}')"
            # Apply filters
            if filters:
                filter_clauses = []
                for column, values in filters.items():
                    if isinstance(values, list):
                        # Escape single quotes and wrap values in quotes
                        values_list = ', '.join(["'" + str(value).replace("'", "''") + "'" for value in values])
                        filter_clauses.append(f"{column} IN ({values_list})")
                    else:
                        value = str(values).replace("'", "''")
                        filter_clauses.append(f"{column} = '{value}'")
                if filter_clauses:
                    query += " WHERE " + " AND ".join(filter_clauses)
            # Apply sample size limit
            if sample_size:
                query += f" LIMIT {sample_size}"
            # Execute the query and fetch the data
            df = con.execute(query).fetchdf()
            con.close()
        elif helper['file_type'] == 'parquet':
            # For Parquet, use DuckDB to read specific columns and apply filters efficiently
            con = duckdb.connect()
            # Build the SELECT clause
            select_clause = "*" if not columns else ", ".join(columns)
            # Start building the query
            query = f"SELECT {select_clause} FROM parquet_scan('{file_path}')"
            # Apply filters
            if filters:
                filter_clauses = []
                for column, values in filters.items():
                    if isinstance(values, list):
                        # Escape single quotes and wrap values in quotes
                        values_list = ', '.join(["'" + str(value).replace("'", "''") + "'" for value in values])
                        filter_clauses.append(f"{column} IN ({values_list})")
                    else:
                        value = str(values).replace("'", "''")
                        filter_clauses.append(f"{column} = '{value}'")
                if filter_clauses:
                    query += " WHERE " + " AND ".join(filter_clauses)
            # Apply sample size limit
            if sample_size:
                query += f" LIMIT {sample_size}"
            # Execute the query and fetch the data
            df = con.execute(query).fetchdf()
            con.close()
        else:
            raise ValueError("Unsupported filetype. Only 'csv' and 'parquet' are supported.")
        print(f"Data loaded successfully from {file_path}")
        return df
    else:
        raise FileNotFoundError(f"The file {file_path} does not exist in the specified directory.")

def standardize_datetime(df):
    """
    Ensure that all *_dttm variables are in the correct format.
    Convert all datetime columns to a specific precision and remove timezone
    Parameters:
        DataFrame: DataFrame containing the data.
    Returns:
        DataFrame: DataFrame containing the data.
    """
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            # Here converting to 'datetime64[ns]' for uniformity and removing timezone with 'tz_convert(None)'
            df[col] = df[col].dt.tz_convert(None) if df[col].dt.tz is not None else df[col]
    return df

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

def count_unique_encounters(df, encounter_column='hospitalization_id'):
    """
    Counts the unique encounters in a DataFrame.
    
    Parameters:
    df (DataFrame): The DataFrame to analyze.
    encounter_column (str): The name of the column containing encounter IDs (default is 'hospitalization_id').
    
    Returns:
    int: The number of unique encounters.
    """
    return df[encounter_column].nunique()

def generate_facetgrid_histograms(data, category_column, value_column):
    """
    Generate histograms using seaborn's FacetGrid.

    Parameters:
        data (DataFrame): DataFrame containing the data.
        category_column (str): Name of the column containing categories.
        value_column (str): Name of the column containing values.

    Returns:
        FacetGrid: Seaborn FacetGrid object containing the generated histograms.
    """
    # Create a FacetGrid
    g = sns.FacetGrid(data, col=category_column, col_wrap=6, sharex=False, sharey=False)
    g.map(sns.histplot, value_column, bins=30, color='blue', edgecolor='black')

    # Set titles and labels
    g.set_titles('{col_name}')
    g.set_axis_labels(value_column, 'Frequency')

    # Adjust layout
    plt.subplots_adjust(top=0.9)
    g.fig.suptitle(f'Histograms of {value_column} by {category_column}', fontsize=16)

    return g

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

def remove_duplicates(df, columns, df_name):
    """
    Checks for and removes duplicate rows in a DataFrame based on the combination of specified columns.

    Parameters:
        df (DataFrame): The DataFrame to clean.
        columns (list): A list of columns to use for identifying duplicates.
        df_name (str): The name of the DataFrame (for display purposes).

    Returns:
        DataFrame: The DataFrame with duplicates removed.
    """
    # Check for duplicates based on the combination of specified columns
    initial_count = len(df)
    duplicates = df[df.duplicated(subset=columns, keep=False)]
    
    print(f"Processing DataFrame: {df_name}")
    
    if not duplicates.empty:
        num_duplicates = len(duplicates)
        print(f"Found {num_duplicates} duplicate rows based on columns: {columns}")
        
        # Drop duplicates, keeping the first occurrence
        df_cleaned = df.drop_duplicates(subset=columns, keep='first')
        final_count = len(df_cleaned)
        duplicates_dropped = initial_count - final_count
        
        print(f"Dropped {duplicates_dropped} duplicate rows. New DataFrame has {final_count} rows.")
    else:
        df_cleaned = df
        print(f"No duplicates found based on columns: {columns}.")
    
    return df_cleaned

def process_resp_support(df):
    """
    Process the respiratory support data using waterfall logic.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing respiratory support data.
        
    Returns:
        pd.DataFrame: Processed DataFrame with filled values.
    """
    print("Initiating waterfall processing...")
    
    # Ensure 'recorded_dttm' is in datetime format
    df['recorded_dttm'] = pd.to_datetime(df['recorded_dttm'])
    
    # Convert categories to lowercase to standardize
    df['device_category'] = df['device_category'].str.lower()
    df['mode_category'] = df['mode_category'].str.lower()
    df['device_name'] = df['device_name'].str.lower()
    df['mode_name'] = df['mode_name'].str.lower()
    
    # # Fix out-of-range values
    # print("Fixing out-of-range values for 'fio2_set', 'peep_set', and 'resp_rate_set'...")
    # df['fio2_set'] = df['fio2_set'].where(df['fio2_set'].between(0.21, 1), np.nan)
    # df['peep_set'] = df['peep_set'].where(df['peep_set'].between(0, 50), np.nan)
    # df['resp_rate_set'] = df['resp_rate_set'].where(df['resp_rate_set'].between(0, 60), np.nan)
    
    # Create 'recorded_date' and 'recorded_hour'
    print('Creating recorded_date and recorded_hour...')
    df['recorded_date'] = df['recorded_dttm'].dt.date
    df['recorded_hour'] = df['recorded_dttm'].dt.hour
    
    # Sort data
    print("Sorting data by 'hospitalization_id' and 'recorded_dttm'...")
    df.sort_values(by=['hospitalization_id', 'recorded_dttm'], inplace=True)
    
    # Fix missing 'device_category' and 'device_name' based on 'mode_category'
    print("Fixing missing 'device_category' and 'device_name' based on 'mode_category'...")
    mask = (
        df['device_category'].isna() &
        df['device_name'].isna() &
        df['mode_category'].str.contains('assist control-volume control|simv|pressure control', case=False, na=False)
    )
    df.loc[mask, 'device_category'] = 'imv'
    df.loc[mask, 'device_name'] = 'mechanical ventilator'
    
    # Fix 'device_category' and 'device_name' based on neighboring records
    print("Fixing 'device_category' and 'device_name' based on neighboring records...")
    # Create shifted columns once to avoid multiple shifts
    df['device_category_shifted'] = df['device_category'].shift()
    df['device_category_shifted_neg'] = df['device_category'].shift(-1)
    
    condition_prev = (
        df['device_category'].isna() &
        (df['device_category_shifted'] == 'imv') &
        df['resp_rate_set'].gt(1) &
        df['peep_set'].gt(1)
    )
    condition_next = (
        df['device_category'].isna() &
        (df['device_category_shifted_neg'] == 'imv') &
        df['resp_rate_set'].gt(1) &
        df['peep_set'].gt(1)
    )
    
    condition = condition_prev | condition_next
    df.loc[condition, 'device_category'] = 'imv'
    df.loc[condition, 'device_name'] = 'mechanical ventilator'
    
    # Drop the temporary shifted columns
    df.drop(['device_category_shifted', 'device_category_shifted_neg'], axis=1, inplace=True)
    
    # Handle duplicates and missing data
    print("Handling duplicates and removing rows with all key variables missing...")
    df['n'] = df.groupby(['hospitalization_id', 'recorded_dttm'])['recorded_dttm'].transform('size')
    df = df[~((df['n'] > 1) & (df['device_category'] == 'nippv'))]
    df = df[~((df['n'] > 1) & (df['device_category'].isna()))]
    subset_vars = ['device_category', 'device_name', 'mode_category', 'mode_name', 'fio2_set']
    df.dropna(subset=subset_vars, how='all', inplace=True)
    df.drop_duplicates(subset=['hospitalization_id', 'recorded_dttm'], keep='first', inplace=True)
    df.drop('n', axis=1, inplace=True)  # Drop 'n' as it's no longer needed
    
    # Fill forward 'device_category' within each hospitalization
    print("Filling forward 'device_category' within each hospitalization...")
    df['device_category'] = df.groupby('hospitalization_id')['device_category'].ffill()
    
    # Create 'device_cat_id' based on changes in 'device_category'
    print("Creating 'device_cat_id' to track changes in 'device_category'...")
    df['device_cat_f'] = df['device_category'].fillna('missing').astype('category').cat.codes
    df['device_cat_change'] = df['device_cat_f'] != df.groupby('hospitalization_id')['device_cat_f'].shift()
    df['device_cat_change'] = df['device_cat_change'].astype(int)
    df['device_cat_id'] = df.groupby('hospitalization_id')['device_cat_change'].cumsum()
    df.drop('device_cat_change', axis=1, inplace=True)
    
    # Fill 'device_name' within 'device_cat_id'
    print("Filling 'device_name' within each 'device_cat_id'...")
    df['device_name'] = df.groupby(['hospitalization_id', 'device_cat_id'])['device_name'].ffill().bfill()
    
    # Create 'device_id' based on changes in 'device_name'
    print("Creating 'device_id' to track changes in 'device_name'...")
    df['device_name_f'] = df['device_name'].fillna('missing').astype('category').cat.codes
    df['device_name_change'] = df['device_name_f'] != df.groupby('hospitalization_id')['device_name_f'].shift()
    df['device_name_change'] = df['device_name_change'].astype(int)
    df['device_id'] = df.groupby('hospitalization_id')['device_name_change'].cumsum()
    df.drop('device_name_change', axis=1, inplace=True)
    
    # Fill 'mode_category' within 'device_id'
    print("Filling 'mode_category' within each 'device_id'...")
    df['mode_category'] = df.groupby(['hospitalization_id', 'device_id'])['mode_category'].ffill().bfill()
    
    # Create 'mode_cat_id' based on changes in 'mode_category'
    print("Creating 'mode_cat_id' to track changes in 'mode_category'...")
    df['mode_cat_f'] = df['mode_category'].fillna('missing').astype('category').cat.codes
    df['mode_cat_change'] = df['mode_cat_f'] != df.groupby(['hospitalization_id', 'device_id'])['mode_cat_f'].shift()
    df['mode_cat_change'] = df['mode_cat_change'].astype(int)
    df['mode_cat_id'] = df.groupby(['hospitalization_id', 'device_id'])['mode_cat_change'].cumsum()
    df.drop('mode_cat_change', axis=1, inplace=True)
    
    # Fill 'mode_name' within 'mode_cat_id'
    print("Filling 'mode_name' within each 'mode_cat_id'...")
    df['mode_name'] = df.groupby(['hospitalization_id', 'mode_cat_id'])['mode_name'].ffill().bfill()
    
    # Create 'mode_name_id' based on changes in 'mode_name'
    print("Creating 'mode_name_id' to track changes in 'mode_name'...")
    df['mode_name_f'] = df['mode_name'].fillna('missing').astype('category').cat.codes
    df['mode_name_change'] = df['mode_name_f'] != df.groupby(['hospitalization_id', 'mode_cat_id'])['mode_name_f'].shift()
    df['mode_name_change'] = df['mode_name_change'].astype(int)
    df['mode_name_id'] = df.groupby(['hospitalization_id', 'mode_cat_id'])['mode_name_change'].cumsum()
    df.drop('mode_name_change', axis=1, inplace=True)
    
    # Adjust 'fio2_set' for 'room air' device_category
    print("Adjusting 'fio2_set' for 'room air' device_category...")
    df['fio2_set'] = np.where(df['fio2_set'].isna() & (df['device_category'] == 'room air'), 0.21, df['fio2_set'])
    
    # Adjust 'mode_category' for 't-piece' devices
    print("Adjusting 'mode_category' for 't-piece' devices...")
    mask_tpiece = (
        df['mode_category'].isna() &
        df['device_name'].str.contains('t-piece', case=False, na=False)
    )
    df.loc[mask_tpiece, 'mode_category'] = 'blow by'
    
    # Fill remaining variables within 'mode_name_id'
    print("Filling remaining variables within each 'mode_name_id'...")
    fill_vars = [
        'fio2_set', 'lpm_set', 'peep_set', 'resp_rate_set',
        'resp_rate_obs'
    ]
    df[fill_vars] = df.groupby(['hospitalization_id', 'mode_name_id'])[fill_vars].transform(lambda x: x.ffill().bfill())
    
    # Fill 'tracheostomy' forward within each hospitalization
    print("Filling 'tracheostomy' forward within each hospitalization...")
    df['tracheostomy'] = df.groupby('hospitalization_id')['tracheostomy'].ffill()
    
    # Remove duplicates
    print("Removing duplicates...")
    df.drop_duplicates(inplace=True)
    
    # Select relevant columns
    columns_to_keep = [
        'hospitalization_id', 'recorded_dttm', 'recorded_date', 'recorded_hour',
        'device_category', 'device_name', 'mode_category', 'mode_name',
        'device_cat_id', 'device_id', 'mode_cat_id', 'mode_name_id',
        'fio2_set', 'lpm_set', 'peep_set', 'resp_rate_set',
        'tracheostomy', 'resp_rate_obs'
    ]
    # Ensure columns exist before selecting
    existing_columns = [col for col in columns_to_keep if col in df.columns]
    df = df[existing_columns]
    
    print("Waterfall processing completed.")
    return df


helper = load_config()
print(helper)