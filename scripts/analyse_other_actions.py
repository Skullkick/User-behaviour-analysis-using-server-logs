import pandas as pd
import re
from pathlib import Path
import plotly.express as px
import plotly.io as pio

def reclassify_events(input_file, output_dir=r"D:\MAJOR PROJECT\User behaviour analysis using server logs\data\processed_logs", report_dir=r"D:\MAJOR PROJECT\User behaviour analysis using server logs\reports"):
    """
    Reclassify 'Other_Action' events into specific categories and generate a distribution chart.
    
    Args:
        input_file (str): Path to the input CSV file (e.g., event_logs.csv).
        output_dir (str): Directory to save the refined event logs.
        report_dir (str): Directory to save the report and visualization.
    
    Returns:
        tuple: (Path to event_logs_refined.csv, Path to refined_event_distribution.png)
    """
    # Ensure output directories exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(report_dir).mkdir(parents=True, exist_ok=True)
    
    # Output file paths
    output_file = Path(output_dir) / "event_logs_refined.csv"
    viz_file = Path(report_dir) / "refined_event_distribution.png"
    table_file = Path(report_dir) / "refined_event_distribution.md"
    
    # Load event logs
    df = pd.read_csv(input_file)
    df['TimeStamp'] = pd.to_datetime(df['TimeStamp'])
    
    # Filter "Other_Action" events
    other_actions = df[df['Event'] == 'Other_Action'].copy()
    
    # Reclassify "Other_Action" events
    def reclassify_event(row):
        page_url = str(row['Page_URL']).lower() if pd.notna(row['Page_URL']) else ''
        referrer_url = str(row['Referrer_URL']).lower() if pd.notna(row['Referrer_URL']) else ''
        if 'search' in page_url or 'q=' in page_url:
            return 'Search'
        elif page_url.startswith('/c-') or '/category/' in page_url or bool(re.match(r'(/[a-zA-Z0-9_-]+){2,}/', page_url)):
            return 'Category_View'
        elif 'login' in page_url or 'account' in page_url or 'logout' in page_url:
            return 'Account_Action'
        elif 'contact' in page_url or 'about' in page_url or 'faq' in page_url:
            return 'Static_Page_View'
        elif 'checkout' in page_url:
            return 'Checkout_View'
        else:
            return 'Other_Action'
    
    other_actions['Refined_Event'] = other_actions.apply(reclassify_event, axis=1)
    df.loc[df['Event'] == 'Other_Action', 'Event'] = other_actions['Refined_Event']
    
    # Calculate event distribution
    event_dist = df['Event'].value_counts().reset_index()
    event_dist.columns = ['Event', 'Count']
    event_dist['Percentage'] = (event_dist['Count'] / event_dist['Count'].sum() * 100).round(2)
    
    # Save distribution table
    with open(table_file, "w") as f:
        f.write(event_dist.to_markdown(index=False))
    
    # Generate bar chart
    fig = px.bar(
        event_dist,
        x='Count',
        y='Event',
        orientation='h',
        title='Refined Event Distribution After Breaking Down "Other_Action"',
        color='Count',
        color_continuous_scale='Blues',
        text='Count'
    )
    fig.update_traces(
        textposition='outside',
        textfont=dict(size=12, color='black'),
        marker=dict(line=dict(color='black', width=1))
    )
    fig.update_layout(
        xaxis_title='Count',
        yaxis_title='Event Type',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=150, r=100, t=80, b=50),
        height=max(400, len(event_dist) * 50)
    )
    pio.write_image(fig, viz_file, format='png', width=800, height=max(400, len(event_dist) * 50))
    
    # Save updated event logs
    df.to_csv(output_file, index=False)
    
    return str(output_file), str(viz_file)