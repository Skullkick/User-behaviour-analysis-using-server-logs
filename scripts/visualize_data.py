import pandas as pd
import matplotlib.pyplot as plt

# Load event logs
df = pd.read_csv('D:\\Major Project\\User behaviour analysis using server logs\\data\\processed_logs\\event_logs.csv')

# Event distribution
event_counts = df['Event'].value_counts()

# Plot
plt.figure(figsize=(8, 6))
event_counts.plot(kind='bar', color='skyblue')
plt.title('Event Distribution in E-Commerce Sessions')
plt.xlabel('Event Type')
plt.ylabel('Count')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(r'D:\MAJOR PROJECT\User behaviour analysis using server logs\reports\event_distribution.png')
plt.show()