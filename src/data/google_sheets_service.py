"""
Serviço para interação com Google Sheets API.
"""
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from typing import List, Optional


class GoogleSheetsService:
    """Gerencia a autenticação e acesso ao Google Sheets."""
    
    # Escopos de permissão
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    
    def __init__(self, credentials_path: str):
        """
        Inicializa o serviço.
        
        Args:
            credentials_path: Caminho para o arquivo de credenciais JSON
        """
        self.credentials_path = credentials_path
        self.service = None
    
    def authenticate(self) -> bool:
        """
        Autentica com a API do Google Sheets.
        
        Returns:
            True se a autenticação foi bem-sucedida, False caso contrário
        """
        try:
            creds = Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=self.SCOPES
            )
            self.service = build('sheets', 'v4', credentials=creds)
            return True
        except Exception as e:
            print(f"Erro na autenticação: {e}")
            return False
    
    def read_spreadsheet(
        self, 
        spreadsheet_id: str, 
        range_name: str = 'A:BT',
        sheet_name: Optional[str] = None
    ) -> List[list]:
        """
        Lê dados de uma planilha do Google Sheets.
        
        Args:
            spreadsheet_id: ID da planilha
            range_name: Range a ser lido (padrão: 'A:BT')
            sheet_name: Nome da aba (se None, usa apenas o range)
            
        Returns:
            Lista de listas com os valores da planilha
        """
        try:
            if not self.service:
                raise Exception("Serviço não autenticado. Chame authenticate() primeiro.")
            
            # Se um nome de aba foi fornecido, inclui no range
            if sheet_name:
                full_range = f"'{sheet_name}'!{range_name}"
            else:
                full_range = range_name
            
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=full_range
            ).execute()
            
            return result.get('values', [])
        except Exception as e:
            print(f"Erro ao ler planilha: {e}")
            return []