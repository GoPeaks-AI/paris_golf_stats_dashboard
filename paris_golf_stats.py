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

    # 1. Generate new column names for the 18 holes
    generated_column_names = []
    for i in range(1, 19):
        start_index = i * 20 - 12
        end_index = i * 20 + 8
        current_cols = df.columns[start_index:min(end_index, len(df.columns))]

        for col_name in current_cols:
            modified_name = col_name.split('.')[0] if '.' in col_name else col_name
            final_name = f"{i} - {modified_name}"
            generated_column_names.append(final_name)

    # Assign new column names
    df.columns = list(df.columns[:8]) + generated_column_names

    # Initialize new_df for individual round statistics
    # This `new_df_rounds` will contain only the raw golf round data before summaries are added.
    new_df_rounds = pd.DataFrame()
    new_df_rounds["Date"] = df["Date"]
    new_df_rounds["Course"] = df["Course"]

    # --- New columns: Approach and Up & Down stats ---
    # Helper to get only columns that exist, fill missing with NaN
    def safe_mean(df, col_list):
        cols_present = [c for c in col_list if c in df.columns]
        if not cols_present:
            return pd.Series([np.nan] * len(df))
        temp = df[cols_present].apply(pd.to_numeric, errors='coerce')
        # Add missing columns as NaN
        for c in col_list:
            if c not in temp.columns:
                temp[c] = np.nan
        temp = temp[col_list]  # preserve order
        return temp.mean(axis=1)

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

    # 1. Generate new column names for the 18 holes
    generated_column_names = []
    for i in range(1, 19):
        start_index = i * 20 - 12
        end_index = i * 20 + 8
        current_cols = df.columns[start_index:min(end_index, len(df.columns))]

        for col_name in current_cols:
            modified_name = col_name.split('.')[0] if '.' in col_name else col_name
            final_name = f"{i} - {modified_name}"
            generated_column_names.append(final_name)

    # Assign new column names
    df.columns = list(df.columns[:8]) + generated_column_names

    # Initialize new_df for individual round statistics
    # This `new_df_rounds` will contain only the raw golf round data before summaries are added.
    new_df_rounds = pd.DataFrame()
    new_df_rounds["Date"] = df["Date"]
    new_df_rounds["Course"] = df["Course"]

    # Calculate Total Yds by summing 'Distance in yards' for all 18 holes
    distance_cols = [f"{i} - Distance in yards" for i in range(1, 19)]
    new_df_rounds["Total Yds"] = df[distance_cols].sum(axis=1)

    new_df_rounds["Slope Rating"] = df["Course par/slope"]

    # Score: Sum of 'Total shots' for each hole
    total_shots_cols = [f"{i} - Total shots" for i in range(1, 19)]
    new_df_rounds["Score"] = df[total_shots_cols].sum(axis=1)

    # Total Par: Sum of 'Par' for each hole
    par_cols = [f"{i} - Par" for i in range(1, 19)]
    total_par = df[par_cols].sum(axis=1)

    # 1. Update 'Avg Diff from Par/Hole' to 'Diff from Par'
    new_df_rounds["Diff from Par"] = new_df_rounds["Score"] - total_par

    # 2. Add 'Par 3 - Diff per Hole', 'Par 4 - Diff per Hole', and 'Par 5 - Diff per Hole' columns
    par3_diff_per_round = []
    par4_diff_per_round = []
    par5_diff_per_round = []

    for index, row in df.iterrows():
        current_round_par3_diffs = []
        current_round_par4_diffs = []
        current_round_par5_diffs = []

        for i in range(1, 19):
            hole_par = row[f"{i} - Par"]
            hole_shots = row[f"{i} - Total shots"]
            diff = hole_shots - hole_par

            if hole_par == 3:
                current_round_par3_diffs.append(diff)
            elif hole_par == 4:
                current_round_par4_diffs.append(diff)
            elif hole_par == 5:
                current_round_par5_diffs.append(diff)

        par3_diff_per_round.append(np.mean(current_round_par3_diffs) if current_round_par3_diffs else np.nan)
        par4_diff_per_round.append(np.mean(current_round_par4_diffs) if current_round_par4_diffs else np.nan)
        par5_diff_per_round.append(np.mean(current_round_par5_diffs) if current_round_par5_diffs else np.nan)

    new_df_rounds["Par 3 - Diff per Hole"] = par3_diff_per_round
    new_df_rounds["Par 4 - Diff per Hole"] = par4_diff_per_round
    new_df_rounds["Par 5 - Diff per Hole"] = par5_diff_per_round

    # FIR %: Sum of 'Tee shot FIR' for each hole, converted to 1/0
    fir_cols = [f"{i} - Tee shot FIR" for i in range(1, 19)]
    fir_sum = df[fir_cols].apply(convert_binary_column).sum(axis=1)
    new_df_rounds["FIR %"] = (fir_sum / 18) * 100

    # GIR %: Sum of 'Approach shot GIR' for each hole, converted to 1/0
    gir_cols = [f"{i} - Approach shot GIR" for i in range(1, 19)]
    gir_sum = df[gir_cols].apply(convert_binary_column).sum(axis=1)
    new_df_rounds["GIR %"] = (gir_sum / 18) * 100

    # Avg GIR Green Miss (Yd): Mean of 'Approach shot GIR miss from green (yds)'
    avg_gir_green_miss_cols = [f"{i} - Approach shot GIR miss from green (yds)" for i in range(1, 19)]
    new_df_rounds["Avg GIR Green Miss (Yd)"] = df[avg_gir_green_miss_cols].mean(axis=1)

    # Avg GIR Pin Miss (ft): Mean of 'Approach GIR from pin (ft)'
    avg_gir_pin_miss_cols = [f"{i} - Approach GIR from pin (ft)" for i in range(1, 19)]
    # Ensure all columns are numeric for mean calculation
    new_df_rounds["Avg GIR Pin Miss (ft)"] = df[avg_gir_pin_miss_cols].apply(pd.to_numeric, errors='coerce').mean(axis=1)

    # Total Putts: Sum of all 'Putting stats' categories for each hole
    putting_stats_types = [
        "[>= 30 ft]", "[20-30 ft]", "[10-20 ft]", "[5-10 ft]", "[<= 5 ft]",
    ]
    total_putts_cols = []
    for i in range(1, 19):
        for pt_type in putting_stats_types:
            total_putts_cols.append(f"{i} - Putting stats {pt_type}")

    # Summing all putting stats for all holes, treating missing values as 0 putts
    total_putts = df[total_putts_cols].fillna(0).sum(axis=1)

    # 3. Rename 'Total putts/Hole' to 'Total Putts per Hole'
    new_df_rounds["Total Putts per Hole"] = total_putts / 18

    # 4. New logic for cumulative putting statistics by distance (excluding zeros for mean)
    putt_ranges_definitions = {
        "Total Putts per Hole <= 5ft": { "ranges_to_sum": ["[<= 5 ft]"], "check_key": "[<= 5 ft]" },
        "Total Putts per Hole 5-10ft": { "ranges_to_sum": ["[<= 5 ft]", "[5-10 ft]"], "check_key": "[5-10 ft]" },
        "Total Putts per Hole 10-20ft": { "ranges_to_sum": ["[<= 5 ft]", "[5-10 ft]", "[10-20 ft]"], "check_key": "[10-20 ft]" },
        "Total Putts per Hole 20-30ft": { "ranges_to_sum": ["[<= 5 ft]", "[5-10 ft]", "[10-20 ft]", "[20-30 ft]"], "check_key": "[20-30 ft]" },
        "Total Putts per Hole >= 30ft": { "ranges_to_sum": ["[<= 5 ft]", "[5-10 ft]", "[10-20 ft]", "[20-30 ft]", "[>= 30 ft]"], "check_key": "[>= 30 ft]" }
    }

    for new_col_name, defs in putt_ranges_definitions.items():
        ranges_to_sum = defs['ranges_to_sum']
        check_key = defs['check_key'] # The key for the specific range to check for zero putts

        new_df_rounds[new_col_name] = np.nan
        for idx, row in df.iterrows():
            cumulative_putts_per_hole_for_round = []
            for i in range(1, 19): # Iterate through each hole
                # Get the actual putt count for the 'check_key' range for this hole
                check_col_name = f"{i} - Putting stats {check_key}"
                check_value = row.get(check_col_name, 0)

                if check_value > 0: # Only calculate cumulative if putts from 'this range' are non-zero
                    hole_cumulative_putts = 0
                    for r_type in ranges_to_sum:
                        col_name_for_hole_range = f"{i} - Putting stats {r_type}"
                        val = row[col_name_for_hole_range] if pd.notna(row[col_name_for_hole_range]) else 0
                        hole_cumulative_putts += val
                    cumulative_putts_per_hole_for_round.append(hole_cumulative_putts)

            # Calculate the average only from the included hole cumulative putts
            if len(cumulative_putts_per_hole_for_round) > 0:
                new_df_rounds.loc[idx, new_col_name] = np.mean(cumulative_putts_per_hole_for_round)
            else:
                new_df_rounds.loc[idx, new_col_name] = 0.0 # If no holes met the condition, or all putts are zero, set to 0.0

    # Up and Down %: Percentage of holes where GIR was missed but player made 1 shot to green, followed by 1 putt to the hole
    total_scramble_opportunities = pd.Series(0, index=df.index)
    total_successful_up_and_downs = pd.Series(0, index=df.index)

    for i in range(1, 19):
        gir_missed_for_hole = (convert_binary_column(df[f'{i} - Approach shot GIR']) == 0)
        total_scramble_opportunities = total_scramble_opportunities + gir_missed_for_hole.astype(int)

        putting_cols_for_current_hole = [f"{i} - Putting stats {pt_type}" for pt_type in putting_stats_types]
        total_putts_for_current_hole = df[putting_cols_for_current_hole].fillna(0).sum(axis=1)

        successful_up_down_for_hole = (gir_missed_for_hole) & (total_putts_for_current_hole <= 1)
        total_successful_up_and_downs = total_successful_up_and_downs + successful_up_down_for_hole.astype(int)

    new_df_rounds["Up and Down %"] = np.where(
        total_scramble_opportunities > 0,
        (total_successful_up_and_downs / total_scramble_opportunities) * 100,
        0
    )

    # Add Avg Approach Distance (yds) from Pin (original: 'Approach shot distance (yds) from pin')
    approach_dist_cols = [f"{i} - Approach shot distance (yds) from pin" for i in range(1, 19)]
    if all(col in df.columns for col in approach_dist_cols):
        new_df_rounds["Avg Approach Distance (yds) from Pin"] = df[approach_dist_cols].apply(pd.to_numeric, errors='coerce').mean(axis=1)
    else:
        new_df_rounds["Avg Approach Distance (yds) from Pin"] = np.nan

    # AddAvg Up & Down Distance from Pin (yds) (original: 'Scramble up & down distance from pin (yds)')
    updown_dist_cols = [f"{i} - Scramble up & down distance from pin (yds)" for i in range(1, 19)]
    if all(col in df.columns for col in updown_dist_cols):
        new_df_rounds["Avg Up & Down Distance from Pin (yds)"] = df[updown_dist_cols].apply(pd.to_numeric, errors='coerce').mean(axis=1)
    else:
        new_df_rounds["Avg Up & Down Distance from Pin (yds)"] = np.nan

    # Add Avg Up & Down Miss from Pin (ft) (original: 'Scramble up & down miss from pin (ft)')
    updown_miss_cols = [f"{i} - Scramble up & down miss from pin (ft)" for i in range(1, 19)]
    if all(col in df.columns for col in updown_miss_cols):
        new_df_rounds["Avg Up & Down Miss from Pin (ft)"] = df[updown_miss_cols].apply(pd.to_numeric, errors='coerce').mean(axis=1)
    else:
        new_df_rounds["Avg Up & Down Miss from Pin (ft)"] = np.nan

    # --- Add 'D1 Average', 'LPGA Tour Average', and 'Paris Summary' rows ---

    # Define the new average rows
    new_row_data_1 = {
        'Date': '2026-01-01',
        'Course': 'D1 Average',
        'Total Yds': 6300.0,
        'Slope Rating': 72.0,
        'Score': 75.0,
        'Diff from Par': 3.0,
        'Par 3 - Diff per Hole': 0.3,
        'Par 4 - Diff per Hole': 0.55,
        'Par 5 - Diff per Hole': 0.2,
        'FIR %': 75.0,
        'GIR %': 65.0,
        'Avg GIR Green Miss (Yd)': 8.0,
        'Avg GIR Pin Miss (ft)': 21.5,
        'Total Putts per Hole': 2.0,
        'Total Putts per Hole >= 30ft': 2.1,
        'Total Putts per Hole 20-30ft': 2.0,
        'Total Putts per Hole 10-20ft': 1.8,
        'Total Putts per Hole 5-10ft': 1.6,
        'Total Putts per Hole <= 5ft': 1.3,
        'Up and Down %': 55.0,
        'Avg Approach Distance (yds) from Pin': 135.0,
        'Avg Up & Down Distance from Pin (yds)': 15.0,
        'Avg Up & Down Miss from Pin (ft)': 10.0
    }

    new_row_data_2 = {
        'Date': '2026-01-01',
        'Course': 'LPGA Tour Average',
        'Total Yds': 6500.0,
        'Slope Rating': 72.0,
        'Score': 72.0,
        'Diff from Par': 0.0,
        'Par 3 - Diff per Hole': 0.1,
        'Par 4 - Diff per Hole': 0.2,
        'Par 5 - Diff per Hole': -0.4,
        'FIR %': 77.5,
        'GIR %': 70.0,
        'Avg GIR Green Miss (Yd)': 6.5,
        'Avg GIR Pin Miss (ft)': 20.0,
        'Total Putts per Hole': 2.0,
        'Total Putts per Hole >= 30ft': 2.1,
        'Total Putts per Hole 20-30ft': 2.0,
        'Total Putts per Hole 10-20ft': 1.8,
        'Total Putts per Hole 5-10ft': 1.6,
        'Total Putts per Hole <= 5ft': 1.3,
        'Up and Down %': 55.7,
        'Avg Approach Distance (yds) from Pin': 140.0,
        'Avg Up & Down Distance from Pin (yds)': 22.5,
        'Avg Up & Down Miss from Pin (ft)': 8.0
    }
    new_rows_df = pd.DataFrame([new_row_data_1, new_row_data_2])

    # Prepare `new_df_rounds` for summary calculation and concatenation
    # Convert Date column in `new_df_rounds` to datetime for calculating min/max date
    original_rounds_df_for_date = new_df_rounds.copy()
    original_rounds_df_for_date['Date'] = pd.to_datetime(original_rounds_df_for_date['Date'], errors='coerce')

    # Calculate summary statistics from the original golf round data
    numeric_cols_for_summary = original_rounds_df_for_date.select_dtypes(include=np.number).columns
    summary_means = original_rounds_df_for_date[numeric_cols_for_summary].mean().round(2) # Round summary means
    # Add Paris averages for new columns, only if present
    # For Paris Summary, calculate the average of the above for each column across all csv_url rows
    # For Paris Summary, calculate the average of the above for each column across all csv_url rows
    for col in [
        'Avg Approach Distance (yds) from Pin',
        'Avg Up & Down Distance from Pin (yds)',
        'Avg Up & Down Miss from Pin (ft)']:
        if col in new_df_rounds.columns and new_df_rounds[col].notnull().any():
            summary_means[col] = new_df_rounds[col].mean(skipna=True).round(2)
        else:
            summary_means[col] = np.nan

    min_date = original_rounds_df_for_date['Date'].min()
    max_date = original_rounds_df_for_date['Date'].max()

    summary_course = 'Paris Summary'

    summary_row_data = summary_means.to_dict()
    summary_row_data['Date'] = min_date.strftime('%Y-%m-%d') + " to " + max_date.strftime('%Y-%m-%d')
    summary_row_data['Course'] = summary_course
    summary_df = pd.DataFrame([summary_row_data])

    # Format the 'Date' column for the individual rounds and the average rows to 'YYYY-MM-DD'
    new_df_rounds['Date'] = pd.to_datetime(new_df_rounds['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
    new_rows_df['Date'] = pd.to_datetime(new_rows_df['Date']).dt.strftime('%Y-%m-%d')

    # Concatenate in the desired order: individual rounds, then Paris Summary, then D1/LPGA Averages
    final_df = pd.concat([new_df_rounds, summary_df, new_rows_df], ignore_index=True)

    # 5. Adjust the column order of the output DataFrame
    desired_column_order = [
        'Date',
        'Course',
        'Total Yds',
        'Slope Rating',
        'Score',
        'Diff from Par',
        'Par 3 - Diff per Hole',
        'Par 4 - Diff per Hole',
        'Par 5 - Diff per Hole',
        'FIR %',
        'GIR %',
        'Avg GIR Green Miss (Yd)',
        'Avg GIR Pin Miss (ft)',
        'Avg Approach Distance (yds) from Pin',
        'Total Putts per Hole',
        'Total Putts per Hole >= 30ft',
        'Total Putts per Hole 20-30ft',
        'Total Putts per Hole 10-20ft',
        'Total Putts per Hole 5-10ft',
        'Total Putts per Hole <= 5ft',
        'Up and Down %',
        'Avg Up & Down Distance from Pin (yds)',
        'Avg Up & Down Miss from Pin (ft)'
    ]
    final_df = final_df[desired_column_order]

    # Apply final rounding to all numeric columns for consistency across the entire DataFrame
    for col in final_df.select_dtypes(include=np.number).columns:
        final_df[col] = final_df[col].round(2)

    return final_df