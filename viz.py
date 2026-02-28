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

        # Row 1 (two chart slots)
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.empty()  # placeholder for Chart 1
        with r1c2:
            st.empty()  # placeholder for Chart 2

        # Row 2 (two chart slots)
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            st.empty()  # placeholder for Chart 3
        with r2c2:
            st.empty()  # placeholder for Chart 4

        # Row 3 (two chart slots)
        r3c1, r3c2 = st.columns(2)
        with r3c1:
            st.empty()  # placeholder for Chart 5
        with r3c2:
            st.empty()  # placeholder for Chart 6

if __name__ == '__main__':
    main()