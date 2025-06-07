import pandas as pd
import os

def analyze_add_to_cart_distribution(event_log_path, report_dir):
    """
    Analyze Add_to_Cart event distribution per session.

    Parameters:
    - event_log_path: Path to the event logs CSV file.
    - report_dir: Directory to save the analysis report.

    Returns:
    - results: dict with textual summary and report file path.
    """
    df = pd.read_csv(event_log_path)

    # Count Add_to_Cart events per session
    cart_events = df[df['Event'] == 'Add_to_Cart'].groupby('Session_ID').size()

    # Summary statistics as string
    stats_str = cart_events.describe().to_string()
    top5_str = cart_events.sort_values(ascending=False).head(5).to_string()

    summary = (
        "Add_to_Cart Events per Session Stats:\n"
        f"{stats_str}\n\n"
        "Top 5 Sessions by Add_to_Cart Events:\n"
        f"{top5_str}"
    )

    # Ensure report directory exists
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "add_to_cart_distribution.txt")

    # Save the report (append mode)
    with open(report_path, 'a') as f:
        f.write("\n" + summary + "\n")

    # Return the results dictionary
    return {
        "textual_data": {
            "Add_to_Cart Distribution": summary
        },
        "report_path": report_path
    }
