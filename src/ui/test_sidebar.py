import sys
import os
from PyQt6.QtWidgets import QApplication

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.ui.components.sidebar import Sidebar, SidebarContext

def test_sidebar_elements():
    app = QApplication(sys.argv)
    sidebar = Sidebar()
    
    print(f"Initial Context: {sidebar.current_context}")
    
    # Check buttons in HOME context
    found_reports = False
    print("Buttons in HOME context:")
    for btn in sidebar.buttons:
        print(f" - {btn.text()}")
        if "Relatórios" in btn.text():
            found_reports = True
    
    if found_reports:
        print("PASS: 'Relatórios' button found in HOME context.")
    else:
        print("FAIL: 'Relatórios' button NOT found in HOME context.")

    # Switch to REPORTS context
    print("\nSwitching to REPORTS context...")
    sidebar.set_context(SidebarContext.REPORTS)
    
    found_members = False
    found_financial = False
    
    print("Buttons in REPORTS context:")
    for btn in sidebar.buttons:
        print(f" - {btn.text()}")
        if "Membros" in btn.text() and not "Buscar" in btn.text(): # Simple check
            found_members = True
        if "Financeiro" in btn.text():
            found_financial = True
            
    if found_members:
        print("PASS: 'Membros' button found in REPORTS context.")
    else:
        print("FAIL: 'Membros' button NOT found in REPORTS context.")
        
    if found_financial:
        print("PASS: 'Financeiro' button found in REPORTS context.")
    else:
        print("FAIL: 'Financeiro' button NOT found in REPORTS context.")

if __name__ == "__main__":
    test_sidebar_elements()
