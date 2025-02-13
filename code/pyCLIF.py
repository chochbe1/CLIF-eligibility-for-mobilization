import pandas as pd
import numpy as np
import json
import os
import duckdb
import seaborn as sns
import matplotlib.pyplot as plt
import pytz

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

def standardize_datetime_utc(df, dttm_columns):
    """
    Standardize datetime columns in a DataFrame:
    - Converts to datetime if not already
    - Ensures UTC timezone for all timestamps
    - Removes timezone information after conversion
    - Standardizes format to '%Y-%m-%d %H:%M:%S'
    
    Parameters:
        df (pd.DataFrame): The DataFrame containing the data.
        dttm_columns (str or list): A column name or list of column names to standardize.
    
    Returns:
        pd.DataFrame: DataFrame with standardized datetime columns.
    """
    if isinstance(dttm_columns, str):
        dttm_columns = [dttm_columns]  # Convert single column name to list

    for col in dttm_columns:
        if col in df.columns:
            # Convert to datetime if not already
            df[col] = pd.to_datetime(df[col], errors='coerce')
            # Check if timezone-aware
            if df[col].dt.tz is None:
                df[col] = df[col].dt.tz_localize('UTC', ambiguous='NaT', nonexistent='shift_forward')
            else:
                df[col] = df[col].dt.tz_convert('UTC')
            # Remove timezone and convert to standard format
            df[col] = df[col].dt.tz_convert(None)
        else:
            print(f"Couldn't find {col} column in this df")
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

def map_race_column(df, race_column='race'):
    """
    Function to map race values to simplified categories.

    Args:
    - df (pandas.DataFrame): Input DataFrame containing the race data.
    - race_column (str): The name of the race column. Default is 'race'.

    Returns:
    - pandas.DataFrame: DataFrame with a new column 'race_new' containing the mapped race values.
    """
    # Define the mapping
    race_mapping = {
        'Black or African American': 'Black',
        'White': 'White',
        'Asian': 'Other',
        'American Indian or Alaska Native': 'Other',
        'Native Hawaiian or Other Pacific Islander': 'Other',
        'Other': 'Other',
        'Unknown': 'Other'
    }

    # Apply the mapping to create a new 'race_new' column
    df['race_new'] = df[race_column].map(race_mapping).fillna('Missing')

    return df


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

def apply_outlier_thresholds(df, col_name, min_val, max_val):
    """
    Helper function to clamp column values between min and max thresholds, 
    setting values outside range to NaN.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing the column to process
        col_name (str): Name of the column to apply thresholds to
        min_val (float): Minimum allowed value (inclusive)
        max_val (float): Maximum allowed value (inclusive)
        
    Returns:
        None: Modifies the DataFrame in place by updating the specified column
    """
    df[col_name] = df[col_name].where(df[col_name].between(min_val, 
                                                           max_val, 
                                                           inclusive='both'), 
                                                           np.nan)

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

def stitch_encounters(hospitalization, adt, time_interval=6):
    """
    Stitches together related hospital encounters that occur within a specified time interval of each other.
    
    Args:
        hospitalization (pd.DataFrame): Hospitalization table with required columns
        adt (pd.DataFrame): ADT table with required columns
        time_interval (int, optional): Number of hours between encounters to consider them linked. Defaults to 6.
        
    Returns:
        pd.DataFrame: Stitched encounters with encounter blocks
    """
    hospitalization_filtered = hospitalization[["patient_id","hospitalization_id","admission_dttm","discharge_dttm","age_at_admission"]].copy()
    hospitalization_filtered['admission_dttm'] = pd.to_datetime(hospitalization_filtered['admission_dttm'])
    hospitalization_filtered['discharge_dttm'] = pd.to_datetime(hospitalization_filtered['discharge_dttm'])

    hosp_adt_join = pd.merge(hospitalization_filtered[["patient_id","hospitalization_id","admission_dttm","discharge_dttm"]],
                      adt[["hospitalization_id","in_dttm","out_dttm","location_category","hospital_id"]],
                 on="hospitalization_id",how="left")

    hospital_cat = hosp_adt_join[["hospitalization_id","in_dttm","out_dttm","hospital_id"]]

    # Step 1: Sort by patient_id and admission_dttm
    hospital_block = hosp_adt_join[["patient_id","hospitalization_id","admission_dttm","discharge_dttm"]]
    hospital_block = hospital_block.drop_duplicates()
    hospital_block = hospital_block.sort_values(by=["patient_id", "admission_dttm"]).reset_index(drop=True)
    hospital_block = hospital_block[["patient_id","hospitalization_id","admission_dttm","discharge_dttm"]]

    # Step 2: Calculate time between discharge and next admission
    hospital_block["next_admission_dttm"] = hospital_block.groupby("patient_id")["admission_dttm"].shift(-1)
    hospital_block["discharge_to_next_admission_hrs"] = (
        (hospital_block["next_admission_dttm"] - hospital_block["discharge_dttm"]).dt.total_seconds() / 3600
    )

    # Step 3: Create linked column based on time_interval
    hospital_block["linked6hrs"] = hospital_block["discharge_to_next_admission_hrs"] < time_interval

    # Sort values to ensure correct order
    hospital_block = hospital_block.sort_values(by=["patient_id", "admission_dttm"]).reset_index(drop=True)

    # Initialize encounter_block with row indices + 1
    hospital_block['encounter_block'] = hospital_block.index + 1

    # Iteratively propagate the encounter_block values
    while True:
        shifted = hospital_block['encounter_block'].shift(-1)
        mask = hospital_block['linked6hrs'] & (hospital_block['patient_id'] == hospital_block['patient_id'].shift(-1))
        hospital_block.loc[mask, 'encounter_block'] = shifted[mask]
        if hospital_block['encounter_block'].equals(hospital_block['encounter_block'].bfill()):
            break

    hospital_block['encounter_block'] = hospital_block['encounter_block'].bfill(downcast='int')
    hospital_block = pd.merge(hospital_block,hospital_cat,how="left",on="hospitalization_id")
    hospital_block = hospital_block.sort_values(by=["patient_id", "admission_dttm","in_dttm","out_dttm"]).reset_index(drop=True)
    hospital_block = hospital_block.drop_duplicates()

    hospital_block2 = hospital_block.groupby(['patient_id','encounter_block']).agg(
        admission_dttm=pd.NamedAgg(column='admission_dttm', aggfunc='min'),
        discharge_dttm=pd.NamedAgg(column='discharge_dttm', aggfunc='max'),
        hospital_id = pd.NamedAgg(column='hospital_id', aggfunc='last'),
        list_hospitalization_id=pd.NamedAgg(column='hospitalization_id', aggfunc=lambda x: sorted(x.unique()))
    ).reset_index()

    df = pd.merge(hospital_block[["patient_id",
                                  "hospitalization_id",
                                  "encounter_block"]].drop_duplicates(),
             hosp_adt_join[["hospitalization_id","location_category","in_dttm","out_dttm"]], on="hospitalization_id",how="left")

    df = pd.merge(df,hospital_block2[["encounter_block",
                                      "admission_dttm",
                                      "discharge_dttm",
                                      "hospital_id",
                                     "list_hospitalization_id"]],on="encounter_block",how="left")
    df = df.drop_duplicates(subset=["patient_id","encounter_block","in_dttm","out_dttm","location_category"])
    
    return df

