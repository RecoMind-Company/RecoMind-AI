import os
import json
from ..graph.state import GraphState

# --- Node Functions --- (Copied from your code)

def save_outputs(state: GraphState):
    """
    Saves the cleaned DataFrame and generated reports to files.
    """
    print("---SAVING OUTPUTS---")
    output_dir = "final_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # === MODIFICATION START: Disabled saving the cleaned DataFrame as requested ===
    # df = state.get('dataframe')
    # if df is not None:
    #     df.to_csv(os.path.join(output_dir, 'cleaned_data.csv'), index=False)
    #     print(f"✅ Cleaned DataFrame saved to '{os.path.join(output_dir, 'cleaned_data.csv')}'")
    # === MODIFICATION END ===

    analysis_report = state.get('analysis_report')
    if analysis_report is not None:
        data_type = state.get('data_type', 'report')
        report_filename = f"{data_type}_analysis_and_recommendations_report.txt"
        with open(os.path.join(output_dir, report_filename), 'w', encoding='utf-8') as f:
            f.write(analysis_report)
        print(f"✅ Comprehensive report saved to '{os.path.join(output_dir, report_filename)}'")

    print("---OUTPUTS SAVED SUCCESSFULLY---")
    return {}

def final_output_viewer(state: GraphState):
    """
    Displays the final outputs for user review before manual saving.
    """
    print("--- ALL PROCESSES COMPLETE ---")
    print("\n--- Final Graph State ---")
    print(f"Data type: {state.get('data_type')}")
    print(f"DataFrame shape after cleaning: {state.get('dataframe').shape if state.get('dataframe') is not None else 'None'}")
    
    kpis = state.get('kpis')
    print("Calculated KPIs:")
    if kpis and 'error' in kpis:
        print(f"❌ Error during KPI calculation: {kpis['error']}")
    else:
        print(json.dumps(kpis, indent=2))
    
    print("\n--- Generated Report ---")
    print(f"Report: {state.get('analysis_report')}")

    print("\n✅ The process has finished. You can now check the 'final_output' directory for the saved files.")
    return {}
