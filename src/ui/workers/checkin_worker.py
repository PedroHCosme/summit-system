"""Worker para realizar check-in."""

from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

from src.data.db import get_db_session
from src.services.checkin_service import CheckinService


class CheckinWorker(QThread):
    """
    Thread para realizar check-in sem travar a GUI.
    
    Responsável por:
    1. Criar sessão própria de banco de dados
    2. Instanciar CheckinService
    3. Executar check-in
    4. Retornar resultado
    """
    
    # Sinais
    checkin_completed = pyqtSignal(bool, str, dict) # success, message, details
    
    def __init__(self, member_id):
        """
        Inicializa o worker.
        
        Args:
            member_id: ID do membro a fazer check-in
        """
        super().__init__()
        self.member_id = member_id
    
    def run(self):
        """Executa o check-in."""
        try:
            with get_db_session() as session:
                service = CheckinService(db_session=session)
                
                # Realizar check-in
                result = service.perform_checkin(self.member_id)
                
                # Preparar detalhes do resultado
                details = {
                    'checkin_id': result.checkin_id,
                    'payment_generated': result.payment_generated,
                    'payment_amount': result.payment_amount
                }
                
                self.checkin_completed.emit(
                    result.success, 
                    result.message, 
                    details
                )
                
        except Exception as e:
            self.checkin_completed.emit(False, f"Erro sistêmico ao realizar check-in: {str(e)}", {})
