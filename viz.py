import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import numpy as np
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

import matplotlib.pyplot as plt
import seaborn as sns

import paris_golf_stats as pgs
import paris_golf_data_subset as gpd

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

    st.markdown('<h1 style="color:#ff69b4;">Paris Golf Stats Dashboard</h1>', unsafe_allow_html=True)

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

    tab_home, tab1, tab_score, tab_shots, tab_short, tab_analytics = st.tabs([
        "🏠 Home",
        "𝄜 Table",
        "🔢 Score Diff",
        "🎯 Shots",
        "⛳️ Short Game",
        "📊 Analytics"
    ])

    # --- Home Tab: Summary of Strengths and Opportunities ---
    with tab_home:
        st.subheader("A Letter of Summary")
        if comparison_df is not None:
            # Get the last game date from the dataframe if available
            last_game_date = None
            date_col = next((c for c in df.columns if c.lower() == 'date'), None)
            if date_col is not None:
                try:
                    last_game_date = pd.to_datetime(df[date_col], errors='coerce').max()
                    if pd.notnull(last_game_date):
                        last_game_date_str = last_game_date.strftime('%B %d, %Y')
                    else:
                        last_game_date_str = None
                except Exception:
                    last_game_date_str = None
            else:
                last_game_date_str = None
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
                        ('FIR %', 'FIR %'),
                        ('GIR %', 'GIR %'),
                        ('Avg Approach Distance (yds) from Pin', 'Approach Distance to Pin (yds)'),
                        ('Avg GIR Green Miss (yds)', 'GIR Green Miss (yds)'),
                        ('Avg GIR Pin Miss (ft)', 'GIR Pin Miss (ft)')
                    ],
                    'group': 'shots'
                },
                {
                    'label': 'Short Game',
                    'metrics': [
                        ('Total Putts per Hole', 'Total Putts per Hole'),
                        ('Up and Down %', 'Up and Down %'),
                        ('Avg Up & Down Distance from Pin (yds)', 'Up & Down Distance from Pin (yds)'),
                        ('Avg Up & Down Miss from Pin (ft)', 'Up & Down Miss from Pin (ft)'),
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
                    if metric in comparison_df.columns:
                        val = comparison_df[comparison_df[course_col_name]=='Paris Summary'][metric].values[0]
                        d1 = comparison_df[comparison_df[course_col_name]=='D1 Average'][metric].values[0]
                        color = get_annotation_color(metric, val, d1, row['group'])
                        item = f"{desc} (Paris: {val:.2f}, D1: {d1:.2f})"
                        if color == 'green':
                            strengths.append(item)
                        elif color == 'red':
                            opportunities.append(item)
                    else:
                        item = f"{desc} (Paris: N/A, D1: N/A)"
                        opportunities.append(item)
                table_data.append((row['label'], strengths, opportunities))

            # Render as a coach's letter with colored strengths/opportunities
            letter = f"""
Dear Paris,

Here is a quick summary of your recent golf performance, focusing on your strengths and areas for growth vis-a-vis D1 average. Let's keep building on what you do well and target a few key opportunities for improvement.
"""
            if last_game_date_str:
                letter = f"<div style='color:gray; font-size: 0.95em; margin-bottom: 0.5em;'>As of last game: <b>{last_game_date_str}</b></div>\n" + letter
            # Shots
            shots_strengths = []
            shots_opps = []
            for metric, desc in summary_rows[1]['metrics']:
                if metric in comparison_df.columns:
                    val = comparison_df[comparison_df[course_col_name]=='Paris Summary'][metric].values[0]
                    d1 = comparison_df[comparison_df[course_col_name]=='D1 Average'][metric].values[0]
                    color = get_annotation_color(metric, val, d1, 'shots')
                    if color == 'green':
                        shots_strengths.append(f"<span style='color:green'>{desc} ({val:.2f} vs D1 {d1:.2f})</span>")
                    elif color == 'red':
                        shots_opps.append(f"<span style='color:red'>{desc} ({val:.2f} vs D1 {d1:.2f})</span>")
                else:
                    shots_opps.append(f"<span style='color:red'>{desc} (N/A vs D1 N/A)</span>")
            letter += "\n\n**Shots:**\n"
            if shots_strengths:
                letter += "Strengths: " + ", ".join(shots_strengths) + ".\n"
            if shots_opps:
                letter += "Opportunities: " + ", ".join(shots_opps) + ".\n"

            # Short Game
            short_strengths = []
            short_opps = []
            for metric, desc in summary_rows[2]['metrics']:
                if metric in comparison_df.columns:
                    val = comparison_df[comparison_df[course_col_name]=='Paris Summary'][metric].values[0]
                    d1 = comparison_df[comparison_df[course_col_name]=='D1 Average'][metric].values[0]
                    color = get_annotation_color(metric, val, d1, 'short')
                    if color == 'green':
                        short_strengths.append(f"<span style='color:green'>{desc} ({val:.2f} vs D1 {d1:.2f})</span>")
                    elif color == 'red':
                        short_opps.append(f"<span style='color:red'>{desc} ({val:.2f} vs D1 {d1:.2f})</span>")
                else:
                    short_opps.append(f"<span style='color:red'>{desc} (N/A vs D1 N/A)</span>")
            letter += "\n\n**Short Game:**\n"
            if short_strengths:
                letter += "Strengths: " + ", ".join(short_strengths) + ".\n"
            if short_opps:
                letter += "Opportunities: " + ", ".join(short_opps) + ".\n"

            # Scoring Difference
            score_strengths = []
            score_opps = []
            for metric, desc in summary_rows[0]['metrics']:
                if metric in comparison_df.columns:
                    val = comparison_df[comparison_df[course_col_name]=='Paris Summary'][metric].values[0]
                    d1 = comparison_df[comparison_df[course_col_name]=='D1 Average'][metric].values[0]
                    color = get_annotation_color(metric, val, d1, 'score')
                    if color == 'green':
                        score_strengths.append(f"<span style='color:green'>{desc} ({val:.2f} vs D1 {d1:.2f})</span>")
                    elif color == 'red':
                        score_opps.append(f"<span style='color:red'>{desc} ({val:.2f} vs D1 {d1:.2f})</span>")
                else:
                    score_opps.append(f"<span style='color:red'>{desc} (N/A vs D1 N/A)</span>")
            letter += "\n\n**Scoring Difference:**\n"
            if score_strengths:
                letter += "Strengths: " + ", ".join(score_strengths) + ".\n"
            if score_opps:
                letter += "Opportunities: " + ", ".join(score_opps) + ".\n"

            letter += "\nKeep up the great work and let's keep improving together!\n\n-Your AI Assistant Coach 🏌️‍♀️"
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

        if comparison_df is not None:
            metrics = [
                (col('Diff from Par'), 'Diff from Par'),
                (col('Par 3 - Diff per Hole'), 'Par 3 - Diff per Hole'),
                (col('Par 4 - Diff per Hole'), 'Par 4 - Diff per Hole'),
                (col('Par 5 - Diff per Hole'), 'Par 5 - Diff per Hole')
            ]
            metrics = [(m, label) for m, label in metrics if m]
            if metrics:
                st.markdown('<h4 style="margin-bottom:0.5em;">Paris vs. D1 vs. LPGA Pro</h4>', unsafe_allow_html=True)
                show_color_legend()
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

                # --- Second row: Paris trend lines over time ---
                st.markdown('<h4 style="margin-bottom:0.5em;">Paris Stats Over Time</h4>', unsafe_allow_html=True)
                # Filter for Paris only, and ensure date is sorted
                date_col = next((c for c in df.columns if c.lower() == 'date'), None)
                # Legend row at the top, centered
                legend_cols = st.columns([1, 3, 1])
                with legend_cols[1]:
                    import matplotlib.lines as mlines
                    blue_line = mlines.Line2D([], [], color='crimson', linestyle='--', linewidth=2, label='Target (D1)')
                    # Four new legend markers
                    red_o = mlines.Line2D([], [], color='red', marker='o', linestyle='None', markersize=10, label='Miss target in practice')
                    red_s = mlines.Line2D([], [], color='red', marker="*", linestyle='None', markersize=10, label='Miss target in tournament')
                    green_o = mlines.Line2D([], [], color='green', marker='o', linestyle='None', markersize=10, label='Match/exceed target in practice')
                    green_s = mlines.Line2D([], [], color='green', marker="*", linestyle='None', markersize=10, label='Match/exceed target in tournament')
                    fig_legend, ax_legend = plt.subplots(figsize=(7, 0.7))
                    ax_legend.axis('off')
                    handles = [blue_line, red_o, red_s, green_o, green_s]
                    ax_legend.legend(handles=handles, loc='center', ncol=5, frameon=False, fontsize=12)
                    st.pyplot(fig_legend)
                    plt.close(fig_legend)
                if date_col:
                    # Exclude summary/average rows for Paris's individual rounds
                    exclude_names = set(['Paris Summary', 'D1 Average', 'LPGA Tour Average'])
                    if course_col_name:
                        paris_df = df[~df[course_col_name].isin(exclude_names)].copy()
                    else:
                        paris_df = None
                    if paris_df is not None and not paris_df.empty:
                        try:
                            paris_df[date_col] = pd.to_datetime(paris_df[date_col], errors='coerce')
                            paris_df = paris_df.sort_values(date_col)
                        except Exception:
                            pass
                        trend_cols = st.columns(len(metrics))
                        for i, (metric, label) in enumerate(metrics):
                            with trend_cols[i]:
                                fig, ax = plt.subplots(figsize=(4, 2.5))
                                if metric in paris_df.columns:
                                    x_dates = paris_df[date_col]
                                    y_vals = paris_df[metric]
                                    # Get D1 Average for comparison
                                    d1_avg = None
                                    if metric in comparison_df.columns:
                                        d1_avg = comparison_df[comparison_df[course_col_name]=='D1 Average'][metric].values[0]
                                        ax.axhline(d1_avg, color='crimson', linestyle='--', linewidth=2, label='D1 Target')
                                    # Determine color for each segment/node
                                    line_colors = []
                                    node_colors = []
                                    for y in y_vals:
                                        if d1_avg is not None:
                                            if y > d1_avg:
                                                line_colors.append('red')
                                                node_colors.append('red')
                                            else:
                                                line_colors.append('green')
                                                node_colors.append('green')
                                        else:
                                            line_colors.append('#ff69b4')
                                            node_colors.append('#ff69b4')
                                    # Plot colored segments
                                    for j in range(len(x_dates)-1):
                                        # Thin pink line for Paris segments
                                        ax.plot(x_dates[j:j+2], y_vals[j:j+2], color='#ff69b4', linewidth=1)
                                    # Use "*" marker for Tournament games, 'o' otherwise
                                    mode_col = next((c for c in paris_df.columns if c.lower() == 'mode'), None)
                                    for j in range(len(x_dates)):
                                        marker_style = 'o'
                                        if mode_col and str(paris_df.iloc[j][mode_col]).strip().lower() == 'tournament':
                                            marker_style = "*"
                                        ax.plot(x_dates[j], y_vals[j], marker=marker_style, color=node_colors[j], markersize=8)
                                    ax.set_xlabel("")
                                    ax.set_ylabel("")
                                    ax.set_title(label)
                                    ax.grid(True, linestyle='--', alpha=0.5)
                                    ax.set_xticks(x_dates)
                                    ax.set_xticklabels([d.strftime('%Y-%m-%d') if not pd.isna(d) else '' for d in x_dates], rotation=90, fontsize=7)
                                    fig.tight_layout()
                                else:
                                    ax.text(0.5, 0.5, 'No data', ha='center', va='center')
                                st.pyplot(fig)
                                plt.close(fig)

    # --- Viz - Shots ---
    with tab_shots:
        st.subheader("Shots Visualizations")
        if comparison_df is not None:
            fir_col = col('FIR %')
            approach_col = col('Avg Approach Distance (yds) from Pin')
            gir_col = col('GIR %')
            green_miss_col = col('Avg GIR Green Miss (yds)')
            gir_pin_col = col('Avg GIR Pin Miss (ft)')
            # Order: FIR %, GIR %, Approach, Green Miss, GIR Pin Miss
            shots_to_show = []
            if fir_col: shots_to_show.append(fir_col)
            if gir_col: shots_to_show.append(gir_col)
            if approach_col: shots_to_show.append(approach_col)
            if green_miss_col: shots_to_show.append(green_miss_col)
            if gir_pin_col: shots_to_show.append(gir_pin_col)
            if shots_to_show:
                st.markdown('<h4 style="margin-bottom:0.5em;">Paris vs. D1 vs. LPGA Pro</h4>', unsafe_allow_html=True)
                show_color_legend()
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

                # --- Second row: Paris trend lines over time ---
                st.markdown('<h4 style="margin-bottom:0.5em;">Paris Stats Over Time</h4>', unsafe_allow_html=True)
                date_col = next((c for c in df.columns if c.lower() == 'date'), None)
                # Add legend explanation for Paris line (red miss, green match/exceed), and crimson dash line (target)
                legend_cols = st.columns([1, 3, 1])
                with legend_cols[1]:
                    import matplotlib.lines as mlines
                    blue_line = mlines.Line2D([], [], color='crimson', linestyle='--', linewidth=2, label='Target (D1)')
                    # Four new legend markers
                    red_o = mlines.Line2D([], [], color='red', marker='o', linestyle='None', markersize=10, label='Miss target in practice')
                    red_s = mlines.Line2D([], [], color='red', marker="*", linestyle='None', markersize=10, label='Miss target in tournament')
                    green_o = mlines.Line2D([], [], color='green', marker='o', linestyle='None', markersize=10, label='Match/exceed target in practice')
                    green_s = mlines.Line2D([], [], color='green', marker="*", linestyle='None', markersize=10, label='Match/exceed target in tournament')
                    fig_legend, ax_legend = plt.subplots(figsize=(7, 0.7))
                    ax_legend.axis('off')
                    handles = [blue_line, red_o, red_s, green_o, green_s]
                    ax_legend.legend(handles=handles, loc='center', ncol=5, frameon=False, fontsize=12)
                    st.pyplot(fig_legend)
                    plt.close(fig_legend)
                if date_col:
                    exclude_names = set(['Paris Summary', 'D1 Average', 'LPGA Tour Average'])
                    if course_col_name:
                        paris_df = df[~df[course_col_name].isin(exclude_names)].copy()
                    else:
                        paris_df = None
                    if paris_df is not None and not paris_df.empty:
                        try:
                            paris_df[date_col] = pd.to_datetime(paris_df[date_col], errors='coerce')
                            paris_df = paris_df.sort_values(date_col)
                        except Exception:
                            pass
                        trend_cols = st.columns(len(shots_to_show))
                        for i, metric in enumerate(shots_to_show):
                            with trend_cols[i]:
                                fig, ax = plt.subplots(figsize=(4, 2.5))
                                if metric in paris_df.columns:
                                    x_dates = paris_df[date_col]
                                    y_vals = paris_df[metric]
                                    # Get D1 Average for comparison
                                    d1_avg = None
                                    if metric in comparison_df.columns:
                                        d1_avg = comparison_df[comparison_df[course_col_name]=='D1 Average'][metric].values[0]
                                        ax.axhline(d1_avg, color='crimson', linestyle='--', linewidth=2, label='D1 Target')
                                    # Determine color for each segment/node
                                    metric_name = metric if isinstance(metric, str) else ''
                                    fir_gir_metrics = ['FIR %', 'GIR %']
                                    for colname in df.columns:
                                        if df[colname].equals(df[metric]):
                                            metric_name = colname
                                            break
                                    line_colors = []
                                    node_colors = []
                                    for y in y_vals:
                                        if d1_avg is not None:
                                            if metric_name in fir_gir_metrics:
                                                # FIR % and GIR %: green if at/above, red if below
                                                if y >= d1_avg:
                                                    line_colors.append('green')
                                                    node_colors.append('green')
                                                else:
                                                    line_colors.append('red')
                                                    node_colors.append('red')
                                            else:
                                                # Other metrics: red if above, green if at/below
                                                if y > d1_avg:
                                                    line_colors.append('red')
                                                    node_colors.append('red')
                                                else:
                                                    line_colors.append('green')
                                                    node_colors.append('green')
                                        else:
                                            line_colors.append('#ff69b4')
                                            node_colors.append('#ff69b4')
                                    # Plot colored segments
                                    for j in range(len(x_dates)-1):
                                        # Thin pink line for Paris segments
                                        ax.plot(x_dates[j:j+2], y_vals[j:j+2], color='#ff69b4', linewidth=1)
                                    # Use "*" marker for Tournament games, 'o' otherwise
                                    mode_col = next((c for c in paris_df.columns if c.lower() == 'mode'), None)
                                    for j in range(len(x_dates)):
                                        marker_style = 'o'
                                        if mode_col and str(paris_df.iloc[j][mode_col]).strip().lower() == 'tournament':
                                            marker_style = "*"
                                        ax.plot(x_dates[j], y_vals[j], marker=marker_style, color=node_colors[j], markersize=8)
                                    ax.set_xlabel("")
                                    ax.set_ylabel("")
                                    ax.set_title(str(metric_name))
                                    ax.grid(True, linestyle='--', alpha=0.5)
                                    ax.set_xticks(x_dates)
                                    ax.set_xticklabels([d.strftime('%Y-%m-%d') if not pd.isna(d) else '' for d in x_dates], rotation=90, fontsize=7)
                                    fig.tight_layout()
                                else:
                                    ax.text(0.5, 0.5, 'No data', ha='center', va='center')
                                st.pyplot(fig)
                                plt.close(fig)

    # --- Viz - Short Game ---
    with tab_short:
        st.subheader("Short Game Visualizations")
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
            # First row: 4 charts (Total Putts per Hole, Up & Down %, Putts per Hole by Distance Range, Up & Down Distance or Miss)
            first_row_metrics = [putts_col, updown_col, updown_dist_col, updown_miss_col]
            first_row_metrics = [m for m in first_row_metrics if m]
            order = ['Paris Summary', 'D1 Average', 'LPGA Tour Average']
            color_map = ['#ff69b4', '#990000', '#006994']
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
            # Create y-tick labels by removing 'Total Putts per Hole ' prefix
            yticklabels = [label.replace('Total Putts per Hole ', '') for label in putt_labels]
            st.markdown('<h4 style="margin-bottom:0.5em;">Paris vs. D1 vs. LPGA Pro</h4>', unsafe_allow_html=True)
            show_color_legend()
            cols = st.columns(5)
            # Chart 1: Total Putts per Hole
            with cols[0]:
                metric = putts_col
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
            # Chart 2: Putts per Hole by Distance Range (first row, bar chart)
            if n_distances > 0:
                with cols[1]:
                    fig, ax = plt.subplots(figsize=(4, 4))
                    for i, (group, color) in enumerate(zip(order, color_map)):
                        ax.barh(y + (i - 1) * bar_height, data[:, i], height=bar_height, label=group, color=color)
                    ax.set_yticks(y)
                    ax.set_yticklabels(yticklabels)
                    ax.set_xlabel('Number of Putts')
                    ax.set_ylabel('')  # Remove Y-axis title
                    ax.set_title('Putts per Hole by Distance')
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
            # --- Second row: Paris trend lines over time ---
            st.markdown('<h4 style="margin-bottom:0.5em;">Paris Stats Over Time</h4>', unsafe_allow_html=True)
            date_col = next((c for c in df.columns if c.lower() == 'date'), None)
            # Add legend explanation for Paris line (red miss, green match/exceed), and crimson dash line (target)
            legend_cols = st.columns([1, 3, 1])
            with legend_cols[1]:
                import matplotlib.lines as mlines
                blue_line = mlines.Line2D([], [], color='crimson', linestyle='--', linewidth=2, label='Target (D1)')
                # Four new legend markers
                red_o = mlines.Line2D([], [], color='red', marker='o', linestyle='None', markersize=10, label='Miss target in practice')
                red_s = mlines.Line2D([], [], color='red', marker="*", linestyle='None', markersize=10, label='Miss target in tournament')
                green_o = mlines.Line2D([], [], color='green', marker='o', linestyle='None', markersize=10, label='Match/exceed target in practice')
                green_s = mlines.Line2D([], [], color='green', marker="*", linestyle='None', markersize=10, label='Match/exceed target in tournament')
                fig_legend, ax_legend = plt.subplots(figsize=(7, 0.7))
                ax_legend.axis('off')
                handles = [blue_line, red_o, red_s, green_o, green_s]
                ax_legend.legend(handles=handles, loc='center', ncol=5, frameon=False, fontsize=12)
                st.pyplot(fig_legend)
                plt.close(fig_legend)
            if date_col:
                exclude_names = set(['Paris Summary', 'D1 Average', 'LPGA Tour Average'])
                if course_col_name:
                    paris_df = df[~df[course_col_name].isin(exclude_names)].copy()
                else:
                    paris_df = None
                if paris_df is not None and not paris_df.empty:
                    try:
                        paris_df[date_col] = pd.to_datetime(paris_df[date_col], errors='coerce')
                        paris_df = paris_df.sort_values(date_col)
                    except Exception:
                        pass
                    trend_cols = st.columns(5)
                    # Chart 1: Total Putts per Hole
                    if putts_col:
                        with trend_cols[0]:
                            fig, ax = plt.subplots(figsize=(4, 2.5))
                            if putts_col in paris_df.columns:
                                x_dates = paris_df[date_col]
                                y_vals = paris_df[putts_col]
                                d1_avg = None
                                if putts_col in comparison_df.columns:
                                    d1_avg = comparison_df[comparison_df[course_col_name]=='D1 Average'][putts_col].values[0]
                                    ax.axhline(d1_avg, color='crimson', linestyle='--', linewidth=2, label='D1 Target')
                                line_colors = []
                                node_colors = []
                                for y in y_vals:
                                    if d1_avg is not None:
                                        if y > d1_avg:
                                            line_colors.append('red')
                                            node_colors.append('red')
                                        else:
                                            line_colors.append('green')
                                            node_colors.append('green')
                                    else:
                                        line_colors.append('#ff69b4')
                                        node_colors.append('#ff69b4')
                                for j in range(len(x_dates)-1):
                                    # Thin pink line for Paris segments
                                    ax.plot(x_dates[j:j+2], y_vals[j:j+2], color='#ff69b4', linewidth=1)
                                # Use "*" marker for Tournament games, 'o' otherwise
                                mode_col = next((c for c in paris_df.columns if c.lower() == 'mode'), None)
                                for j in range(len(x_dates)):
                                    marker_style = 'o'
                                    if mode_col and str(paris_df.iloc[j][mode_col]).strip().lower() == 'tournament':
                                        marker_style = "*"
                                    ax.plot(x_dates[j], y_vals[j], marker=marker_style, color=node_colors[j], markersize=8)
                                ax.set_xlabel("")
                                ax.set_ylabel("")
                                ax.set_title('Total Putts per Hole')
                                ax.grid(True, linestyle='--', alpha=0.5)
                                ax.set_xticks(x_dates)
                                ax.set_xticklabels([d.strftime('%Y-%m-%d') if not pd.isna(d) else '' for d in x_dates], rotation=90, fontsize=7)
                                fig.tight_layout()
                            else:
                                ax.text(0.5, 0.5, 'No data', ha='center', va='center')
                            st.pyplot(fig)
                            plt.close(fig)
                    # Chart 2: Putts per Hole by Distance Range (5 lines) -- NO D1 line
                    # Empty the second column, leave blank space
                    # if n_distances > 0:
                    #     with trend_cols[1]:
                    #         fig, ax = plt.subplots(figsize=(4, 2.5))
                    #         line_styles = ['-', '--', '-.', ':', (0, (3, 1, 1, 1))]
                    #         mode_col = next((c for c in paris_df.columns if c.lower() == 'mode'), None)
                    #         for i, label in enumerate(putt_labels):
                    #             colname = col(label)
                    #             if colname and colname in paris_df.columns:
                    #                 # Plot the connecting line first
                    #                 ax.plot(paris_df[date_col], paris_df[colname], linestyle=line_styles[i % len(line_styles)], linewidth=1, label=yticklabels[i])
                    #                 # Then plot markers on top
                    #                 for j in range(len(paris_df)):
                    #                     marker_style = 'o'
                    #                     if mode_col and str(paris_df.iloc[j][mode_col]).strip().lower() == 'tournament':
                    #                         marker_style = "*"
                    #                     ax.plot(paris_df[date_col].iloc[j], paris_df[colname].iloc[j], marker=marker_style, linestyle='None', markersize=8)
                    #         handles, labels = ax.get_legend_handles_labels()
                    #         by_label = dict(zip(labels, handles))
                    #         ax.legend(by_label.values(), by_label.keys(), loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)
                    #         ax.set_xlabel("")
                    #         ax.set_ylabel("")
                    #         ax.set_title('Putts per Hole by Distance')
                    #         ax.grid(True, linestyle='--', alpha=0.5)
                    #         ax.set_xticks(paris_df[date_col])
                    #         ax.set_xticklabels([d.strftime('%Y-%m-%d') if not pd.isna(d) else '' for d in paris_df[date_col]], rotation=90, fontsize=7)
                    #         ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)
                    #         fig.tight_layout()
                    #         st.pyplot(fig)
                    #         plt.close(fig)
                    # Chart 3: Up & Down %
                    if updown_col:
                        with trend_cols[2]:
                            fig, ax = plt.subplots(figsize=(4, 2.5))
                            if updown_col in paris_df.columns:
                                x_dates = paris_df[date_col]
                                y_vals = paris_df[updown_col]
                                d1_avg = None
                                if updown_col in comparison_df.columns:
                                    d1_avg = comparison_df[comparison_df[course_col_name]=='D1 Average'][updown_col].values[0]
                                    ax.axhline(d1_avg, color='crimson', linestyle='--', linewidth=2, label='D1 Target')
                                line_colors = []
                                node_colors = []
                                for y in y_vals:
                                    if d1_avg is not None:
                                        if y >= d1_avg:
                                            line_colors.append('green')
                                            node_colors.append('green')
                                        else:
                                            line_colors.append('red')
                                            node_colors.append('red')
                                    else:
                                        line_colors.append('#ff69b4')
                                        node_colors.append('#ff69b4')
                                for j in range(len(x_dates)-1):
                                    # Thin pink line for Paris segments
                                    ax.plot(x_dates[j:j+2], y_vals[j:j+2], color='#ff69b4', linewidth=1)
                                    # Use "*" marker for Tournament games, 'o' otherwise
                                    mode_col = next((c for c in paris_df.columns if c.lower() == 'mode'), None)
                                    for j in range(len(x_dates)):
                                        marker_style = 'o'
                                        if mode_col and str(paris_df.iloc[j][mode_col]).strip().lower() == 'tournament':
                                            marker_style = "*"
                                        ax.plot(x_dates[j], y_vals[j], marker=marker_style, color=node_colors[j], markersize=8)
                                ax.set_xlabel("")
                                ax.set_ylabel("")
                                ax.set_title('Up and Down %')
                                ax.grid(True, linestyle='--', alpha=0.5)
                                ax.set_xticks(x_dates)
                                ax.set_xticklabels([d.strftime('%Y-%m-%d') if not pd.isna(d) else '' for d in x_dates], rotation=90, fontsize=7)
                                fig.tight_layout()
                            else:
                                ax.text(0.5, 0.5, 'No data', ha='center', va='center')
                            st.pyplot(fig)
                            plt.close(fig)
                    # Chart 4: Up & Down Distance from Pin
                    if updown_dist_col:
                        with trend_cols[3]:
                            fig, ax = plt.subplots(figsize=(4, 2.5))
                            if updown_dist_col in paris_df.columns:
                                x_dates = paris_df[date_col]
                                y_vals = paris_df[updown_dist_col]
                                d1_avg = None
                                if updown_dist_col in comparison_df.columns:
                                    d1_avg = comparison_df[comparison_df[course_col_name]=='D1 Average'][updown_dist_col].values[0]
                                    ax.axhline(d1_avg, color='crimson', linestyle='--', linewidth=2, label='D1 Target')
                                line_colors = []
                                node_colors = []
                                for y in y_vals:
                                    if d1_avg is not None:
                                        if y > d1_avg:
                                            line_colors.append('red')
                                            node_colors.append('red')
                                        else:
                                            line_colors.append('green')
                                            node_colors.append('green')
                                    else:
                                        line_colors.append('#ff69b4')
                                        node_colors.append('#ff69b4')
                                for j in range(len(x_dates)-1):
                                    # Thin pink line for Paris segments
                                    ax.plot(x_dates[j:j+2], y_vals[j:j+2], color='#ff69b4', linewidth=1)
                                for j in range(len(x_dates)):
                                    ax.plot(x_dates[j], y_vals[j], marker='o', color=node_colors[j], markersize=8)
                                ax.set_xlabel("")
                                ax.set_ylabel("")
                                ax.set_title('Up & Down Distance from Pin (yds)')
                                ax.grid(True, linestyle='--', alpha=0.5)
                                ax.set_xticks(x_dates)
                                ax.set_xticklabels([d.strftime('%Y-%m-%d') if not pd.isna(d) else '' for d in x_dates], rotation=90, fontsize=7)
                                fig.tight_layout()
                            else:
                                ax.text(0.5, 0.5, 'No data', ha='center', va='center')
                            st.pyplot(fig)
                            plt.close(fig)
                    # Chart 5: Up & Down Miss from Pin
                    if updown_miss_col:
                        with trend_cols[4]:
                            fig, ax = plt.subplots(figsize=(4, 2.5))
                            if updown_miss_col in paris_df.columns:
                                x_dates = paris_df[date_col]
                                y_vals = paris_df[updown_miss_col]
                                d1_avg = None
                                if updown_miss_col in comparison_df.columns:
                                    d1_avg = comparison_df[comparison_df[course_col_name]=='D1 Average'][updown_miss_col].values[0]
                                    ax.axhline(d1_avg, color='crimson', linestyle='--', linewidth=2, label='D1 Target')
                                line_colors = []
                                node_colors = []
                                for y in y_vals:
                                    if d1_avg is not None:
                                        if y > d1_avg:
                                            line_colors.append('red')
                                            node_colors.append('red')
                                        else:
                                            line_colors.append('green')
                                            node_colors.append('green')
                                    else:
                                        line_colors.append('#ff69b4')
                                        node_colors.append('#ff69b4')
                                for j in range(len(x_dates)-1):
                                    # Thin pink line for Paris segments
                                    ax.plot(x_dates[j:j+2], y_vals[j:j+2], color='#ff69b4', linewidth=1)
                                for j in range(len(x_dates)):
                                    ax.plot(x_dates[j], y_vals[j], marker='o', color=node_colors[j], markersize=8)
                                ax.set_xlabel("")
                                ax.set_ylabel("")
                                ax.set_title('Up & Down Miss from Pin (ft)')
                                ax.grid(True, linestyle='--', alpha=0.5)
                                ax.set_xticks(x_dates)
                                ax.set_xticklabels([d.strftime('%Y-%m-%d') if not pd.isna(d) else '' for d in x_dates], rotation=90, fontsize=7)
                                fig.tight_layout()
                            else:
                                ax.text(0.5, 0.5, 'No data', ha='center', va='center')
                            st.pyplot(fig)
                            plt.close(fig)

                    # New row for individual putt distance charts
                    new_trend_cols = st.columns(5)
                    for i in range(5):
                        with new_trend_cols[i]:
                            label = putt_labels[i]
                            colname = col(label)
                            if colname and colname in paris_df.columns:
                                fig, ax = plt.subplots(figsize=(4, 2.5))
                                # Get D1 average for target line
                                d1_avg = None
                                if colname in comparison_df.columns:
                                    d1_avg = comparison_df[comparison_df[course_col_name]=='D1 Average'][colname].values[0]
                                    ax.axhline(d1_avg, color='crimson', linestyle='--', linewidth=2, label='D1 Target')
                                # Determine marker colors based on D1 benchmark
                                node_colors = []
                                for y in paris_df[colname]:
                                    if d1_avg is not None:
                                        if y > d1_avg:
                                            node_colors.append('red')
                                        else:
                                            node_colors.append('green')
                                    else:
                                        node_colors.append('#ff69b4')
                                # Plot the connecting line
                                ax.plot(paris_df[date_col], paris_df[colname], linestyle='-', linewidth=1, color='#ff69b4')
                                # Then plot markers
                                mode_col = next((c for c in paris_df.columns if c.lower() == 'mode'), None)
                                for j in range(len(paris_df)):
                                    marker_style = 'o'
                                    if mode_col and str(paris_df.iloc[j][mode_col]).strip().lower() == 'tournament':
                                        marker_style = "*"
                                    ax.plot(paris_df[date_col].iloc[j], paris_df[colname].iloc[j], marker=marker_style, linestyle='None', markersize=8, color=node_colors[j])
                                ax.set_xlabel("")
                                ax.set_ylabel("")
                                ax.set_title("Putts per Hole " + yticklabels[i])
                                ax.grid(True, linestyle='--', alpha=0.5)
                                ax.set_xticks(paris_df[date_col])
                                ax.set_xticklabels([d.strftime('%Y-%m-%d') if not pd.isna(d) else '' for d in paris_df[date_col]], rotation=90, fontsize=7)
                                fig.tight_layout()
                                st.pyplot(fig)
                                plt.close(fig)

            # Chart 3: Up & Down %
            if updown_col:
                with cols[2]:
                    metric = updown_col
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
            # Chart 4: Up & Down Distance from Pin
            if updown_dist_col:
                with cols[3]:
                    metric = updown_dist_col
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
            # Chart 5: Up & Down Miss from Pin
            if updown_miss_col:
                with cols[4]:
                    metric = updown_miss_col
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

    with tab_analytics:

        st.subheader("Paris Analytics in Detail")
        # Legend row at the top, centered
        legend_cols = st.columns([2, 1, 2])
        with legend_cols[1]:
            import matplotlib.lines as mlines
            blue_line = mlines.Line2D([], [], color='crimson', linestyle='--', linewidth=2, label='Target (D1)')
            red_dot = mlines.Line2D([], [], color='red', marker='o', linestyle='None', markersize=10, label='Miss Target')
            green_dot = mlines.Line2D([], [], color='green', marker='o', linestyle='None', markersize=10, label='Match/Exceed Target')
            fig_legend, ax_legend = plt.subplots(figsize=(5, 0.5))
            ax_legend.axis('off')
            handles = [blue_line, red_dot, green_dot]
            ax_legend.legend(handles=handles, loc='center', ncol=3, frameon=False, fontsize=12)
            st.pyplot(fig_legend)
            plt.close(fig_legend)

        df = gpd.run(csv_url)

        # Fill GIR miss from green with 0 if empty
        gir_miss_col = 'Approach shot GIR miss from green (yds)'
        if gir_miss_col in df.columns:
            df[gir_miss_col] = df[gir_miss_col].fillna(0)

        cols = st.columns([1, 1, 1, 1])

        # Plot hole handicap vs score diff from par in first column
        if 'Hole Handicap' in df.columns and 'Score Diff from Par' in df.columns:
            fig, ax = plt.subplots(figsize=(8, 5))
            y0 = 0
            colors = df['Score Diff from Par'].apply(lambda y: 'green' if y <= y0 else 'red')
            # Add light grey shade for X >= 13
            ax.axvspan(13, 20, color='lightgrey', alpha=0.4, zorder=0)
            ax.axhline(y0, color='crimson', linestyle='--', linewidth=2, alpha=0.5)
            # Make dot size proportional to the number of overlapping points (relative frequency)
            xy = list(zip(df['Hole Handicap'], df['Score Diff from Par']))
            from collections import Counter
            freq = Counter(xy)
            s = np.array([40 * freq[(x, y)] for x, y in xy])
            ax.scatter(df['Hole Handicap'], df['Score Diff from Par'], c=colors, s=s)
            ax.set_title('Hole Handicap vs Score Diff from Par')
            ax.set_xlabel('Hole Handicap')
            ax.set_ylabel('Score Diff from Par')
            x_min = 1
            x_max = max(18, int(np.nanmax(df['Hole Handicap'])))
            ax.set_xlim(x_min, x_max)
            ax.set_xticks([i for i in range(x_min, x_max+1)])
            y_min = -2
            y_max = int(np.ceil(np.nanmax(df['Score Diff from Par'])))
            ax.set_yticks([i for i in range(y_min, y_max+1)])
            with cols[0]:
                st.pyplot(fig)

        # Plot approach distance from pin vs GIR miss from green in second column
        approach_col = 'Approach shot distance (yds) from pin'
        if approach_col in df.columns and gir_miss_col in df.columns:
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            y0 = 8
            colors2 = df[gir_miss_col].apply(lambda y: 'green' if y <= y0 else 'red')
            ax2.axvspan(0, 125, color='lightgrey', alpha=0.4, zorder=0)
            ax2.axhline(y0, color='crimson', linestyle='--', linewidth=2, alpha=0.5)
            xy2 = list(zip(df[approach_col], df[gir_miss_col]))
            freq2 = Counter(xy2)
            s2 = np.array([40 * freq2[(x, y)] for x, y in xy2])
            ax2.scatter(df[approach_col], df[gir_miss_col], c=colors2, s=s2)
            ax2.set_title('Approach Distance from Pin vs GIR Miss from Green')
            ax2.set_xlabel('Approach shot distance (yds) from pin')
            ax2.set_ylabel('GIR miss from green (yds)')
            with cols[1]:
                st.pyplot(fig2)

        # Plot approach distance from pin vs GIR miss from pin in third column, exclude empty GIR miss from pin
        gir_miss_pin_col = 'Approach GIR from pin (ft)'
        if approach_col in df.columns and gir_miss_pin_col in df.columns:
            df_nonan = df.dropna(subset=[gir_miss_pin_col])
            if not df_nonan.empty:
                fig3, ax3 = plt.subplots(figsize=(8, 5))
                y0 = 21.5
                colors3 = df_nonan[gir_miss_pin_col].apply(lambda y: 'green' if y <= y0 else 'red')
                ax3.axvspan(0, 100, color='lightgrey', alpha=0.4, zorder=0)
                ax3.axhline(y0, color='crimson', linestyle='--', linewidth=2, alpha=0.5)
                xy3 = list(zip(df_nonan[approach_col], df_nonan[gir_miss_pin_col]))
                freq3 = Counter(xy3)
                s3 = np.array([40 * freq3[(x, y)] for x, y in xy3])
                ax3.scatter(df_nonan[approach_col], df_nonan[gir_miss_pin_col], c=colors3, s=s3)
                ax3.set_title('Approach Distance from Pin vs GIR Miss from Pin')
                ax3.set_xlabel('Approach shot distance (yds) from pin')
                ax3.set_ylabel('GIR miss from pin (ft)')
                with cols[2]:
                    st.pyplot(fig3)

        # Plot Scramble up & down distance vs Scramble up & down miss from pin in fourth column
        updown_dist_col = 'Scramble up & down distance from pin (yds)'
        updown_miss_col = 'Scramble up & down miss from pin (ft)'
        if updown_dist_col in df.columns and updown_miss_col in df.columns:
            df_updown = df.dropna(subset=[updown_dist_col])
            if not df_updown.empty:
                fig4, ax4 = plt.subplots(figsize=(8, 5))
                y0 = 10
                colors4 = df_updown[updown_miss_col].apply(lambda y: 'green' if y <= y0 else 'red')
                ax4.axvspan(0, 15, color='lightgrey', alpha=0.4, zorder=0)
                ax4.axhline(y0, color='crimson', linestyle='--', linewidth=2, alpha=0.5)
                xy4 = list(zip(df_updown[updown_dist_col], df_updown[updown_miss_col]))
                freq4 = Counter(xy4)
                s4 = np.array([40 * freq4[(x, y)] for x, y in xy4])
                ax4.scatter(df_updown[updown_dist_col], df_updown[updown_miss_col], c=colors4, s=s4)
                ax4.set_title('Scramble Up & Down Distance vs Miss from Pin')
                ax4.set_xlabel('Scramble up & down distance from pin (yds)')
                ax4.set_ylabel('Scramble up & down miss from pin (ft)')
                with cols[3]:
                    st.pyplot(fig4)

    st.markdown("<hr style='margin-top:2em;margin-bottom:0.5em;'>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;font-size:1.1em;'>Made with ❤️ by dad 👨🏻.</div>", unsafe_allow_html=True)

if __name__ == '__main__':
    main()
