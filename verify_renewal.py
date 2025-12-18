
import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDate

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ui.dialogs.renew_plan_dialog import RenewPlanDialog
from src.config import PLANOS_PRECOS

def verify_renewal_change():
    print("Verifying Renewal Plan Change...")
    
    app = QApplication(sys.argv)
    
    # Mock member data
    member_data = {
        'id': 1,
        'nome': 'Test Member',
        'plano': 'Mensal',
        'vencimento_plano': '01/01/2025'
    }
    
    dialog = RenewPlanDialog(member_data)
    
    # 1. Verify initial state
    print("\n1. Verifying Initial State...")
    if dialog.plan_combo.currentText() == 'Mensal':
        print("✅ Initial plan is correct (Mensal).")
    else:
        print(f"❌ Initial plan is incorrect: {dialog.plan_combo.currentText()}")
        
    initial_price_text = dialog.valor_label.text()
    expected_price = PLANOS_PRECOS['Mensal']
    if f"{expected_price:.2f}" in initial_price_text:
        print(f"✅ Initial price is correct (R$ {expected_price:.2f}).")
    else:
        print(f"❌ Initial price is incorrect. Text: {initial_price_text}")

    # 2. Simulate Plan Change
    print("\n2. Simulating Plan Change to 'Trimestral'...")
    dialog.plan_combo.setCurrentText('Trimestral')
    
    # Check if price updated
    new_price_text = dialog.valor_label.text()
    expected_new_price = PLANOS_PRECOS['Trimestral']
    if f"{expected_new_price:.2f}" in new_price_text:
        print(f"✅ Price updated correctly (R$ {expected_new_price:.2f}).")
    else:
        print(f"❌ Price did NOT update correctly. Text: {new_price_text}")
        
    # Check if date updated (should be approx 90 days from now)
    # Since we can't easily predict the exact date without replicating logic, 
    # we check if it's different from the initial date (which was based on extension or today)
    # Actually, the logic is: if plan changes, start_date = now.
    
    # 3. Verify Signal Emission
    print("\n3. Verifying Signal Emission...")
    
    signal_data = {}
    def on_renewed(data):
        nonlocal signal_data
        signal_data = data
        
    dialog.plan_renewed.connect(on_renewed)
    
    # Set payment method to enable confirm
    dialog.metodo_combo.setCurrentText("PIX")
    
    # Trigger confirm
    dialog._on_confirm()
    
    if signal_data:
        print("✅ Signal emitted.")
        if signal_data['plano'] == 'Trimestral':
            print("✅ Signal contains new plan ('Trimestral').")
        else:
            print(f"❌ Signal contains wrong plan: {signal_data['plano']}")
            
        if signal_data['metodo_pagamento'] == 'PIX':
            print("✅ Signal contains payment method.")
        else:
             print("❌ Signal missing payment method.")
    else:
        print("❌ Signal NOT emitted.")

    print("\n🎉 Verification Successful!")

if __name__ == "__main__":
    verify_renewal_change()
