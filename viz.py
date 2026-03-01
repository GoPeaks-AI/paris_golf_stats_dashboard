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

    # Ensure course_col_name and comparison_df are always defined before any use
    course_col_name = None
    comparison_df = None
    if df is not None:
        course_col_name = next((c for c in df.columns if c.lower() == 'course'), None)
        if course_col_name:
            course_names = ['LPGA Tour Average', 'D1 Average', 'Paris Summary']
            comparison_df = df[df[course_col_name].isin(course_names)].copy()
    if df is None:
        st.info("No data loaded. Upload a CSV or provide a `paris_golf_stats` module with `load_data()` or `df`.")
        return

    tab_home, tab1, tab_score, tab_shots, tab_short = st.tabs([
        "🏠 Home",
        "𝄜 Table",
        "🔢 Viz - Score Diff",
        "🏌️‍♀️ Viz - Shots",
        "⛳️ Viz - Short Game"
    ])

    # --- Home Tab: Summary of Strengths and Opportunities ---
    with tab_home:
        st.subheader("A Letter of Summary")
        if comparison_df is not None:
            def get_annotation_color(metric, value, d1_value, group):
                if metric == 'Up and Down %':
                    return 'green' if value >= d1_value else 'red'
                if group == 'score':
                    return 'green' if value <= d1_value else 'red'
                elif group == 'shots':
                    percent_metrics = ['FIR %', 'GIR %']
                    if metric in percent_metrics:
                        return 'green' if value >= d1_value else 'red'
                    else:
                        return 'green' if value <= d1_value else 'red'
                elif group == 'short':
                    return 'green' if value <= d1_value else 'red'
                return 'black'

            # Prepare row-wise strengths and opportunities
            summary_rows = [
                {
                    'label': 'Scoring Difference',
                    'metrics': [
                        ('Diff from Par', 'Overall Score Differential'),
                        ('Par 3 - Diff per Hole', 'Par 3 Performance'),
                        ('Par 4 - Diff per Hole', 'Par 4 Performance'),
                        ('Par 5 - Diff per Hole', 'Par 5 Performance')
                    ],
                    'group': 'score'
                },
                {
                    'label': 'Shots',
                    'metrics': [
                        ('FIR %', 'Fairways in Regulation %'),
                        ('GIR %', 'Greens in Regulation %'),
                        ('Avg Approach Distance (yds) from Pin', 'Approach Distance to Pin'),
                        ('Avg GIR Green Miss (Yd)', 'GIR Green Miss (Yards)'),
                        ('Avg GIR Pin Miss (ft)', 'GIR Pin Miss (Feet)')
                    ],
                    'group': 'shots'
                },
                {
                    'label': 'Short Game',
                    'metrics': [
                        ('Total Putts per Hole', 'Total Putts per Hole'),
                        ('Up and Down %', 'Up and Down %'),
                        ('Avg Up & Down Distance from Pin (yds)', 'Up & Down Distance from Pin (Yards)'),
                        ('Avg Up & Down Miss from Pin (ft)', 'Up & Down Miss from Pin (Feet)'),
                        ('Total Putts per Hole <= 5ft', 'Putts per Hole <= 5ft'),
                        ('Total Putts per Hole 5-10ft', 'Putts per Hole 5-10ft'),
                        ('Total Putts per Hole 10-20ft', 'Putts per Hole 10-20ft'),
                        ('Total Putts per Hole 20-30ft', 'Putts per Hole 20-30ft'),
                        ('Total Putts per Hole >= 30ft', 'Putts per Hole >= 30ft')
                    ],
                    'group': 'short'
                }
            ]

            # Build table data
            table_data = []
            for row in summary_rows:
                strengths = []
                opportunities = []
                for metric, desc in row['metrics']:
                    val = comparison_df[comparison_df[course_col_name]=='Paris Summary'][metric].values[0]
                    d1 = comparison_df[comparison_df[course_col_name]=='D1 Average'][metric].values[0]
                    color = get_annotation_color(metric, val, d1, row['group'])
                    item = f"{desc} (Paris: {val:.2f}, D1: {d1:.2f})"
                    if color == 'green':
                        strengths.append(item)
                    elif color == 'red':
                        opportunities.append(item)
                table_data.append((row['label'], strengths, opportunities))

            # Render as a coach's letter with colored strengths/opportunities
            letter = """
Dear Paris,

Here is a quick summary of your recent golf performance, focusing on your strengths and areas for growth. Let's keep building on what you do well and target a few key opportunities for improvement.
"""
            # Shots
            shots_strengths = []
            shots_opps = []
            for metric, desc in summary_rows[1]['metrics']:
                val = comparison_df[comparison_df[course_col_name]=='Paris Summary'][metric].values[0]
                d1 = comparison_df[comparison_df[course_col_name]=='D1 Average'][metric].values[0]
                color = get_annotation_color(metric, val, d1, 'shots')
                if color == 'green':
                    shots_strengths.append(f"<span style='color:green'>{desc} ({val:.2f} vs D1 {d1:.2f})</span>")
                elif color == 'red':
                    shots_opps.append(f"<span style='color:red'>{desc} ({val:.2f} vs D1 {d1:.2f})</span>")
            letter += "\n\n**Shots:**\n"
            if shots_strengths:
                letter += "Strengths: " + ", ".join(shots_strengths) + ".\n"
            if shots_opps:
                letter += "Opportunities: " + ", ".join(shots_opps) + ".\n"

            # Short Game
            short_strengths = []
            short_opps = []
            for metric, desc in summary_rows[2]['metrics']:
                val = comparison_df[comparison_df[course_col_name]=='Paris Summary'][metric].values[0]
                d1 = comparison_df[comparison_df[course_col_name]=='D1 Average'][metric].values[0]
                color = get_annotation_color(metric, val, d1, 'short')
                if color == 'green':
                    short_strengths.append(f"<span style='color:green'>{desc} ({val:.2f} vs D1 {d1:.2f})</span>")
                elif color == 'red':
                    short_opps.append(f"<span style='color:red'>{desc} ({val:.2f} vs D1 {d1:.2f})</span>")
            letter += "\n\n**Short Game:**\n"
            if short_strengths:
                letter += "Strengths: " + ", ".join(short_strengths) + ".\n"
            if short_opps:
                letter += "Opportunities: " + ", ".join(short_opps) + ".\n"

            # Scoring Difference
            score_strengths = []
            score_opps = []
            for metric, desc in summary_rows[0]['metrics']:
                val = comparison_df[comparison_df[course_col_name]=='Paris Summary'][metric].values[0]
                d1 = comparison_df[comparison_df[course_col_name]=='D1 Average'][metric].values[0]
                color = get_annotation_color(metric, val, d1, 'score')
                if color == 'green':
                    score_strengths.append(f"<span style='color:green'>{desc} ({val:.2f} vs D1 {d1:.2f})</span>")
                elif color == 'red':
                    score_opps.append(f"<span style='color:red'>{desc} ({val:.2f} vs D1 {d1:.2f})</span>")
            letter += "\n\n**Scoring Difference:**\n"
            if score_strengths:
                letter += "Strengths: " + ", ".join(score_strengths) + ".\n"
            if score_opps:
                letter += "Opportunities: " + ", ".join(score_opps) + ".\n"

            letter += "\nKeep up the great work and let's keep improving together!\n\n-AI Assistant Coach"
            st.markdown(letter, unsafe_allow_html=True)
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
                    return ['background-color: #f4cccc'] * len(row)  # light cardinal red
                if v == 'LPGA Tour Average':
                    return ['background-color: #cce6f4'] * len(row)  # light deep water
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
        'D1 Average': '#990000',          # Cardinal Red
        'LPGA Tour Average': '#006994'    # Deep Water
    }
    course_names = ['LPGA Tour Average', 'D1 Average', 'Paris Summary']
    comparison_df = df[df[course_col_name].isin(course_names)].copy() if course_col_name else None

    def show_color_legend():
        import matplotlib.patches as mpatches
        fig, ax = plt.subplots(figsize=(4, 0.07))  # Legend stays compact
        legend_labels = ['LPGA Tour Average', 'D1 Average', 'Paris Summary']
        legend_colors = ['#006994', '#990000', '#ff69b4']
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
                (col('Diff from Par'), 'Diff from Par'),
                (col('Par 3 - Diff per Hole'), 'Par 3 - Diff per Hole'),
                (col('Par 4 - Diff per Hole'), 'Par 4 - Diff per Hole'),
                (col('Par 5 - Diff per Hole'), 'Par 5 - Diff per Hole')
            ]
            metrics = [(m, label) for m, label in metrics if m]
            if metrics:
                cols = st.columns(len(metrics))
                order = ['Paris Summary', 'D1 Average', 'LPGA Tour Average']
                color_map = ['#ff69b4', '#990000', '#006994']
                for i, (metric, label) in enumerate(metrics):
                    with cols[i]:
                        fig, ax = plt.subplots(figsize=(4, 3))
                        vals_ordered = [comparison_df[comparison_df[course_col_name]==k][metric].values[0] if k in comparison_df[course_col_name].values else 0 for k in order]
                        y_labels_ordered = order
                        bars = ax.barh(y_labels_ordered, vals_ordered, color=color_map)
                        ax.set_xlabel(label)
                        ax.set_ylabel('')
                        # Color annotation for Paris Summary: green/bold for up, red/bold for down
                        for idx, (bar, value, label_y) in enumerate(zip(bars, vals_ordered, y_labels_ordered)):
                            annotation = f'{value:.2f}'
                            text_kwargs = {'va': 'center', 'ha': 'left', 'fontsize': 10}
                            if label_y == 'Paris Summary':
                                d1_value = vals_ordered[y_labels_ordered.index('D1 Average')]
                                # Special rule for Up and Down %
                                if label == 'Up and Down %':
                                    if value >= d1_value:
                                        text_kwargs['color'] = 'green'
                                        text_kwargs['fontweight'] = 'bold'
                                    else:
                                        text_kwargs['color'] = 'red'
                                        text_kwargs['fontweight'] = 'bold'
                                else:
                                    if value > d1_value:
                                        text_kwargs['color'] = 'red'
                                        text_kwargs['fontweight'] = 'bold'
                                    else:
                                        text_kwargs['color'] = 'green'
                                        text_kwargs['fontweight'] = 'bold'
                            ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, annotation, **text_kwargs)
                        ax.set_yticks([])
                        st.pyplot(fig)
                        plt.close(fig)

        # --- New: Relationship between Hole Handicap and Hole Score Diff ---

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
                color_map = ['#ff69b4', '#990000', '#006994']
                for i, metric in enumerate(shots_to_show):
                    with cols[i]:
                        fig, ax = plt.subplots(figsize=(4, 3))
                        vals_ordered = [comparison_df[comparison_df[course_col_name]==k][metric].values[0] if k in comparison_df[course_col_name].values else 0 for k in order]
                        y_labels_ordered = order
                        bars = ax.barh(y_labels_ordered, vals_ordered, color=color_map)
                        ax.set_xlabel(metric)
                        ax.set_ylabel('')
                        # Color annotation for Paris Summary: green/bold for up, red/bold for down
                        for idx, (bar, value, label_y) in enumerate(zip(bars, vals_ordered, y_labels_ordered)):
                            annotation = f'{value:.2f}'
                            text_kwargs = {'va': 'center', 'ha': 'left', 'fontsize': 10}
                            if label_y == 'Paris Summary':
                                d1_value = vals_ordered[y_labels_ordered.index('D1 Average')]
                                # Special rule for Up and Down %
                                if metric == 'Up and Down %':
                                    if value >= d1_value:
                                        text_kwargs['color'] = 'green'
                                        text_kwargs['fontweight'] = 'bold'
                                    else:
                                        text_kwargs['color'] = 'red'
                                        text_kwargs['fontweight'] = 'bold'
                                else:
                                    percent_metrics = ['FIR %', 'GIR %']
                                    metric_name = metric if isinstance(metric, str) else ''
                                    for colname in df.columns:
                                        if df[colname].equals(df[metric]):
                                            metric_name = colname
                                            break
                                    if metric_name in percent_metrics:
                                        if value < d1_value:
                                            text_kwargs['color'] = 'red'
                                            text_kwargs['fontweight'] = 'bold'
                                        else:
                                            text_kwargs['color'] = 'green'
                                            text_kwargs['fontweight'] = 'bold'
                                    else:
                                        if value > d1_value:
                                            text_kwargs['color'] = 'red'
                                            text_kwargs['fontweight'] = 'bold'
                                        else:
                                            text_kwargs['color'] = 'green'
                                            text_kwargs['fontweight'] = 'bold'
                            ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, annotation, **text_kwargs)
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
                # First row: 4 charts (Total Putts per Hole, Up & Down %, Up & Down Distance, Up & Down Miss)
                cols = st.columns(4)
                order = ['Paris Summary', 'D1 Average', 'LPGA Tour Average']
                color_map = ['#ff69b4', '#990000', '#006994']
                # Chart 1: Total Putts per Hole
                with cols[0]:
                    metric = first_row_metrics[0]
                    fig, ax = plt.subplots(figsize=(4, 4))
                    vals_ordered = [comparison_df[comparison_df[course_col_name]==k][metric].values[0] if k in comparison_df[course_col_name].values else 0 for k in order]
                    y_labels_ordered = order
                    bars = ax.barh(y_labels_ordered, vals_ordered, color=color_map)
                    ax.set_xlabel(metric)
                    ax.set_ylabel('')
                    for idx, (bar, value, label_y) in enumerate(zip(bars, vals_ordered, y_labels_ordered)):
                        annotation = f'{value:.2f}'
                        text_kwargs = {'va': 'center', 'ha': 'left', 'fontsize': 10}
                        if label_y == 'Paris Summary':
                            d1_value = vals_ordered[y_labels_ordered.index('D1 Average')]
                            if metric == 'Up and Down %':
                                if value >= d1_value:
                                    text_kwargs['color'] = 'green'
                                    text_kwargs['fontweight'] = 'bold'
                                else:
                                    text_kwargs['color'] = 'red'
                                    text_kwargs['fontweight'] = 'bold'
                            else:
                                if value > d1_value:
                                    text_kwargs['color'] = 'red'
                                    text_kwargs['fontweight'] = 'bold'
                                else:
                                    text_kwargs['color'] = 'green'
                                    text_kwargs['fontweight'] = 'bold'
                        ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, annotation, **text_kwargs)
                    ax.set_yticks([])
                    st.pyplot(fig)
                    plt.close(fig)
                # Chart 2: Up & Down %
                if len(first_row_metrics) > 1:
                    with cols[1]:
                        metric = first_row_metrics[1]
                        fig, ax = plt.subplots(figsize=(4, 4))
                        vals_ordered = [comparison_df[comparison_df[course_col_name]==k][metric].values[0] if k in comparison_df[course_col_name].values else 0 for k in order]
                        y_labels_ordered = order
                        bars = ax.barh(y_labels_ordered, vals_ordered, color=color_map)
                        ax.set_xlabel(metric)
                        ax.set_ylabel('')
                        for idx, (bar, value, label_y) in enumerate(zip(bars, vals_ordered, y_labels_ordered)):
                            annotation = f'{value:.2f}'
                            text_kwargs = {'va': 'center', 'ha': 'left', 'fontsize': 10}
                            if label_y == 'Paris Summary':
                                d1_value = vals_ordered[y_labels_ordered.index('D1 Average')]
                                if metric == 'Up and Down %':
                                    if value >= d1_value:
                                        text_kwargs['color'] = 'green'
                                        text_kwargs['fontweight'] = 'bold'
                                    else:
                                        text_kwargs['color'] = 'red'
                                        text_kwargs['fontweight'] = 'bold'
                                else:
                                    if value > d1_value:
                                        text_kwargs['color'] = 'red'
                                        text_kwargs['fontweight'] = 'bold'
                                    else:
                                        text_kwargs['color'] = 'green'
                                        text_kwargs['fontweight'] = 'bold'
                            ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, annotation, **text_kwargs)
                        ax.set_yticks([])
                        st.pyplot(fig)
                        plt.close(fig)
                # Chart 3: Up & Down Distance
                if len(first_row_metrics) > 2:
                    with cols[2]:
                        metric = first_row_metrics[2]
                        fig, ax = plt.subplots(figsize=(4, 4))
                        vals_ordered = [comparison_df[comparison_df[course_col_name]==k][metric].values[0] if k in comparison_df[course_col_name].values else 0 for k in order]
                        y_labels_ordered = order
                        bars = ax.barh(y_labels_ordered, vals_ordered, color=color_map)
                        ax.set_xlabel(metric)
                        ax.set_ylabel('')
                        for idx, (bar, value, label_y) in enumerate(zip(bars, vals_ordered, y_labels_ordered)):
                            annotation = f'{value:.2f}'
                            text_kwargs = {'va': 'center', 'ha': 'left', 'fontsize': 10}
                            if label_y == 'Paris Summary':
                                d1_value = vals_ordered[y_labels_ordered.index('D1 Average')]
                                if metric == 'Up and Down %':
                                    if value >= d1_value:
                                        text_kwargs['color'] = 'green'
                                        text_kwargs['fontweight'] = 'bold'
                                    else:
                                        text_kwargs['color'] = 'red'
                                        text_kwargs['fontweight'] = 'bold'
                                else:
                                    if value > d1_value:
                                        text_kwargs['color'] = 'red'
                                        text_kwargs['fontweight'] = 'bold'
                                    else:
                                        text_kwargs['color'] = 'green'
                                        text_kwargs['fontweight'] = 'bold'
                            ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, annotation, **text_kwargs)
                        ax.set_yticks([])
                        st.pyplot(fig)
                        plt.close(fig)
                # Chart 4: Up & Down Miss
                if len(first_row_metrics) > 3:
                    with cols[3]:
                        metric = first_row_metrics[3]
                        fig, ax = plt.subplots(figsize=(4, 4))
                        vals_ordered = [comparison_df[comparison_df[course_col_name]==k][metric].values[0] if k in comparison_df[course_col_name].values else 0 for k in order]
                        y_labels_ordered = order
                        bars = ax.barh(y_labels_ordered, vals_ordered, color=color_map)
                        ax.set_xlabel(metric)
                        ax.set_ylabel('')
                        for idx, (bar, value, label_y) in enumerate(zip(bars, vals_ordered, y_labels_ordered)):
                            annotation = f'{value:.2f}'
                            text_kwargs = {'va': 'center', 'ha': 'left', 'fontsize': 10}
                            if label_y == 'Paris Summary':
                                d1_value = vals_ordered[y_labels_ordered.index('D1 Average')]
                                if metric == 'Up and Down %':
                                    if value >= d1_value:
                                        text_kwargs['color'] = 'green'
                                        text_kwargs['fontweight'] = 'bold'
                                    else:
                                        text_kwargs['color'] = 'red'
                                        text_kwargs['fontweight'] = 'bold'
                                else:
                                    if value > d1_value:
                                        text_kwargs['color'] = 'red'
                                        text_kwargs['fontweight'] = 'bold'
                                    else:
                                        text_kwargs['color'] = 'green'
                                        text_kwargs['fontweight'] = 'bold'
                            ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, annotation, **text_kwargs)
                        ax.set_yticks([])
                        st.pyplot(fig)
                        plt.close(fig)

                # Second row: merged putt distance chart (1/4 width)
                putt_labels = [x for x in putt_order if col(x) in putt_other_cols]
                n_distances = len(putt_labels)
                n_groups = len(order)
                data = []
                for metric in putt_labels:
                    vals = [comparison_df[comparison_df[course_col_name]==k][col(metric)].values[0] if k in comparison_df[course_col_name].values else 0 for k in order]
                    data.append(vals)
                data = np.array(data)
                y = np.arange(n_distances)
                bar_height = 0.2
                row2_cols = st.columns([1, 1, 1, 1])  # 1/4 width for chart, 3/4 empty
                with row2_cols[0]:
                    fig, ax = plt.subplots(figsize=(4, 4))
                    for i, (group, color) in enumerate(zip(order, color_map)):
                        ax.barh(y + (i - 1) * bar_height, data[:, i], height=bar_height, label=group, color=color)
                    ax.set_yticks(y)
                    ax.set_yticklabels(putt_labels)
                    ax.set_xlabel('Number of Putts')
                    ax.set_ylabel('Distance Range')
                    ax.set_title('Putts per Hole by Distance Range')
                    # Annotate all bars, color Paris Summary vs D1
                    for i in range(n_distances):
                        for j in range(n_groups):
                            val = data[i, j]
                            x = val
                            y_pos = y[i] + (j - 1) * bar_height
                            annotation = f'{val:.2f}'
                            text_kwargs = {'va': 'center', 'ha': 'left', 'fontsize': 10}
                            # Paris Summary annotation color logic
                            if j == 0:  # Paris Summary
                                d1_value = data[i, 1]
                                if val > d1_value:
                                    text_kwargs['color'] = 'red'
                                    text_kwargs['fontweight'] = 'bold'
                                else:
                                    text_kwargs['color'] = 'green'
                                    text_kwargs['fontweight'] = 'bold'
                            else:
                                text_kwargs['color'] = 'black'
                                text_kwargs['fontweight'] = 'normal'
                            ax.text(x, y_pos, annotation, **text_kwargs)
                    st.pyplot(fig)
                    plt.close(fig)

    st.markdown("<hr style='margin-top:2em;margin-bottom:0.5em;'>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;font-size:1.1em;'>Made with ❤️ by dad 🤓.</div>", unsafe_allow_html=True)

if __name__ == '__main__':
    main()