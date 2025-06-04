import pandas as pd

# Load event logs
df = pd.read_csv('E:\\Major Project\\User behaviour analysis using server logs\\data\\processed_logs\\event_logs.csv')

# Count Add_to_Cart events per session
cart_events = df[df['Event'] == 'Add_to_Cart'].groupby('Session_ID').size()
print("Add_to_Cart Events per Session Stats:")
print(cart_events.describe())
print("\nTop 5 Sessions by Add_to_Cart Events:")
print(cart_events.sort_values(ascending=False).head(5))

# Save results
with open(r'E:\Major Project\User behaviour analysis using server logs\reports\add_to_cart_distribution.txt', 'a') as f:
    f.write("\nAdd_to_Cart Events per Session Stats:\n")
    f.write(cart_events.describe().to_string())
    f.write("\nTop 5 Sessions by Add_to_Cart Events:\n")
    f.write(cart_events.sort_values(ascending=False).head(5).to_string())