# ltl_conversion_analysis.py
import pandas as pd
import matplotlib.pyplot as plt
import os

def analyze_ltl_conversion(file_path, report_dir):
    df = pd.read_csv(file_path)

    # Define LTL Property
    ltl_property = "G (Product_View → F Add_to_Cart)"

    # Prepare Event Sequences
    event_sequences = df.groupby('Session_ID')['Event'].apply(list).reset_index()
    output_csv = os.path.join(report_dir, "event_sequences_conversion.csv")
    event_sequences.to_csv(output_csv, index=False)

    # Filter sessions with Product_View
    sessions_with_product_view = event_sequences[event_sequences['Event'].apply(lambda x: 'Product_View' in x)]

    def check_conversion_property(sequence):
        if 'Product_View' not in sequence:
            return True
        for i, event in enumerate(sequence):
            if event == 'Product_View':
                if not any(e == 'Add_to_Cart' for e in sequence[i:]):
                    return False
        return True

    # Identify violations
    conversion_violations = {
        session: seq for session, seq in zip(
            sessions_with_product_view['Session_ID'], sessions_with_product_view['Event'])
        if not check_conversion_property(seq)
    }

    violation_count = len(conversion_violations)
    total_product_sessions = len(sessions_with_product_view)

    # Visualization
    plt.figure(figsize=(6, 4))
    plt.bar(['Sessions with Violations', 'Sessions without Violations'],
            [violation_count, total_product_sessions - violation_count], color=['red', 'green'])
    plt.title('Sessions Violating G (Product_View → F Add_to_Cart)')
    plt.ylabel('Number of Sessions')

    img_path = os.path.join(report_dir, "conversion_violation_distribution.png")
    plt.savefig(img_path)
    plt.close()

    # Text Summary
    summary = (
        f"LTL Property: {ltl_property}\n"
        f"Total Sessions with Product_View: {total_product_sessions}\n"
        f"Violations Found: {violation_count}\n"
        f"Violation Session IDs (Sample): {list(conversion_violations.keys())[:5]}\n"
    )

    return {
        "visualizations": {"Conversion Violation Distribution": img_path},
        "textual_data": {"LTL Analysis": summary}
    }
