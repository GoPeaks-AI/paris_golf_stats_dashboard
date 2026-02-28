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

    tab1, tab2 = st.tabs(["Table View", "Visualizations"])

    with tab1:
        st.subheader("Table")
        # find actual 'course' column name (case-insensitive)
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

    with tab2:
        st.subheader("Visualizations")

        course_col_name = next((c for c in df.columns if c.lower() == 'course'), None)
        if course_col_name is None:
            st.info("No 'Course' column found for comparison charts.")
        else:
            comparison_df = df[df[course_col_name].isin(
                ['Paris Summary', 'D1 Average', 'LPGA Tour Average']
            )].copy()

            def col(name):
                return next((c for c in df.columns if c.lower() == name.lower()), None)

            percentage_cols = [col('FIR %'), col('GIR %'), col('Up and Down %')]
            percentage_cols = [c for c in percentage_cols if c is not None]

            putt_cols = [col(x) for x in [
                'Total Putts per Hole',
                'Total Putts per Hole >= 30ft',
                'Total Putts per Hole 20-30ft',
                'Total Putts per Hole 10-20ft',
                'Total Putts per Hole 5-10ft',
                'Total Putts per Hole <= 5ft'
            ]]
            putt_cols = [c for c in putt_cols if c is not None]

            non_putt_other_cols = [col(x) for x in [
                'Diff from Par/Slope',
                'Par 3 - Diff per Hole',
                'Par 4 - Diff per Hole',
                'Par 5 - Diff per Hole',
                'Avg GIR Green Miss (Yd)',
                'Avg GIR Pin Miss (ft)'
            ]]
            non_putt_other_cols = [c for c in non_putt_other_cols if c is not None]

            custom_colors = {
                'Paris Summary': '#FFC0CB',
                'D1 Average': '#4B9CD3',
                'LPGA Tour Average': '#8C1515'
            }

            # Row 1: putt metrics — each metric in its own column
            if putt_cols:
                cols = st.columns(len(putt_cols))
                for i, metric in enumerate(putt_cols):
                    with cols[i]:
                        fig, ax = plt.subplots(figsize=(4, 3))
                        sns.barplot(
                            x=metric, y=course_col_name, data=comparison_df, ax=ax,
                            hue=course_col_name,
                            palette=[custom_colors.get(k, '#999999') for k in ['Paris Summary','D1 Average','LPGA Tour Average']],
                            dodge=False, orient='h', legend=False
                        )

                        # Capture original y labels (category names)
                        orig_labels = [t.get_text() for t in ax.get_yticklabels()]

                        # For first column: remove y-axis tick labels and annotate bars with course names
                        if i == 0:
                            ax.set_ylabel('')
                            ax.set_yticks([])  # remove tick marks/labels
                            # annotate each bar with the course name centered inside the bar
                            for lbl, p in zip(orig_labels, ax.patches):
                                width = p.get_width()
                                y = p.get_y() + p.get_height() / 2
                                # choose text color for contrast
                                text_color = 'black'
                                ax.text(width / 2, y, lbl, va='center', ha='center', color=text_color, fontsize=9)
                        else:
                            # other columns: no y ticks/labels
                            ax.set_ylabel('')
                            ax.set_yticks([])

                        ax.set_xlabel(metric)
                        for container in ax.containers:
                            try:
                                ax.bar_label(container, fmt='%.2f', fontsize=8)
                            except Exception:
                                pass
                        st.pyplot(fig)
                        plt.close(fig)

            # Row 2: non-putt other metrics — each metric in its own column
            if non_putt_other_cols:
                cols = st.columns(len(non_putt_other_cols))
                for i, metric in enumerate(non_putt_other_cols):
                    with cols[i]:
                        fig, ax = plt.subplots(figsize=(4, 3))
                        sns.barplot(
                            x=metric, y=course_col_name, data=comparison_df, ax=ax,
                            hue=course_col_name,
                            palette=[custom_colors.get(k, '#999999') for k in ['Paris Summary','D1 Average','LPGA Tour Average']],
                            dodge=False, orient='h', legend=False
                        )

                        orig_labels = [t.get_text() for t in ax.get_yticklabels()]

                        if i == 0:
                            ax.set_ylabel('')
                            ax.set_yticks([])
                            for lbl, p in zip(orig_labels, ax.patches):
                                width = p.get_width()
                                y = p.get_y() + p.get_height() / 2
                                text_color = 'black'
                                ax.text(width / 2, y, lbl, va='center', ha='center', color=text_color, fontsize=9)
                        else:
                            ax.set_ylabel('')
                            ax.set_yticks([])

                        ax.set_xlabel(metric)
                        for container in ax.containers:
                            try:
                                ax.bar_label(container, fmt='%.2f', fontsize=8)
                            except Exception:
                                pass
                        st.pyplot(fig)
                        plt.close(fig)

            # Row 3: percentage donut charts — one row per metric, 3 columns (one per course)
            if percentage_cols:
                course_names = ['Paris Summary', 'D1 Average', 'LPGA Tour Average']
                for metric in percentage_cols:
                    cols = st.columns(3)
                    for i, course_name in enumerate(course_names):
                        with cols[i]:
                            try:
                                val = comparison_df[comparison_df[course_col_name] == course_name][metric].iloc[0]
                            except Exception:
                                val = 0
                            if pd.isna(val):
                                val = 0
                            sizes = [val, max(0, 100 - float(val))]
                            colors = [custom_colors.get(course_name, '#999999'), '#e0e0e0']
                            fig, ax = plt.subplots(figsize=(3, 3))
                            wedges, texts, autotexts = ax.pie(
                                sizes, colors=colors, autopct='%1.1f%%', startangle=90,
                                pctdistance=0.85, wedgeprops=dict(width=0.3, edgecolor='w')
                            )
                            centre_circle = plt.Circle((0, 0), 0.70, fc='white')
                            ax.add_artist(centre_circle)
                            ax.set_title(f"{course_name}\n{metric}", fontsize=10)
                            ax.axis('equal')
                            st.pyplot(fig)
                            plt.close(fig)

    st.write("Made with ❤️ by dad 🤓.")

if __name__ == '__main__':
    main()