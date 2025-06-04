import pandas as pd

# Load event logs
df = pd.read_csv('D:\\Major Project\\User behaviour analysis using server logs\\data\\processed_logs\\event_logs.csv')

# 1. Conversion Rate: Percentage of sessions with Add_to_Cart
cart_sessions = df[df['Event'] == 'Add_to_Cart']['Session_ID'].nunique()
total_sessions = df['Session_ID'].nunique()
conversion_rate = (cart_sessions / total_sessions) * 100
print(f"Percentage of sessions with Add_to_Cart: {conversion_rate:.2f}%")
print(f"Sessions with Add_to_Cart: {cart_sessions} out of {total_sessions}")

# 2. Common Event Transitions
df['next_event'] = df.groupby('Session_ID')['Event'].shift(-1)
event_transitions = df.groupby(['Event', 'next_event']).size().reset_index(name='count')
print("\nTop 5 Event Transitions:")
print(event_transitions.sort_values(by='count', ascending=False).head(5))

# Save results to a file
with open(r'E:\Major Project\User behaviour analysis using server logs\reports\analysis_results.txt', 'w') as f:
    f.write(f"Percentage of sessions with Add_to_Cart: {conversion_rate:.2f}%\n")
    f.write(f"Sessions with Add_to_Cart: {cart_sessions} out of {total_sessions}\n")
    f.write("\nTop 5 Event Transitions:\n")
    f.write(event_transitions.sort_values(by='count', ascending=False).head(5).to_string())