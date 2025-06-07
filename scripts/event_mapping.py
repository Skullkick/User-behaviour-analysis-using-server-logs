import pandas as pd
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from pathlib import Path
import plotly.io as pio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def map_event_to_proposition(input_file, output_dir=r"D:\MAJOR PROJECT\User behaviour analysis using server logs\data\processed_logs", report_dir=r"D:\MAJOR PROJECT\User behaviour analysis using server logs\reports", use_refined=False):
    """
    Map events to LTL propositions and generate mapping table and visualizations.
    
    Args:
        input_file (str): Path to the input CSV file (e.g., event_logs.csv or event_logs_refined.csv).
        output_dir (str): Directory to save output CSV files.
        report_dir (str): Directory to save visualizations and HTML report.
        use_refined (bool): Whether to use refined event logs.
    
    Returns:
        tuple: (Path to event_logs_with_propositions.csv, Path to event_mapping_table.csv,
                Path to event_mapping_table.png, Path to proposition_summary.html,
                Path to proposition_summary.png, Path to summary_insights.txt)
    """
    try:
        # Validate input file
        if not Path(input_file).is_file():
            raise FileNotFoundError(f"Input file {input_file} does not exist")

        # Ensure output directories exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        Path(report_dir).mkdir(parents=True, exist_ok=True)
        
        # Output file paths
        event_logs_output = Path(output_dir) / "event_logs_with_propositions.csv"
        mapping_table_output = Path(output_dir) / "event_mapping_table.csv"
        table_viz = Path(report_dir) / "event_mapping_table.png"
        prop_viz_html = Path(report_dir) / "proposition_summary.html"
        prop_viz_png = Path(report_dir) / "proposition_summary.png"
        html_report = Path(report_dir) / "event_mapping_report.html"
        help_file = Path(report_dir) / "proposition_help.txt"
        summary_insights = Path(report_dir) / "summary_insights.txt"
        
        # Set Seaborn style
        sns.set_style("whitegrid")
        
        # Load event logs
        logging.info(f"Loading event logs from {input_file}")
        required_columns = ['Event', 'TimeStamp']
        df = pd.read_csv(input_file)
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in input file: {missing_cols}")
        logging.info(f"Loaded {len(df)} rows from event logs")
        
        # Convert TimeStamp
        try:
            df['TimeStamp'] = pd.to_datetime(df['TimeStamp'])
        except Exception as e:
            logging.error(f"Failed to convert TimeStamp column: {str(e)}")
            raise ValueError(f"Invalid TimeStamp format: {str(e)}")
        
        # Simplify URLs
        def simplify_url(url):
            if pd.isna(url):
                return "N/A"
            match = re.search(r'/(.*?)(?:\.html|$|\?)', url)
            return match.group(1) if match else url.split('/')[-1] or "N/A"
        
        df['Simplified_Page_URL'] = df.get('Page_URL', pd.Series(dtype=str)).apply(simplify_url)
        
        # Define website structure and mapping rules
        def infer_category(page_url, referrer_url):
            if pd.isna(page_url) and pd.isna(referrer_url):
                return "Other"
            main_category = None
            if isinstance(page_url, str):
                page_url_lower = page_url.lower()
                if 'do_koszyka' in page_url_lower or page_url.startswith('/cart/') or 'koszyk.html' in page_url_lower:
                    return 'Cart'
                elif page_url.startswith('/p-'):
                    return 'Product'
                elif page_url.startswith('/inne/'):
                    return 'Info'
                path_parts = page_url.strip('/').split('/')
                if len(path_parts) >= 1:
                    first_part = path_parts[0].capitalize()
                    if first_part.lower().startswith(('electronics', 'phones', 'laptops', 'computers')):
                        return 'Electronics'
                    elif first_part.lower().startswith(('clothing', 'shoes', 'accessories')):
                        return 'Fashion'
                    elif first_part.lower().startswith(('books', 'ebooks', 'magazines')):
                        return 'Books'
                    elif first_part.lower().startswith(('home', 'kitchen', 'furniture')):
                        return 'Home & Garden'
                    elif first_part.lower().startswith(('sports', 'fitness', 'outdoor')):
                        return 'Sports'
                    else:
                        return first_part if first_part else 'Other'
            if isinstance(referrer_url, str):
                referrer_url_lower = referrer_url.lower()
                if 'do_koszyka' in referrer_url_lower:
                    return 'Cart'
                elif '/p-' in referrer_url:
                    return 'Product'
                referrer_path = referrer_url.split('://')[-1].split('/', 1)[-1] if '://' in referrer_url else referrer_url
                path_parts = referrer_path.strip('/').split('/')
                if len(path_parts) >= 1:
                    first_part = path_parts[0].capitalize()
                    if first_part.lower().startswith(('electronics', 'phones', 'laptops', 'computers')):
                        return 'Electronics'
                    elif first_part.lower().startswith(('clothing', 'shoes', 'accessories')):
                        return 'Fashion'
                    elif first_part.lower().startswith(('books', 'ebooks', 'magazines')):
                        return 'Books'
                    elif first_part.lower().startswith(('home', 'kitchen', "furniture")):
                        return 'Home & Garden'
                    elif first_part.lower().startswith(('sports', 'fitness', 'outdoor')):
                        return 'Sports'
                    else:
                        return first_part if first_part else 'Other'
            return 'Other'
        
        # Map events to propositions and broader event types
        def map_event_to_proposition(event, page_url, referrer_url):
            main_category = infer_category(page_url, referrer_url)
            prop, level = None, None
            event_group = 'Basic'
            event_type = 'Other'
            prop_desc = ''
            if event == 'Info_Page_View':
                prop = 'info_page_view'
                prop_desc = 'Info Page Viewed'
                level = 'v^1'
                event_type = 'View Actions'
            elif event == 'Product_View':
                prop = 'product_view'
                prop_desc = 'Product Page Viewed'
                level = 'v^1'
                event_type = 'View Actions'
            elif event == 'Add_to_Cart':
                prop = 'add_to_cart'
                prop_desc = 'Added to Cart'
                level = None
                event_type = 'Cart Actions'
            elif event == 'Other_Action' and not use_refined:
                prop = 'other_action'
                prop_desc = 'Other Action'
                level = None
                event_type = 'Other'
            elif use_refined:
                event_group = 'Refined'
                if event == 'Search':
                    prop = 'search'
                    prop_desc = 'Search Performed'
                    level = None
                    event_type = 'Search Actions'
                elif event == 'Category_View':
                    prop = 'category_view'
                    prop_desc = 'Category Page Viewed'
                    level = 'v^1'
                    event_type = 'View Actions'
                elif event == 'Account_Action':
                    prop = 'account_action'
                    prop_desc = 'Account Action'
                    level = None
                    event_type = 'Account Actions'
                elif event == 'Static_Page_View':
                    prop = 'static_page_view'
                    prop_desc = 'Static Page Viewed'
                    level = 'v^1'
                    event_type = 'View Actions'
                elif event == 'Checkout_View':
                    prop = 'checkout_view'
                    prop_desc = 'Checkout Viewed'
                    level = None
                    event_type = 'Cart Actions'
                else:
                    prop = 'other_action'
                    prop_desc = 'Other Action'
                    level = None
                    event_type = 'Other'
            else:
                prop = 'unknown'
                prop_desc = 'Unknown Action'
                level = None
                event_type = 'Other'
            if main_category and level:
                prop = f"{level} & {main_category.lower()}"
            return prop, level, main_category, event_group, event_type, prop_desc
        
        # Apply mapping
        logging.info("Mapping events to propositions")
        mapping_results = df.apply(
            lambda row: map_event_to_proposition(row['Event'], row.get('Page_URL', None), row.get('Referrer_URL', None)),
            axis=1
        )
        df['Proposition'], df['Level'], df['Main_Category'], df['Event_Group'], df['Event_Type'], df['Proposition_Desc'] = zip(*mapping_results)
        
        # Create grouped mapping table
        logging.info("Creating event mapping table")
        mapping_table = df.groupby(['Event', 'Event_Group', 'Event_Type', 'Proposition', 'Proposition_Desc', 'Main_Category']).agg({
            'Simplified_Page_URL': lambda x: x.mode()[0] if not x.mode().empty else "N/A",
            'TimeStamp': 'count'
        }).reset_index()
        mapping_table.rename(columns={'TimeStamp': 'Count'}, inplace=True)
        
        # Add Event_Type counts
        event_type_counts = mapping_table.groupby('Event_Type')['Count'].sum().reset_index(name='Event_Type_Count')
        mapping_table = mapping_table.merge(event_type_counts, on='Event_Type')
        mapping_table = mapping_table.sort_values(by=['Event_Type', 'Event', 'Count'], ascending=[True, True, False])
        
        # Limit to top 5 Main_Category for summary rows
        category_counts = df.groupby('Main_Category').size().reset_index(name='Total_Count')
        top_categories = category_counts.nlargest(5, 'Total_Count')
        category_summary = pd.DataFrame(
            [['Summary', '', '', '', '', cat['Main_Category'], cat['Total_Count'], '', ''] for _, cat in top_categories.iterrows()],
            columns=['Event', 'Event_Group', 'Event_Type', 'Proposition', 'Proposition_Desc', 'Main_Category', 'Count', 'Event_Type_Count', '']
        )
        
        # Limit mapping_table to top rows to fit within 10 total rows
        remaining_rows = 10 - len(category_summary)  # e.g., 10 - 5 = 5 rows for event mappings
        mapping_table_limited = mapping_table.head(max(0, remaining_rows))
        
        # Combine summary and mapping table, ensure no empty rows
        mapping_table_display = pd.concat([category_summary, mapping_table_limited]).reset_index(drop=True)
        mapping_table_display = mapping_table_display.dropna(how='all')  # Remove any fully empty rows
        table_title = f'Event Mapping Table (Top 5 Categories + Top {remaining_rows} Events of {len(mapping_table)} Total)'
        
        # Generate table visualization with fixed size
        logging.info("Generating event mapping table visualization")
        fig, ax = plt.subplots(figsize=(16, 6))  # Fixed height for 10 rows
        ax.axis('off')
        columns_to_display = ['Event', 'Event_Type', 'Event_Type_Count', 'Proposition', 'Proposition_Desc', 'Main_Category', 'Count']
        table = ax.table(
            cellText=mapping_table_display[columns_to_display].values,
            colLabels=columns_to_display,
            cellLoc='center',
            loc='center',
            colColours=['#d3d3d3'] * len(columns_to_display),
            cellColours=[['#e6f3ff' if i < len(top_categories) else '#f9f9f9' if i % 2 == 0 else '#ffffff'] * len(columns_to_display) for i in range(len(mapping_table_display))],
            bbox=[0.05, 0.05, 0.9, 0.9]  # Adjust bbox to reduce padding
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)  # Reduce vertical scaling to minimize gaps
        for (i, j), cell in table.get_celld().items():
            cell.set_text_props(wrap=True)
            if i == 0:
                cell.set_text_props(weight='bold', color='black')
                cell.set_facecolor('#d3d3d3')
            elif i < len(top_categories) + 1:
                cell.set_text_props(weight='bold', color='black')
            else:
                cell.set_text_props(color='black')
            cell.set_edgecolor('gray')
            cell.set_height(0.08)  # Fixed row height to reduce gaps
        plt.title(table_title, fontsize=14, pad=15, weight='bold')
        plt.savefig(table_viz, bbox_inches='tight', dpi=300)  # Reduced DPI for smaller file size
        plt.close()
        
        # For CSV, combine Proposition and Description
        mapping_table['Proposition'] = mapping_table.apply(lambda x: f"{x['Proposition']} ({x['Proposition_Desc']})", axis=1)
        mapping_table.drop(columns=['Proposition_Desc'], inplace=True)
        mapping_table.to_csv(mapping_table_output, index=False)
        df.to_csv(event_logs_output, index=False)
        
        # Generate proposition summary chart (limit propositions)
        logging.info("Generating proposition summary chart")
        proposition_counts = df.groupby(['Proposition', 'Proposition_Desc', 'Event_Group', 'Event_Type', 'Main_Category']).size().reset_index(name='Count')
        
        # Log the number of unique propositions
        num_unique_props = len(proposition_counts['Proposition_Desc'].unique())
        logging.info(f"Number of unique Proposition_Desc values: {num_unique_props}")
        
        # Limit Main_Category to top 5 by count, group rest into 'Other'
        top_categories = proposition_counts.groupby('Main_Category')['Count'].sum().nlargest(5).index.tolist()
        proposition_counts['Main_Category_Grouped'] = proposition_counts['Main_Category'].apply(
            lambda x: x if x in top_categories else 'Other'
        )
        
        # Limit Proposition_Desc to top 20 by count, group rest into 'Other'
        top_propositions = proposition_counts.groupby('Proposition_Desc')['Count'].sum().nlargest(20).index.tolist()
        proposition_counts['Proposition_Desc_Grouped'] = proposition_counts['Proposition_Desc'].apply(
            lambda x: x if x in top_propositions else 'Other Proposition'
        )
        # Recompute counts after grouping
        proposition_counts_grouped = proposition_counts.groupby(['Proposition', 'Proposition_Desc_Grouped', 'Event_Group', 'Event_Type', 'Main_Category_Grouped']).agg({'Count': 'sum'}).reset_index()
        
        # Generate summary text based on top propositions
        top_propositions_summary = proposition_counts.groupby(['Event_Type', 'Proposition_Desc'])['Count'].sum().reset_index()
        top_propositions_summary = top_propositions_summary.groupby('Event_Type').apply(lambda x: x.nlargest(3, 'Count')).reset_index(drop=True)
        summary_text = "Top Propositions by Event Type:\n"
        for etype in top_propositions_summary['Event_Type'].unique():
            group_data = top_propositions_summary[top_propositions_summary['Event_Type'] == etype]
            summary_text += f"\n{etype}:\n"
            for _, row in group_data.iterrows():
                summary_text += f"- {row['Proposition_Desc']}: {row['Count']} occurrences\n"
        
        # Create the chart with grouped data
        num_unique_grouped_props = len(proposition_counts_grouped['Proposition_Desc_Grouped'].unique())
        logging.info(f"Number of unique Proposition_Desc_Grouped values after limiting: {num_unique_grouped_props}")
        chart_height = max(600, num_unique_grouped_props * 40)
        logging.info(f"Proposition summary chart height: {chart_height} pixels")
        
        fig = px.bar(
            proposition_counts_grouped,
            y='Proposition_Desc_Grouped',
            x='Count',
            color='Event_Type',
            facet_col='Main_Category_Grouped',
            orientation='h',
            title='Summary of Propositions by Category and Event Type (Top 20 Propositions, Top 5 Categories)',
            text='Count',
            height=chart_height,
            custom_data=['Proposition', 'Event_Type', 'Main_Category_Grouped']
        )
        fig.update_traces(
            textposition='outside',
            textfont=dict(size=12, color='black'),
            marker=dict(line=dict(color='black', width=1)),
            hovertemplate='<b>%{y}</b><br>Count: %{x}<br>Proposition: %{customdata[0]}<br>Event Type: %{customdata[1]}<br>Main Category: %{customdata[2]}'
        )
        fig.update_layout(
            title=dict(font=dict(size=16, family='Arial', color='black'), x=0.5),
            xaxis_title='Count',
            yaxis_title='Proposition',
            font=dict(family='Arial', size=12, color='black'),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=150, r=100, t=80, b=50),
            showlegend=True
        )
        fig.update_xaxes(showgrid=True, gridcolor='lightgray', title=dict(font=dict(size=12, color='black')))
        fig.update_yaxes(tickfont=dict(size=10), tickangle=0, title=dict(font=dict(size=12, color='black')))
        fig.write_html(prop_viz_html)
        fig.write_image(prop_viz_png, width=800, height=chart_height)
        
        # Generate help text
        help_text = """
        Proposition Help:
        Propositions are mapped to events in Linear Temporal Logic (LTL) format for user behavior analysis.
        - 'v^1 & info' (Info Page Viewed): User viewed an informational page (e.g., /inne/) at level 1.
        - 'v^1 & product' (Product Page Viewed): User viewed a product page (e.g., /p-12345/) at level 1.
        - 'add_to_cart' (Added to Cart): User added an item to their cart.
        - 'search' (Search Performed): User performed a search (refined event).
        - 'v^1 & category' (Category Page Viewed): User viewed a category page at level 1.
        """
        with open(help_file, 'w') as f:
            f.write(help_text)
        
        # Save summary insights
        with open(summary_insights, 'w') as f:
            f.write(summary_text)
        
        # Generate HTML report
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Event Mapping Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; text-align: center; }}
                h2 {{ color: #555; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                img {{ max-width: 100%; height: auto; display: block; margin: 20px auto; }}
                pre {{ background-color: #f9f9f9; padding: 10px; border: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <h1>Event Mapping Report</h1>
            <h2>Event Mapping Table (Top 5 Categories + Top Events)</h2>
            {mapping_table_html}
            <h2>Summary of Propositions</h2>
            <iframe src="proposition_summary.html" width="100%" height="600px" frameborder="0"></iframe>
            <h2>Summary Insights</h2>
            <pre>{summary_text}</pre>
            <h2>Proposition Help</h2>
            <pre>{help_text}</pre>
        </body>
        </html>
        """
        mapping_table_html = mapping_table_display[columns_to_display].to_html(index=False, classes='table', border=0)
        html_content = html_content.format(mapping_table_html=mapping_table_html, summary_text=summary_text, help_text=help_text)
        with open(html_report, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logging.info("Event mapping completed successfully")
        return str(event_logs_output), str(mapping_table_output), str(table_viz), str(prop_viz_html), str(prop_viz_png), str(summary_insights)
    except Exception as e:
        logging.error(f"Event mapping failed: {str(e)}")
        raise