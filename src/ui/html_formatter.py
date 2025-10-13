"""
Formatador HTML para exibição de aniversariantes.
Trabalha com objetos da classe Pessoa.
"""
from typing import Optional
from src.core.models import Aniversariante, Pessoa
from src.utils.utils import format_whatsapp_link


class HTMLFormatter:
    """Formata dados de pessoas/aniversariantes em HTML."""
    
    @staticmethod
    def format_header(mes_nome: str) -> str:
        """
        Formata o cabeçalho HTML.
        
        Args:
            mes_nome: Nome do mês
            
        Returns:
            String HTML com o cabeçalho
        """
        return f"""
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #007ACC;">ANIVERSARIANTES DE {mes_nome.upper()}</h2>
                <hr style="border: 1px solid #DDDDDD;">
            </div>
        """
    
    @staticmethod
    def format_pessoa(pessoa: Pessoa) -> str:
        """
        Formata uma pessoa em HTML.
        
        Args:
            pessoa: Objeto Pessoa
            
        Returns:
            String HTML com os dados formatados
        """
        # Formata o link do WhatsApp se houver telefone
        whatsapp_html = ""
        if pessoa.tem_whatsapp():
            whatsapp_link, whatsapp_display = format_whatsapp_link(pessoa.whatsapp)
            if whatsapp_link:
                whatsapp_html = f'WhatsApp: <a href="{whatsapp_link}" style="color: #007ACC; text-decoration: none;">{whatsapp_display}</a><br>'
        
        html = f"""
            <div style="margin-bottom: 15px; padding: 10px; background-color: #F8F8F8; border: 1px solid #DDDDDD; border-radius: 5px;">
                <b style="font-size: 16px; color: #005FA3;">{pessoa.nome}</b><br>
                <span style="margin-left: 20px; color: #555555;">
                    Data: {pessoa.data_nascimento_formatada}<br>
                    Idade: {pessoa.idade} anos<br>
                    Plano: {pessoa.plano}<br>
        """
        
        if whatsapp_html:
            html += f"                    {whatsapp_html}"
        
        # Adiciona informação de dias até o aniversário
        dias = pessoa.dias_ate_aniversario()
        if dias is not None:  # Verifica se dias não é None
            if dias == 0:
                html += '                    <b style="color: #28a745;">HOJE É O DIA!</b><br>'
            elif dias <= 7:
                html += f'                    <i>Faltam {dias} dias</i><br>'
        
        html += """
                </span>
            </div>
        """
        
        return html
    
    @staticmethod
    def format_aniversariante(aniversariante: Pessoa) -> str:
        """
        Alias para format_pessoa (compatibilidade).
        
        Args:
            aniversariante: Objeto Pessoa
            
        Returns:
            String HTML com os dados formatados
        """
        return HTMLFormatter.format_pessoa(aniversariante)
    
    @staticmethod
    def format_no_results(mes_nome: str) -> str:
        """
        Formata mensagem quando não há resultados.
        
        Args:
            mes_nome: Nome do mês
            
        Returns:
            String HTML
        """
        return f"""
            <div style="text-align: center; padding: 40px;">
                <h3 style="color: #007ACC;">Nenhum aniversariante encontrado para {mes_nome}.</h3>
            </div>
        """
