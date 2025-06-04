import pandas as pd
import matplotlib.pyplot as plt

# Load dataset
df = pd.read_csv(r'D:\Major Project\User behaviour analysis using server logs\data\processed_logs\event_logs.csv')

# Step 1: Define LTL Property
ltl_property = "G (Product_View → F Add_to_Cart)"  # Every Product_View is eventually followed by Add_to_Cart

# Step 2: Prepare Event Sequences
event_sequences = df.groupby('Session_ID')['Event'].apply(list).reset_index()
event_sequences.to_csv(r'D:\Major Project\User behaviour analysis using server logs\data\processed_logs\event_sequences_conversion.csv', index=False)

# Focus on sessions with Product_View
sessions_with_product_view = event_sequences[event_sequences['Event'].apply(lambda x: 'Product_View' in x)]
print("Sessions with Product_View (Sample):")
print(sessions_with_product_view.head(10))

# Step 3: Check LTL Property
def check_conversion_property(sequence):
    if 'Product_View' not in sequence:
        return True  # No Product_View, property holds by default
    has_product_view = False
    for i, event in enumerate(sequence):
        if event == 'Product_View':
            has_product_view = True
            # Check if Add_to_Cart occurs later
            if not any(e == 'Add_to_Cart' for e in sequence[i:]):
                return False
    return has_product_view  # True if no Product_View or all followed by Add_to_Cart

# Check all sessions with Product_View
conversion_violations = {session: seq for session, seq in zip(sessions_with_product_view['Session_ID'], sessions_with_product_view['Event']) 
                        if not check_conversion_property(seq)}
violation_count = len(conversion_violations)
total_product_sessions = len(sessions_with_product_view)

# Step 4: Visualize Violations
plt.figure(figsize=(6, 4))
plt.bar(['Sessions with Violations', 'Sessions without Violations'], 
        [violation_count, total_product_sessions - violation_count], color=['red', 'green'])
plt.title('Sessions Violating G (Product_View → F Add_to_Cart)')
plt.ylabel('Number of Sessions')
plt.savefig(r'D:\MAJOR PROJECT\User behaviour analysis using server logs\reports\conversion_violation_distribution.png')
plt.close()


# Write Markdown
# with open('final_report_with_ltl_updated.md', 'w', encoding='utf-8') as f:
#     f.write(markdown_content.format(violation_count=violation_count, total_product_sessions=total_product_sessions))

# Print outputs for sharing
print("Sessions with Product_View Violations:")
print({k: v for k, v in conversion_violations.items()})
print(f"\nTotal Sessions with Product_View: {total_product_sessions}")
print(f"Violations of G (Product_View → F Add_to_Cart): {violation_count}")