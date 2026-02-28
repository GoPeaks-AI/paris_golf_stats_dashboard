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
    st.title("Paris Golf Stats Dashboard")

    csv_url = 'https://docs.google.com/spreadsheets/d/1B4xhV_zVKYWskpMqjLGuityFR6B5qOLI39zq_8Nh1Hc/export?format=csv&gid=432528582'
    df = pgs.run(csv_url)

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
        'Paris Summary': '#FFC0CB',
        'D1 Average': '#4B9CD3',
        'LPGA Tour Average': '#8C1515'
    }
    course_names = ['Paris Summary', 'D1 Average', 'LPGA Tour Average']
    comparison_df = df[df[course_col_name].isin(course_names)].copy() if course_col_name else None

    # --- Viz - Score Diff ---
    with tab_score:
        st.subheader("Score Differential Visualizations")
        if comparison_df is not None:
            # All horizontal bar charts (Diff from Par/Slope, Par 3, Par 4, Par 5) in the same row
            metrics = [col('Diff from Par/Slope'), col('Par 3 - Diff per Hole'), col('Par 4 - Diff per Hole'), col('Par 5 - Diff per Hole')]
            metrics = [m for m in metrics if m]
            if metrics:
                cols = st.columns(len(metrics))
                for i, metric in enumerate(metrics):
                    with cols[i]:
                        fig, ax = plt.subplots(figsize=(4, 3))
                        sns.barplot(
                            x=metric, y=course_col_name, data=comparison_df, ax=ax,
                            hue=course_col_name,
                            palette=[custom_colors.get(k, '#999999') for k in course_names],
                            dodge=False, orient='h', legend=False
                        )
                        ax.set_ylabel('')
                        ax.set_yticks([])
                        orig_labels = [t.get_text() for t in ax.get_yticklabels()]
                        for lbl, p in zip(orig_labels, ax.patches):
                            width = p.get_width()
                            y = p.get_y() + p.get_height() / 2
                            ax.text(width / 2, y, lbl, va='center', ha='center', color='black', fontsize=9)
                        ax.set_xlabel(metric)
                        for container in ax.containers:
                            try:
                                ax.bar_label(container, fmt='%.2f', fontsize=8)
                            except Exception:
                                pass
                        st.pyplot(fig)
                        plt.close(fig)

    # --- Viz - Shots ---
    with tab_shots:
        st.subheader("Shots Visualizations")
        if comparison_df is not None:
            fir_col = col('FIR %')
            gir_col = col('GIR %')
            green_miss_col = col('Avg GIR Green Miss (Yd)')
            gir_pin_col = col('Avg GIR Pin Miss (ft)')
            # Show FIR %, GIR %, Avg GIR Green Miss (Yd), and Avg GIR Pin Miss (ft) as four charts
            shots_to_show = [fir_col, gir_col, green_miss_col, gir_pin_col]
            shots_to_show = [m for m in shots_to_show if m]
            if shots_to_show:
                cols = st.columns(len(shots_to_show))
                for i, metric in enumerate(shots_to_show):
                    with cols[i]:
                        fig, ax = plt.subplots(figsize=(4, 3))
                        sns.barplot(
                            x=metric, y=course_col_name, data=comparison_df, ax=ax,
                            hue=course_col_name,
                            palette=[custom_colors.get(k, '#999999') for k in course_names],
                            dodge=False, orient='h', legend=False
                        )
                        ax.set_ylabel('')
                        ax.set_yticks([])
                        orig_labels = [t.get_text() for t in ax.get_yticklabels()]
                        for lbl, p in zip(orig_labels, ax.patches):
                            width = p.get_width()
                            y = p.get_y() + p.get_height() / 2
                            ax.text(width / 2, y, lbl, va='center', ha='center', color='black', fontsize=9)
                        ax.set_xlabel(metric)
                        for container in ax.containers:
                            try:
                                ax.bar_label(container, fmt='%.2f', fontsize=8)
                            except Exception:
                                pass
                        st.pyplot(fig)
                        plt.close(fig)

    # --- Viz - Short Game ---
    with tab_short:
        st.subheader("Short Game Visualizations")
        if comparison_df is not None:
            # All short game charts in the same row
            putts_col = col('Total Putts per Hole')
            putt_other_cols = [col(x) for x in [
                'Total Putts per Hole >= 30ft',
                'Total Putts per Hole 20-30ft',
                'Total Putts per Hole 10-20ft',
                'Total Putts per Hole 5-10ft',
                'Total Putts per Hole <= 5ft']]
            putt_other_cols = [c for c in putt_other_cols if c]
            updown_col = col('Up and Down %')
            metrics = [putts_col] + putt_other_cols + ([updown_col] if updown_col else [])
            metrics = [m for m in metrics if m]
            if metrics:
                cols = st.columns(len(metrics))
                for i, metric in enumerate(metrics):
                    with cols[i]:
                        fig, ax = plt.subplots(figsize=(4, 3))
                        sns.barplot(
                            x=metric, y=course_col_name, data=comparison_df, ax=ax,
                            hue=course_col_name,
                            palette=[custom_colors.get(k, '#999999') for k in course_names],
                            dodge=False, orient='h', legend=False
                        )
                        ax.set_ylabel('')
                        ax.set_yticks([])
                        orig_labels = [t.get_text() for t in ax.get_yticklabels()]
                        for lbl, p in zip(orig_labels, ax.patches):
                            width = p.get_width()
                            y = p.get_y() + p.get_height() / 2
                            ax.text(width / 2, y, lbl, va='center', ha='center', color='black', fontsize=9)
                        ax.set_xlabel(metric)
                        for container in ax.containers:
                            try:
                                ax.bar_label(container, fmt='%.2f', fontsize=8)
                            except Exception:
                                pass
                        st.pyplot(fig)
                        plt.close(fig)

    st.write("Made with ❤️ by dad 🤓.")

if __name__ == '__main__':
    main()