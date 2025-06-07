import pandas as pd
import logging
from urllib.parse import urlparse
import os
from pathlib import Path

def sessionize_and_classify(input_file, output_dir=r"D:\MAJOR PROJECT\User behaviour analysis using server logs\data\processed_logs"):
    """
    Transform processed logs into event logs with session IDs and event categories.
    
    Args:
        input_file (str): Path to the input CSV file (e.g., processed_data.csv).
        output_dir (str): Directory to save the output event log.
    
    Returns:
        str: Path to the output CSV file (event_logs.csv).
    """
    # Set up logging
    log_file = os.path.join(output_dir, "sessions.log")
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')
    
    # Define output file path
    output_file = os.path.join(output_dir, "event_logs.csv")
    
    # Load dataset
    try:
        df = pd.read_csv(input_file)
        df['TimeStamp'] = pd.to_datetime(df['TimeStamp'], utc=True)
        logging.info(f"Loaded {len(df)} rows from {input_file}")
    except Exception as e:
        logging.error(f"Failed to load CSV: {e}")
        raise
    
    # Sort by IP and TimeStamp
    df = df.sort_values(by=['IP', 'TimeStamp'], ignore_index=True)
    logging.info(f"Sorted data by IP and TimeStamp")
    
    # Filter out non-user actions (e.g., images, CSS, JS)
    non_user_extensions = ['.jpg', '.png', '.gif', '.css', '.js']
    df = df[~df['Page_URL'].str.lower().str.endswith(tuple(non_user_extensions))]
    logging.info(f"Rows after filtering non-user actions: {len(df)}")
    
    # Define session timeout (15 minutes)
    SESSION_TIMEOUT = pd.Timedelta(minutes=15)
    
    # Calculate time differences per IP
    df['time_diff'] = df.groupby('IP')['TimeStamp'].diff().dt.total_seconds() / 60
    logging.info(f"Time difference stats (minutes):\n{df['time_diff'].describe()}")
    
    # Extract domain from Referrer_URL
    def get_domain(url):
        if pd.isna(url) or url == '-':
            return ''
        parsed = urlparse(url)
        return parsed.netloc.lower()
    
    df['referrer_domain'] = df['Referrer_URL'].apply(get_domain)
    logging.info(f"Unique referrer domains: {df['referrer_domain'].nunique()}")
    logging.info(f"Top 5 referrer domains:\n{df['referrer_domain'].value_counts().head(5)}")
    
    # Detect domain changes or empty referrers
    df['domain_change'] = df.groupby('IP')['referrer_domain'].transform(lambda x: (x != x.shift()) | (x == '')).fillna(True)
    logging.info(f"Total domain changes: {df['domain_change'].sum()}")
    
    # Mark new sessions
    df['new_session'] = (df['time_diff'].isna()) | (df['time_diff'] > 15) | (df['domain_change'])
    logging.info(f"Total new sessions marked: {df['new_session'].sum()}")
    
    # Assign session number per IP
    df['session_num'] = df.groupby('IP')['new_session'].cumsum()
    df['Session_ID'] = df['IP'] + '_' + df['session_num'].astype(str)
    
    # Verify session assignment
    sample_ip = df['IP'].iloc[0]
    sample_sessions = df[df['IP'] == sample_ip][['Session_ID', 'TimeStamp', 'time_diff', 'new_session', 'session_num', 'Page_URL', 'Referrer_URL', 'referrer_domain']].head(10)
    logging.info(f"Sample session assignment for IP {sample_ip}:\n{sample_sessions}")
    
    # Categorize events
    def categorize_event(url):
        if '/inne/informacja_online.php' in url:
            return 'Info_Page_View'
        elif 'p-' in url:
            return 'Product_View'
        elif 'koszyk' in url:
            return 'Add_to_Cart'
        else:
            return 'Other_Action'
    
    df['Event'] = df['Page_URL'].apply(categorize_event)
    logging.info(f"Event distribution:\n{df['Event'].value_counts()}")
    
    # Log session and user counts
    total_sessions = df['Session_ID'].nunique()
    total_users = df['IP'].nunique()
    avg_events_per_session = len(df) / total_sessions if total_sessions > 0 else 0
    logging.info(f"Total sessions: {total_sessions}")
    logging.info(f"Total unique IPs: {total_users}")
    logging.info(f"Average events per session: {avg_events_per_session:.2f}")
    
    # Check for duplicates
    duplicate_sessions = df['Session_ID'].duplicated().sum()
    logging.info(f"Duplicate Session_IDs: {duplicate_sessions}")
    if duplicate_sessions > 0:
        logging.warning(f"Found {duplicate_sessions} duplicate Session_IDs. Sample duplicates:\n{df[df['Session_ID'].duplicated(keep=False)][['Session_ID', 'IP', 'TimeStamp', 'Page_URL', 'Referrer_URL', 'referrer_domain']].head(10)}")
    
    # Check sessions per IP
    sessions_per_ip = df.groupby('IP')['Session_ID'].nunique()
    logging.info(f"Sessions per IP (top 5):\n{sessions_per_ip.sort_values(ascending=False).head(5)}")
    
    # Select relevant columns
    event_log_df = df[['Session_ID', 'IP', 'TimeStamp', 'Event', 'Page_URL', 'Method', 'Response', 'Bytes_Sent', 'Referrer_URL', 'User_Agent']]
    
    # Save transformed event log
    try:
        event_log_df.to_csv(output_file, index=False)
        logging.info(f"Saved event log to {output_file}")
    except Exception as e:
        logging.error(f"Failed to save CSV: {e}")
        raise
    
    return output_file