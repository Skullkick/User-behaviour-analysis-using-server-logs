import pandas as pd
import matplotlib.pyplot as plt

# Load dataset
df = pd.read_csv(r'D:\Major Project\User behaviour analysis using server logs\data\processed_logs\event_logs.csv')

# Step 1: Define LTL Property
ltl_property = "G !(Add_to_Cart ∧ X Add_to_Cart)"  # No consecutive Add_to_Cart events

# Step 2: Prepare Event Sequences
event_sequences = df.groupby('Session_ID')['Event'].apply(list).reset_index()
event_sequences.to_csv(r'D:\Major Project\User behaviour analysis using server logs\data\processed_logs\event_sequences.csv', index=False)

# Focus on 3560PL_6
pl6_sequence = df[df['Session_ID'] == '3560PL_6']['Event'].tolist()

# Step 3: Check LTL Property
def check_consecutive_adds(sequence):
    violations = [(i, sequence[i], sequence[i+1]) for i in range(len(sequence)-1) 
                  if sequence[i] == 'Add_to_Cart' and sequence[i+1] == 'Add_to_Cart']
    return violations

# Check 3560PL_6
pl6_violations = check_consecutive_adds(pl6_sequence)

# Check all sessions
all_violations = {session: check_consecutive_adds(seq) for session, seq in zip(event_sequences['Session_ID'], event_sequences['Event']) 
                  if any(check_consecutive_adds(seq))}
violation_count = len(all_violations)

# Step 4: Visualize Violations
plt.figure(figsize=(6, 4))
plt.bar(['Sessions with Violations', 'Sessions without Violations'], 
        [violation_count, len(event_sequences) - violation_count], color=['red', 'green'])
plt.title('Sessions with Consecutive Add_to_Cart Violations')
plt.ylabel('Number of Sessions')
plt.savefig(r'D:\Major Project\User behaviour analysis using server logs\reports\violation_distribution.png')
plt.close()

# Print outputs for sharing
print("3560PL_6 Sequence (First 20 Events):")
print(pl6_sequence[:20])
print("\nConsecutive Add_to_Cart Pairs in 3560PL_6:")
print(pl6_violations)
print("\nSessions with LTL Violations:")
print({k: v for k, v in all_violations.items() if v})