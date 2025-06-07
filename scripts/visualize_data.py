import pandas as pd
import matplotlib.pyplot as plt
import os

def generate_visualizations_and_text(input_file, report_dir):
    df = pd.read_csv(input_file)
    output = {
        "visualizations": {},
        "textual_data": {}
    }

    # Ensure output directory exists
    os.makedirs(report_dir, exist_ok=True)

    # 1. Event distribution plot
    event_counts = df['Event'].value_counts()
    plot_path = os.path.join(report_dir, 'event_distribution.png')

    plt.figure(figsize=(8, 6))
    event_counts.plot(kind='bar', color='skyblue')
    plt.title('Event Distribution in E-Commerce Sessions')
    plt.xlabel('Event Type')
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()

    # 2. Textual stats
    total_events = len(df)
    event_percentages = (event_counts / total_events * 100).round(2)
    markdown_text = "### Event Distribution (in %)\n"
    for event, pct in event_percentages.items():
        markdown_text += f"- {event}: {pct}%\n"

    output["visualizations"]["Event Distribution"] = plot_path
    output["textual_data"]["Event Distribution"] = markdown_text

    return output
