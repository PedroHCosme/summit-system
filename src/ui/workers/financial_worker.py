from PyQt6.QtCore import QThread, pyqtSignal
from datetime import datetime
from typing import Dict, Any, List

class FinancialDataWorker(QThread):
    """
    Worker para realizar o carregamento pesado de dados financeiros em background.
    """
    # Sinais emitidos quando os dados são carregados ou ocorre erro
    data_loaded = pyqtSignal(dict)  # Retorna um dict contendo summary, breakdown e transactions
    error_occurred = pyqtSignal(str)

    def __init__(self, data_provider, start_datetime: datetime, end_datetime: datetime):
        super().__init__()
        self.data_provider = data_provider
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime

    def run(self):
        try:
            # Busca do Banco de Dados
            summary = self.data_provider.get_financial_summary(
                self.start_datetime, self.end_datetime
            )
            
            breakdown = self.data_provider.get_revenue_breakdown(
                self.start_datetime, self.end_datetime
            )
            
            transactions = self.data_provider.get_transactions_in_range(
                self.start_datetime, self.end_datetime
            )
            
            # Envelopa os resultados
            result = {
                'summary': summary,
                'breakdown': breakdown,
                'transactions': transactions
            }
            
            self.data_loaded.emit(result)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(str(e))
