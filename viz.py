import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import numpy as np
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

import matplotlib.pyplot as plt
import seaborn as sns

import paris_golf_stats as pgs

def fmt_number(x):
    if pd.isna(x):
        return ""
    try:
        v = float(x)
    except Exception:
        return x
    return str(int(v)) if v.is_integer() else f"{v:.2f}"

def main():
    # Passcode protection
    passcode = st.text_input("Enter passcode to access dashboard:", type="password")
    if passcode != "paris0223":
        st.warning("Incorrect or missing passcode.")
        st.stop()

    st.title("Paris Golf Stats Dashboard")

    csv_url = 'https://docs.google.com/spreadsheets/d/1B4xhV_zVKYWskpMqjLGuityFR6B5qOLI39zq_8Nh1Hc/export?format=csv&gid=432528582'
    df = pgs.run(csv_url)

    # Ensure course_col_name is always defined before any use
    course_col_name = None
    if df is not None:
        course_col_name = next((c for c in df.columns if c.lower() == 'course'), None)

    if df is None:
        st.info("No data loaded. Upload a CSV or provide a `paris_golf_stats` module with `load_data()` or `df`.")
        return

    tab1, tab_score, tab_shots, tab_short = st.tabs(["Table View", "Viz - Score Diff", "Viz - Shots", "Viz - Short Game"])

    with tab1:
        st.subheader("Table")
        course_col = next((c for c in df.columns if c.lower() == 'course'), None)
        if course_col is None:
            st.dataframe(df)
        else:
            def _highlight_row(row):
                v = str(row[course_col]).strip()
                if v == 'Paris Summary':
                    return ['background-color: #ffe6f0'] * len(row)
                if v == 'D1 Average':
                    return ['background-color: #b3d9ff'] * len(row)
                if v == 'LPGA Tour Average':
                    return ['background-color: #ffcccc'] * len(row)
                return [''] * len(row)
            styled = df.style.apply(_highlight_row, axis=1).format(fmt_number)
            st.dataframe(styled)

    if not df.empty:
        csv = df.to_csv(index=False)
        st.download_button("Download filtered CSV", csv, "filtered.csv")

    # Helper functions and color setup
    def col(name):
        return next((c for c in df.columns if c.lower() == name.lower()), None)

    course_col_name = next((c for c in df.columns if c.lower() == 'course'), None)
    custom_colors = {
        'Paris Summary': '#ff69b4',       # pink
        'D1 Average': '#ff0000',          # red
        'LPGA Tour Average': '#0074d9'    # blue
    }
    course_names = ['LPGA Tour Average', 'D1 Average', 'Paris Summary']
    comparison_df = df[df[course_col_name].isin(course_names)].copy() if course_col_name else None

    def show_color_legend():
        import matplotlib.patches as mpatches
        fig, ax = plt.subplots(figsize=(4, 0.07))  # Legend stays compact
        legend_labels = ['LPGA Tour Average', 'D1 Average', 'Paris Summary']
        legend_colors = ['#0074d9', '#ff0000', '#ff69b4']
        for i, (label, color) in enumerate(zip(legend_labels, legend_colors)):
            rect = mpatches.Rectangle((i, 0), 1, 1, color=color)
            ax.add_patch(rect)
            ax.text(i + 0.5, 0.5, label, ha='center', va='center', fontsize=4, color='white')
        ax.set_xlim(0, 3)
        ax.set_ylim(0, 1)
        ax.axis('off')
        # Place legend in the center of three columns (centered, 1/4 width)
        left_col, center_col, right_col = st.columns([1, 3, 1])
        with center_col:
            st.pyplot(fig)
        plt.close(fig)

    # --- Viz - Score Diff ---
    with tab_score:
        st.subheader("Score Differential Visualizations")
        show_color_legend()
        if comparison_df is not None:
            metrics = [
                (col('Diff from Par/Slope'), 'Diff from Par/Slope'),
                (col('Par 3 - Diff per Hole'), 'Par 3 - Diff per Hole'),
                (col('Par 4 - Diff per Hole'), 'Par 4 - Diff per Hole'),
                (col('Par 5 - Diff per Hole'), 'Par 5 - Diff per Hole')
            ]
            metrics = [(m, label) for m, label in metrics if m]
            if metrics:
                cols = st.columns(len(metrics))
                order = ['Paris Summary', 'D1 Average', 'LPGA Tour Average']
                color_map = ['#ff69b4', '#ff0000', '#0074d9']
                for i, (metric, label) in enumerate(metrics):
                    with cols[i]:
                        fig, ax = plt.subplots(figsize=(4, 3))
                        vals_ordered = [comparison_df[comparison_df[course_col_name]==k][metric].values[0] if k in comparison_df[course_col_name].values else 0 for k in order]
                        y_labels_ordered = order
                        bars = ax.barh(y_labels_ordered, vals_ordered, color=color_map)
                        ax.set_xlabel(label)
                        ax.set_ylabel('')
                        for bar, value in zip(bars, vals_ordered):
                            ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f'{value:.2f}', va='center', ha='left', fontsize=10)
                        ax.set_yticks([])
                        st.pyplot(fig)
                        plt.close(fig)

    # --- Viz - Shots ---
    with tab_shots:
        st.subheader("Shots Visualizations")
        show_color_legend()
        if comparison_df is not None:
            fir_col = col('FIR %')
            approach_col = col('Avg Approach Distance (yds) from Pin')
            gir_col = col('GIR %')
            green_miss_col = col('Avg GIR Green Miss (Yd)')
            gir_pin_col = col('Avg GIR Pin Miss (ft)')
            # Insert approach_col between FIR % and GIR %
            shots_to_show = []
            if fir_col: shots_to_show.append(fir_col)
            if approach_col: shots_to_show.append(approach_col)
            if gir_col: shots_to_show.append(gir_col)
            if green_miss_col: shots_to_show.append(green_miss_col)
            if gir_pin_col: shots_to_show.append(gir_pin_col)
            if shots_to_show:
                cols = st.columns(len(shots_to_show))
                order = ['Paris Summary', 'D1 Average', 'LPGA Tour Average']
                color_map = ['#ff69b4', '#ff0000', '#0074d9']
                for i, metric in enumerate(shots_to_show):
                    with cols[i]:
                        fig, ax = plt.subplots(figsize=(4, 3))
                        vals_ordered = [comparison_df[comparison_df[course_col_name]==k][metric].values[0] if k in comparison_df[course_col_name].values else 0 for k in order]
                        y_labels_ordered = order
                        bars = ax.barh(y_labels_ordered, vals_ordered, color=color_map)
                        ax.set_xlabel(metric)
                        ax.set_ylabel('')
                        for bar, value in zip(bars, vals_ordered):
                            ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f'{value:.2f}', va='center', ha='left', fontsize=10)
                        ax.set_yticks([])
                        st.pyplot(fig)
                        plt.close(fig)

    # --- Viz - Short Game ---
    with tab_short:
        st.subheader("Short Game Visualizations")
        show_color_legend()
        if comparison_df is not None:
            putts_col = col('Total Putts per Hole')
            updown_col = col('Up and Down %')
            updown_dist_col = col('Avg Up & Down Distance from Pin (yds)')
            updown_miss_col = col('Avg Up & Down Miss from Pin (ft)')
            # Reorder from shortest to longest: <=5ft, 5-10ft, 10-20ft, 20-30ft, >=30ft
            putt_order = [
                'Total Putts per Hole <= 5ft',
                'Total Putts per Hole 5-10ft',
                'Total Putts per Hole 10-20ft',
                'Total Putts per Hole 20-30ft',
                'Total Putts per Hole >= 30ft'
            ]
            putt_other_cols = [col(x) for x in putt_order]
            putt_other_cols = [c for c in putt_other_cols if c]
            # First row: total putts, up & down %, up & down distance, up & down miss
            first_row_metrics = [putts_col, updown_col, updown_dist_col, updown_miss_col]
            first_row_metrics = [m for m in first_row_metrics if m]
            if first_row_metrics:
                cols1 = st.columns(len(first_row_metrics))
                order = ['Paris Summary', 'D1 Average', 'LPGA Tour Average']
                color_map = ['#ff69b4', '#ff0000', '#0074d9']
                for i, metric in enumerate(first_row_metrics):
                    with cols1[i]:
                        fig, ax = plt.subplots(figsize=(4, 3))
                        vals_ordered = [comparison_df[comparison_df[course_col_name]==k][metric].values[0] if k in comparison_df[course_col_name].values else 0 for k in order]
                        y_labels_ordered = order
                        bars = ax.barh(y_labels_ordered, vals_ordered, color=color_map)
                        ax.set_xlabel(metric)
                        ax.set_ylabel('')
                        for bar, value in zip(bars, vals_ordered):
                            ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f'{value:.2f}', va='center', ha='left', fontsize=10)
                        ax.set_yticks([])
                        st.pyplot(fig)
                        plt.close(fig)
            # Second row: all other putt distance metrics
            if putt_other_cols:
                cols2 = st.columns(len(putt_other_cols))
                order = ['Paris Summary', 'D1 Average', 'LPGA Tour Average']
                color_map = ['#ff69b4', '#ff0000', '#0074d9']
                for i, metric in enumerate(putt_other_cols):
                    with cols2[i]:
                        fig, ax = plt.subplots(figsize=(4, 3))
                        vals_ordered = [comparison_df[comparison_df[course_col_name]==k][metric].values[0] if k in comparison_df[course_col_name].values else 0 for k in order]
                        y_labels_ordered = order
                        bars = ax.barh(y_labels_ordered, vals_ordered, color=color_map)
                        ax.set_xlabel(metric)
                        ax.set_ylabel('')
                        for bar, value in zip(bars, vals_ordered):
                            ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f'{value:.2f}', va='center', ha='left', fontsize=10)
                        ax.set_yticks([])
                        st.pyplot(fig)
                        plt.close(fig)

    st.write("Made with ❤️ by dad 🤓.")

if __name__ == '__main__':
    main()