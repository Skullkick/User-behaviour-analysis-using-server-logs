import pandas as pd
import re
from pathlib import Path
import plotly.express as px
import plotly.io as pio

# Directory for saving outputs
output_dir = Path(r'D:\MAJOR PROJECT\User behaviour analysis using server logs\reports')
output_dir.mkdir(parents=True, exist_ok=True)

# Step 1: Load the event logs
df = pd.read_csv(r'D:\MAJOR PROJECT\User behaviour analysis using server logs\data\processed_logs\event_logs.csv')
df['TimeStamp'] = pd.to_datetime(df['TimeStamp'])

# Step 2: Filter "Other_Action" events
other_actions = df[df['Event'] == 'Other_Action'].copy()

# Step 3: Define a function to reclassify "Other_Action" events based on URL patterns
def reclassify_event(row):
    page_url = str(row['Page_URL']).lower() if pd.notna(row['Page_URL']) else ''
    referrer_url = str(row['Referrer_URL']).lower() if pd.notna(row['Referrer_URL']) else ''
    
    # Define new event types based on URL patterns
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
        return 'Other_Action'  # Still unclassified

# Apply reclassification to "Other_Action" events
other_actions['Refined_Event'] = other_actions.apply(reclassify_event, axis=1)

# Step 4: Update the main DataFrame with refined events
df.loc[df['Event'] == 'Other_Action', 'Event'] = other_actions['Refined_Event']

# Step 5: Calculate the new event distribution
event_dist = df['Event'].value_counts().reset_index()
event_dist.columns = ['Event', 'Count']
event_dist['Percentage'] = (event_dist['Count'] / event_dist['Count'].sum() * 100).round(2)

# Print the new event distribution table
print("\nNew Event Distribution After Reclassifying 'Other_Action':")
print(event_dist.to_markdown(index=False))

# Save the table to a Markdown file
with open(output_dir / "refined_event_distribution.md", "w") as f:
    f.write(event_dist.to_markdown(index=False))

# Step 6: Generate a bar chart for the new event distribution
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
pio.write_image(fig, output_dir / 'refined_event_distribution.png', format='png', width=800, height=max(400, len(event_dist) * 50))

# Step 7: Save the updated event logs
df.to_csv(r'D:\MAJOR PROJECT\User behaviour analysis using server logs\data\processed_logs\event_logs_refined.csv', index=False)

print("\nRefined event logs saved to 'event_logs_refined.csv'")
print("Refined event distribution chart saved to 'refined_event_distribution.png'")