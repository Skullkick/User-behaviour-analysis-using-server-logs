import pandas as pd
import matplotlib.pyplot as plt
import os

def analyze_ltl_violations(input_file, report_dir, session_to_inspect="3560PL_6"):
    os.makedirs(report_dir, exist_ok=True)
    df = pd.read_csv(input_file)

    ltl_property = "G !(Add_to_Cart ∧ X Add_to_Cart)"

    # Event sequences by session
    event_sequences = df.groupby('Session_ID')['Event'].apply(list).reset_index()

    # Save event_sequences for reference (optional)
    event_sequences.to_csv(os.path.join(report_dir, 'event_sequences.csv'), index=False)

    # LTL violation check function
    def check_consecutive_adds(sequence):
        return [(i, sequence[i], sequence[i+1]) for i in range(len(sequence)-1)
                if sequence[i] == 'Add_to_Cart' and sequence[i+1] == 'Add_to_Cart']

    # Session-specific inspection
    inspect_sequence = df[df['Session_ID'] == session_to_inspect]['Event'].tolist()
    inspect_violations = check_consecutive_adds(inspect_sequence)

    # All sessions
    all_violations = {
        session: check_consecutive_adds(seq)
        for session, seq in zip(event_sequences['Session_ID'], event_sequences['Event'])
        if any(check_consecutive_adds(seq))
    }

    # Plot with data labels inside bars
    violation_count = len(all_violations)
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(['Sessions with Violations', 'Sessions without Violations'],
                  [violation_count, len(event_sequences) - violation_count],
                  color=['red', 'green'])
    ax.set_title('Sessions with Consecutive Add_to_Cart Violations')
    ax.set_ylabel('Number of Sessions')
    
    # Add data labels inside the bars
    ax.bar_label(bars, labels=[f'{violation_count}', f'{len(event_sequences) - violation_count}'], 
                 label_type='center', fontsize=10, color='black', weight='bold')
    
    vis_path = os.path.join(report_dir, 'violation_distribution.png')
    plt.savefig(vis_path)
    plt.close()

    # Return results
    textual_report = f"""
### LTL Property Checked
- **Property**: {ltl_property}
- **Session Analyzed**: {session_to_inspect}
- **Total Sessions**: {len(event_sequences)}
- **Violations Found**: {violation_count}

### Example: {session_to_inspect}
- **Events**: {inspect_sequence[:20]}
- **Violations**: {inspect_violations}

### Sessions with Violations:
- Count: {violation_count}
"""

    return {
        "visualizations": {"LTL Violation Distribution": vis_path},
        "textual_data": {"LTL Analysis": textual_report.strip()}
    }