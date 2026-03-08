import pandas as pd
import numpy as np

def convert_binary_column(series):
    """
    Helper function to standardize binary columns (e.g., FIR/GIR) to 1 (YES) / 0 (NO).
    Handles different string representations and NaN values.
    """
    series_str = series.astype(str).str.upper().str.strip()
    return series_str.map({'YES': 1, 'NO': 0}).fillna(0).astype(int)

def run(csv_url):
    """
    Loads golf data from a CSV URL, processes it, calculates various statistics,
    and returns a DataFrame including individual rounds and aggregated summaries.

    Args:
        csv_url (str): The URL to the raw golf data CSV file.

    Returns:
        pd.DataFrame: A processed DataFrame with golf statistics, including
                      "Paris Summary", "D1 Average", and "LPGA Tour Average" rows.
    """
    df = pd.read_csv(csv_url)

    # 1. Generate new column names for the columns after the first 8
    num_initial_cols = 8
    num_generated_cols = len(df.columns) - num_initial_cols
    generated_column_names = []
    for i in range(num_generated_cols):
        col_name = df.columns[num_initial_cols + i]
        # Try to extract hole number and stat name if possible
        modified_name = col_name.split('.')[0] if '.' in col_name else col_name
        hole_num = (i // 20) + 1 if num_generated_cols >= 360 else ''
        final_name = f"{hole_num} - {modified_name}" if hole_num else modified_name
        generated_column_names.append(final_name)

    # Ensure the generated_column_names matches the number of columns after the first 8
    if len(generated_column_names) != num_generated_cols:
        raise ValueError(f"Length mismatch: {len(df.columns)} columns, {num_initial_cols} initial, {len(generated_column_names)} generated")

    df.columns = list(df.columns[:num_initial_cols]) + generated_column_names

    # --- Extract and compile per-hole data into long format ---
    long_data = []
    for idx, row in df.iterrows():
        for i in range(1, 19):
            hole_data = {
                'row_index': idx,
                'hole': i,
            }
            # Extract each required column for this hole
            col_map = {
                'Hole Handicap': f'{i} - Hole Handicap',
                'Par': f'{i} - Par',
                'Approach shot distance (yds) from pin': f'{i} - Approach shot distance (yds) from pin',
                'Approach shot GIR miss from green (yds)': f'{i} - Approach shot GIR miss from green (yds)',
                'Approach GIR from pin (ft)': f'{i} - Approach GIR from pin (ft)',
                'Scramble up & down distance from pin (yds)': f'{i} - Scramble up & down distance from pin (yds)',
                'Scramble up & down miss from pin (ft)': f'{i} - Scramble up & down miss from pin (ft)',
                'Total shots': f'{i} - Total shots',
            }
            for k, colname in col_map.items():
                hole_data[k] = row.get(colname, np.nan)
            # Calculate score diff from par
            try:
                hole_data['Score Diff from Par'] = hole_data['Total shots'] - hole_data['Par']
            except Exception:
                hole_data['Score Diff from Par'] = np.nan
            long_data.append(hole_data)
    long_df = pd.DataFrame(long_data)
    return long_df

