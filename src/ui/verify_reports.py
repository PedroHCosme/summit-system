import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.reports.members_report import generate_members_report
from src.reports.finance_report import generate_finance_report

def verify_reports():
    print("Verifying report generation...")
    
    # 1. Verify Members Report
    try:
        print("Generating Members Report...")
        members_report_path = generate_members_report()
        if os.path.exists(members_report_path):
            print(f"PASS: Members report generated at {members_report_path}")
        else:
            print(f"FAIL: Members report file not found at {members_report_path}")
    except Exception as e:
        print(f"FAIL: Error generating members report: {e}")

    # 2. Verify Finance Report
    try:
        print("Generating Finance Report...")
        finance_report_path = generate_finance_report()
        if os.path.exists(finance_report_path):
            print(f"PASS: Finance report generated at {finance_report_path}")
        else:
            print(f"FAIL: Finance report file not found at {finance_report_path}")
    except Exception as e:
        print(f"FAIL: Error generating finance report: {e}")

if __name__ == "__main__":
    verify_reports()
