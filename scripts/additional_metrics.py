import pandas as pd

df = pd.read_csv('D:\\Major Project\\User behaviour analysis using server logs\\data\\processed_logs\\event_logs.csv')
df['TimeStamp'] = pd.to_datetime(df['TimeStamp'])

# Calculate session duration (minutes)
session_duration = df.groupby('Session_ID')['TimeStamp'].agg(lambda x: (x.max() - x.min()).total_seconds() / 60)
print(f"Average session duration: {session_duration.mean():.2f} minutes")
print(f"Session duration stats:\n{session_duration.describe()}")

with open(r'D:\Major Project\User behaviour analysis using server logs\reports\additional_metrics.txt', 'a') as f:
    f.write(f"\nAverage session duration: {session_duration.mean():.2f} minutes\n")
    f.write(f"Session duration stats:\n{session_duration.describe().to_string()}\n")