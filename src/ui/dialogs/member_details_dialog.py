"""Diálogo para exibir detalhes completos de um membro."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser
)
from PyQt6.QtCore import Qt

class MemberDetailsDialog(QDialog):
    """Diálogo que exibe todas as informações de um membro."""
    
    def __init__(self, member_data: dict, parent=None):
        super().__init__(parent)
        self.member_data = member_data
        self.setWindowTitle("Detalhes do Membro")
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Browser para exibir HTML formatado
        self.details_browser = QTextBrowser()
        self.details_browser.setOpenExternalLinks(True)
        layout.addWidget(self.details_browser)
        
        # Botão Fechar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_button = QPushButton("Fechar")
        self.close_button.setMinimumWidth(100)
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # Popula os dados
        self._populate_data()
        
    def _populate_data(self):
        """Formata e exibe os dados do membro."""
        if not self.member_data:
            return
            
        # Extrair dados com valores padrão
        nome = self.member_data.get('nome', 'N/A')
        plano = self.member_data.get('plano', 'N/A')
        estado_plano = self.member_data.get('estado_plano', 'N/A')
        vencimento_plano = self.member_data.get('vencimento_plano', 'N/A')
        
        data_nascimento = self.member_data.get('data_nascimento', 'N/A')
        genero = self.member_data.get('genero', 'N/A')
        calcado = self.member_data.get('calcado', 'N/A')
        
        whatsapp = self.member_data.get('whatsapp', 'N/A')
        email = self.member_data.get('email', 'N/A')
        
        treina = self.member_data.get('treina', 'Não')
        vencimento_treino = self.member_data.get('vencimento_treino', 'N/A')
        
        # Estilização do status
        is_active = estado_plano.upper() == 'ATIVO'
        color = '#28a745' if is_active else '#FF6B6B'
        
        # HTML Template
        html = f"""
        <style>
            h3 {{ color: #007ACC; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 20px; }}
            p {{ font-size: 14px; margin: 5px 0; }}
            .label {{ font-weight: bold; color: #555; }}
            .value {{ color: #333; }}
            .status {{ font-weight: bold; color: {color}; }}
        </style>
        
        <div style='font-family: sans-serif;'>
            <h2 style='text-align: center; color: #333; margin-bottom: 20px;'>{nome}</h2>
            
            <h3>Informações do Plano</h3>
            <p><span class='label'>Plano:</span> <span class='value'>{plano}</span></p>
            <p><span class='label'>Status:</span> <span class='status'>{estado_plano}</span></p>
            <p><span class='label'>Vencimento:</span> <span class='value'>{vencimento_plano}</span></p>
            
            <h3>Dados Pessoais</h3>
            <p><span class='label'>Data de Nascimento:</span> <span class='value'>{data_nascimento}</span></p>
            <p><span class='label'>Gênero:</span> <span class='value'>{genero}</span></p>
            <p><span class='label'>Tamanho do Calçado:</span> <span class='value'>{calcado}</span></p>
            
            <h3>Contato</h3>
            <p><span class='label'>WhatsApp:</span> <span class='value'>{whatsapp}</span></p>
            <p><span class='label'>Email:</span> <span class='value'>{email}</span></p>
            
            <h3>Treino</h3>
            <p><span class='label'>Treina:</span> <span class='value'>{treina}</span></p>
        """
        
        if treina == 'Sim':
            html += f"<p><span class='label'>Vencimento do Treino:</span> <span class='value'>{vencimento_treino}</span></p>"
            
        # Observações
        observacoes = self.member_data.get('observacoes')
        if not observacoes:
            observacoes = "<i>Nenhuma observação registrada.</i>"
        
        html += f"""
            <h3>Observações</h3>
            <p class='value'>{observacoes}</p>
        """
            
        html += "</div>"
        
        self.details_browser.setHtml(html)
