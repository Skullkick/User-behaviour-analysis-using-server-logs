import pandas as pd
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from pathlib import Path
import plotly.io as pio

# Ensure output directory exists
output_dir = Path(r'D:\MAJOR PROJECT\User behaviour analysis using server logs\reports')
output_dir.mkdir(parents=True, exist_ok=True)

# Apply Seaborn styling directly
sns.set_style("whitegrid")

# Step 1: Load the event logs
df = pd.read_csv(r'D:\MAJOR PROJECT\User behaviour analysis using server logs\data\processed_logs\event_logs.csv')
df['TimeStamp'] = pd.to_datetime(df['TimeStamp'])

# Step 2: Define the website structure and mapping rules
def infer_category(page_url, referrer_url):
    """
    Infer main category from Page_URL and Referrer_URL.
    Returns (main_category) or (None) if not applicable.
    Subcategory is no longer used.
    """
    if pd.isna(page_url) and pd.isna(referrer_url):
        return None
    
    main_category = None
    
    # Check Page_URL for patterns
    if isinstance(page_url, str):
        # Cart-related actions (e.g., /do_koszyka/, /cart/, /koszyk.html)
        if 'do_koszyka' in page_url.lower() or page_url.startswith('/cart/') or 'koszyk.html' in page_url.lower():
            return 'Cart'
        # Product pages (e.g., /p-5315.html)
        elif page_url.startswith('/p-'):
            return 'Product'
        # Informational pages (e.g., /inne/informacja_online.php)
        elif page_url.startswith('/inne/'):
            return 'Info'
        # General URL path splitting for category (e.g., /category/subcategory/page)
        path_parts = page_url.strip('/').split('/')
        if len(path_parts) >= 1:
            main_category = path_parts[0].capitalize()
            return main_category
    
    # Check Referrer_URL for additional context (e.g., https://shop.../p-5315.html)
    if isinstance(referrer_url, str):
        if 'do_koszyka' in referrer_url.lower():
            return 'Cart'
        elif '/p-' in referrer_url:
            return 'Product'
        # Split referrer URL path
        referrer_path = referrer_url.split('://')[-1].split('/', 1)[-1] if '://' in referrer_url else referrer_url
        path_parts = referrer_path.strip('/').split('/')
        if len(path_parts) >= 1:
            main_category = path_parts[0].capitalize()
            return main_category
    
    return main_category

# Step 3: Map events to propositions
def map_event_to_proposition(event, page_url, referrer_url):
    """
    Map an event to an LTL proposition, incorporating website hierarchy.
    Returns a tuple (proposition, level, main_category).
    Subcategory is no longer used.
    """
    main_category = infer_category(page_url, referrer_url)
    
    # Base proposition based on event type
    prop, level = None, None
    if event == 'Info_Page_View':
        prop = 'info_page_view'
        level = 'v^1'
    elif event == 'Product_View':
        prop = 'product_view'
        level = 'v^1'
    elif event == 'Add_to_Cart':
        prop = 'add_to_cart'
        level = None
    elif event == 'Other_Action':
        prop = 'other_action'
        level = None
    else:
        prop = 'unknown'
        level = None
    
    # Add hierarchical context if applicable
    if main_category and level:
        prop = f"{level} & {main_category.lower()}"
    
    return prop, level, main_category

# Apply mapping to each event
mapping_results = df.apply(
    lambda row: map_event_to_proposition(row['Event'], row.get('Page_URL', None), row.get('Referrer_URL', None)),
    axis=1
)
df['Proposition'], df['Level'], df['Main_Category'] = zip(*mapping_results)

# Step 4: Create a mapping table and save as an enhanced image
mapping_table = df[['Page_URL', 'Referrer_URL', 'Event', 'Proposition', 'Main_Category']].drop_duplicates()
mapping_table = mapping_table.sort_values(by='Event')

# Ensure variety of events by sampling up to 3 rows per event type
max_rows_per_event = 3
event_groups = mapping_table.groupby('Event')
sampled_mapping_table = pd.concat([
    group.head(max_rows_per_event) for _, group in event_groups
])
# Sort again by Event to keep the table organized
sampled_mapping_table = sampled_mapping_table.sort_values(by='Event')

# Limit the table to a manageable number of rows for rendering
max_rows = 10
if len(sampled_mapping_table) > max_rows:
    mapping_table_display = sampled_mapping_table.head(max_rows)
    table_title = f'Event Mapping Table (First {max_rows} Rows of {len(sampled_mapping_table)})'
