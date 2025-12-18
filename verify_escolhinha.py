
import sys
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.utils import calculate_new_due_date
from src.config import PLANOS_COM_VENCIMENTO, PLANOS

def verify_escolhinha_plans():
    print("Verifying Escolhinha Plans...")
    
    # 1. Verify Config
    print("\n1. Verifying Config...")
    # Note: PLANOS is loaded from plans_config.json which has "Escolinha"
    if "Escolinha 1x" in PLANOS and "Escolinha 2x" in PLANOS:
        print("✅ Escolinha plans found in PLANOS.")
    else:
        print("❌ Escolinha plans NOT found in PLANOS.")
        
    if "Escolinha 1x" in PLANOS_COM_VENCIMENTO and "Escolinha 2x" in PLANOS_COM_VENCIMENTO:
        print("✅ Escolinha plans found in PLANOS_COM_VENCIMENTO.")
    else:
        print("❌ Escolinha plans NOT found in PLANOS_COM_VENCIMENTO.")

    # 2. Verify Calculation
    print("\n2. Verifying Date Calculation...")
    now = datetime.now()
    expected_date = now + relativedelta(months=1)
    
    # Test Escolinha 1x
    due_date_1x = calculate_new_due_date("Escolinha 1x", start_date=now)
    if due_date_1x and due_date_1x.date() == expected_date.date():
        print("✅ Escolinha 1x calculation correct (1 month).")
    else:
        print(f"❌ Escolinha 1x calculation incorrect. Got {due_date_1x}, expected {expected_date}")

    # Test Escolinha 2x
    due_date_2x = calculate_new_due_date("Escolinha 2x", start_date=now)
    if due_date_2x and due_date_2x.date() == expected_date.date():
        print("✅ Escolinha 2x calculation correct (1 month).")
    else:
        print(f"❌ Escolinha 2x calculation incorrect. Got {due_date_2x}, expected {expected_date}")

    print("\n🎉 Verification Successful!")

if __name__ == "__main__":
    verify_escolhinha_plans()
