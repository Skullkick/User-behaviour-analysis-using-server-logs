import pandas as pd
from datetime import datetime
import logging
import os,time


def preprocess_logs(input_file, output_dir=r"D:\MAJOR PROJECT\User behaviour analysis using server logs\data\processed_logs"):
    """
    Preprocess raw server logs by cleaning and filtering data.
    
    Args:
        input_file (str): Path to the input CSV file (e.g., eclog_1day.csv).
        output_dir (str): Directory to save the processed output.
    
    Returns:
        tuple: (Path to the output CSV file (processed_data.csv), Time taken in seconds).
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Set up logging
    log_file = os.path.join(output_dir, "preprocess.log")
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')
    
    # Start timing
    start_time = time.time()
    
    # Define output file path
    output_file = os.path.join(output_dir, "processed_data.csv")
    
    # Load dataset
    try:
        df = pd.read_csv(input_file)
        logging.info(f"Loaded {len(df)} rows from {input_file}")
    except Exception as e:
        logging.error(f"Failed to load CSV: {e}")
        raise
    
    # Validate data
    if df['IpId'].isnull().any() or df['TimeStamp'].isnull().any():
        logging.error("Missing IpId or TimeStamp values")
        raise ValueError("Missing IpId or TimeStamp values")
    
    # Convert Windows Timestamp to readable format (UTC)
    try:
        df['TimeStamp'] = pd.to_datetime(df['TimeStamp'].apply(lambda x: (x - 621355968000000000) / 10**7), unit='s', utc=True)
        logging.info(f"Sample timestamps:\n{df['TimeStamp'].head(5)}")
    except Exception as e:
        logging.error(f"Timestamp conversion failed: {e}")
        raise
    
    # Rename columns for clarity
    df.rename(columns={
        'IpId': 'IP',
        'UserId': 'User_ID',
        'HttpMethod': 'Method',
        'Uri': 'Page_URL',
        'HttpVersion': 'HTTP_Version',
        'ResponseCode': 'Response',
        'Bytes': 'Bytes_Sent',
        'Referrer': 'Referrer_URL',
        'UserAgent': 'User_Agent'
    }, inplace=True)
    
    # Remove unnecessary columns
    df.drop(columns=['HTTP_Version', 'User_ID'], inplace=True)
    
    # Filter out bot traffic
    bot_keywords = ['bot', 'crawler', 'spider', 'SemrushBot']
    bot_mask = df['User_Agent'].str.lower().str.contains('|'.join(bot_keywords), na=False)
    bot_rows = df[bot_mask]
    logging.info(f"Rows flagged as bots: {len(bot_rows)}")
    logging.info(f"Sample bot UserAgents:\n{bot_rows['User_Agent'].head(5)}")
    df = df[~bot_mask]
    logging.info(f"Rows after bot filtering: {len(df)}")
    
    # Filter for successful responses
    df = df[df['Response'] == 200]
    logging.info(f"Rows after filtering Response == 200: {len(df)}")
    
    # Save cleaned dataset
    try:
        df.to_csv(output_file, index=False)
        logging.info(f"Saved cleaned data to {output_file}")
    except Exception as e:
        logging.error(f"Failed to save CSV: {e}")
        raise
    
    # End timing
    end_time = time.time()
    duration = end_time - start_time
    logging.info(f"Preprocessing completed in {duration:.2f} seconds")
    
    return output_file, duration