def create_summary_table(
    df, 
    numeric_col, 
    group_by_cols=None
):
    """
    Create a summary table for a given numeric column in a DataFrame, optionally grouped.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing your data.
    numeric_col : str
        The name of the numeric column to summarize (e.g., 'fio2_set').
    group_by_cols : str or list of str, optional
        Column name(s) to group by (e.g., 'device_category', ['device_category','mode_category'], etc.).
        If None, the function provides a single overall summary for the entire df.

    Returns
    -------
    pd.DataFrame
        A DataFrame with columns for each statistic: 
        ['N', 'missing', 'min', 'q25', 'median', 'q75', 'mean', 'max'].
        If group_by_cols is provided, those columns appear first in the output.
    """

    # 1) Define helper functions for quartiles & missing
    def q25(x):
        return x.quantile(0.25)
    q25.__name__ = 'q25'

    def q50(x):
        return x.quantile(0.50)
    q50.__name__ = 'median'

    def q75(x):
        return x.quantile(0.75)
    q75.__name__ = 'q75'

    def missing_count(x):
        return x.isna().sum()
    missing_count.__name__ = 'missing'

    # 2) Build an aggregation dictionary for the chosen numeric_col
    #    It includes N (count of non-null), missing, min, q25, median, q75, mean, max
    agg_dict = {
        numeric_col: [
            'count',       # Non-missing count
            missing_count, # Missing
            'min',
            q25,
            q50,
            q75,
            'mean',
            'max'
        ]
    }

    # 3) Perform groupby if group_by_cols is provided, else do a global summary
    if group_by_cols is not None:
        # Accept a single string or a list of strings
        if isinstance(group_by_cols, str):
            group_by_cols = [group_by_cols]
        summary = df.groupby(group_by_cols).agg(agg_dict)
    else:
        # No grouping => just aggregate the entire DataFrame
        summary = df.agg(agg_dict)

    # 4) The result is a multi-level column index. Flatten it.
    #    We'll get something like:
    #       (numeric_col, 'count'), (numeric_col, '<lambda>'), ...
    #    After flattening, rename the stats to a friendlier label.
    summary.columns = summary.columns.droplevel(0)  # drop the numeric_col level
    # summary now has columns like: ['count','missing','min','q25','median','q75','mean','max']

    # 5) Optionally, reorder columns in a nice sequence
    #    We'll define the exact ordering we want:
    desired_order = ['count','missing','min','q25','median','q75','mean','max']
    # Some columns might have <lambda> instead of 'missing' if the function name wasn't recognized
    # We can do a manual rename if needed.
    rename_map = {}
    for col in summary.columns:
        if '<lambda>' in col:
            rename_map[col] = 'missing'  # rename the lambda to 'missing'
    summary.rename(columns=rename_map, inplace=True)

    # Now reorder columns if they all exist
    existing_cols = [c for c in desired_order if c in summary.columns]
    summary = summary[existing_cols]  # reorder if possible

    # 6) If we had group_by_cols, reset_index so those become DataFrame columns
    if group_by_cols is not None:
        summary = summary.reset_index()

    # 7) Final step: rename for clarity, e.g. rename 'count' -> 'N' if desired
    rename_final = {
        'count': 'N'
    }
    summary.rename(columns=rename_final, inplace=True)

    return summary

helper = load_config()
print(helper)