else:
    mapping_table_display = sampled_mapping_table
    table_title = 'Event Mapping Table'

# Define columns to display (Subcategory is removed)
columns_to_display = ['Page_URL', 'Referrer_URL', 'Event', 'Proposition', 'Main_Category']

# Enhanced table visualization
fig, ax = plt.subplots(figsize=(14, len(mapping_table_display) * 0.6))
ax.axis('off')

# Create table with improved styling
table = ax.table(
    cellText=mapping_table_display[columns_to_display].values,
    colLabels=columns_to_display,
    cellLoc='center',
    loc='center',
    colColours=['#f0f0f0'] * len(columns_to_display),  # Light gray header
    cellColours=[['#ffffff'] * len(columns_to_display)] * len(mapping_table_display),
    bbox=[0, 0, 1, 1]
)
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 1.5)

# Style table cells
for (i, j), cell in table.get_celld().items():
    if i == 0:  # Header row
        cell.set_text_props(weight='bold', color='black')
        cell.set_facecolor('#d3d3d3')
    else:  # Data rows
        cell.set_text_props(color='black')
        cell.set_facecolor('#f9f9f9' if i % 2 == 0 else '#ffffff')
    cell.set_edgecolor('gray')

plt.title(table_title, fontsize=14, pad=20, weight='bold')
plt.savefig(output_dir / 'event_mapping_table.png', bbox_inches='tight', dpi=300)
plt.close()

# Step 5: Save the updated event logs and mapping table
df.to_csv(r'D:\MAJOR PROJECT\User behaviour analysis using server logs\data\processed_logs\event_logs_with_propositions.csv', index=False)
mapping_table.to_csv(r'D:\MAJOR PROJECT\User behaviour analysis using server logs\data\processed_logs\event_mapping_table.csv', index=False)

# Step 6: Create an enhanced bar chart for the summary of propositions using Plotly
proposition_counts = df['Proposition'].value_counts().reset_index()
proposition_counts.columns = ['Proposition', 'Count']

# Create a horizontal bar chart with Plotly
fig = px.bar(
    proposition_counts,
    y='Proposition',
    x='Count',
    orientation='h',
    title='Summary of Propositions',
    color='Count',
    color_continuous_scale='Blues',
    text='Count'
)
fig.update_traces(
    textposition='outside',  # Place text outside the bars
    textfont=dict(size=12, color='black'),
    texttemplate='%{text}',  # Ensure text is displayed
    marker=dict(line=dict(color='black', width=1))  # Add border to bars for contrast
)
fig.update_layout(
    title=dict(font=dict(size=16, family='Arial', color='black'), x=0.5),
    xaxis_title='Count',
    yaxis_title='Proposition',
    font=dict(family='Arial', size=12, color='black'),
    plot_bgcolor='white',
    paper_bgcolor='white',
    margin=dict(l=150, r=100, t=80, b=50),  # Increased right margin for text
    height=max(400, len(proposition_counts) * 50)
)
fig.update_xaxes(
    showgrid=True,
    gridcolor='lightgray',
    title=dict(font=dict(size=12, color='black'))
)
fig.update_yaxes(
    tickfont=dict(size=10),
    tickangle=0,
    title=dict(font=dict(size=12, color='black'))
)

# Save the Plotly chart as an image
pio.write_image(fig, output_dir / 'proposition_summary.png', format='png', width=800, height=max(400, len(proposition_counts) * 50))

# Step 7: Generate an HTML report as an alternative display method
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
    </style>
</head>
<body>
    <h1>Event Mapping Report</h1>
    <h2>Event Mapping Table (First 10 Rows)</h2>
    {mapping_table_html}
    <h2>Summary of Propositions</h2>
    <img src="proposition_summary.png" alt="Proposition Summary">
</body>
</html>
"""

# Convert mapping table to HTML
mapping_table_html = mapping_table_display[columns_to_display].to_html(index=False, classes='table', border=0)
html_content = html_content.format(mapping_table_html=mapping_table_html)

# Save the HTML report
with open(output_dir / 'event_mapping_report.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

# Step 8: Notify about saved files
print("Images saved: 'event_mapping_table.png', 'proposition_summary.png'")
print("HTML report saved: 'event_mapping_report.html'")
print("Files saved: 'event_logs_with_propositions.csv', 'event_mapping_table.csv'")