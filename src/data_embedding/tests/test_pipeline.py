"""
Test script for the complete ingestion pipeline with team assignment
"""
import sys
import os

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.ingestion_pipeline import run_ingestion_pipeline

# Test company ID
TEST_COMPANY_ID = "fb140d33-7e96-474d-a06d-ab3a6c65d1a9"

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 TESTING COMPLETE PIPELINE")
    print("="*80)
    print(f"Company ID: {TEST_COMPANY_ID}")
    print("="*80 + "\n")
    
    try:
        run_ingestion_pipeline(TEST_COMPANY_ID)
        
        print("\n" + "="*80)
        print("✅ TEST COMPLETED SUCCESSFULLY!")
        print("="*80)
        
    except Exception as e:
        print("\n" + "="*80)
        print("❌ TEST FAILED!")
        print("="*80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
