"""
Funções utilitárias para o sistema.
"""
from datetime import datetime
from typing import Optional, Tuple


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Converte uma string de data para datetime.
    Tenta múltiplos formatos de data.
    
    Args:
        date_str: String com a data
        
    Returns:
        Objeto datetime ou None se não conseguir fazer o parse
    """
    if not date_str:
        return None
    
    # Formatos de data suportados
    date_formats = (
        '%d/%m/%Y',   # Formato brasileiro: 25/12/2023
        '%d-%m-%Y',   # Formato alternativo: 25-12-2023
        '%Y-%m-%d',   # Formato ISO: 2023-12-25
    )
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Se nenhum formato funcionou
    return None


def get_current_month_name() -> str:
    """
    Retorna o nome do mês atual em português.
    
    Returns:
        Nome do mês (ex: 'Janeiro', 'Fevereiro', etc.)
    """
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 
        'Maio', 'Junho', 'Julho', 'Agosto', 
        'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    return meses[datetime.now().month - 1]


def format_whatsapp_number(number_str: str) -> str:
    """
    Formata um número de telefone para usar com WhatsApp.
    Adiciona o código do país (55) se necessário.
    
    Args:
        number_str: Número de telefone como string
        
    Returns:
        Número formatado para WhatsApp (apenas dígitos com código do país)
    """
    if not number_str:
        return ""
    
    # Remove todos os caracteres não numéricos
    digits_only = ''.join(filter(str.isdigit, number_str))
    
    # Se for um número brasileiro de 11 dígitos (DDD + 9 + número)
    # e não começar com 55, adiciona o código do Brasil
    if len(digits_only) == 11 and not digits_only.startswith('55'):
        digits_only = f"55{digits_only}"
    
    return digits_only


def create_whatsapp_link(number_str: str) -> str:
    """
    Cria um link do WhatsApp para um número de telefone.
    
    Args:
        number_str: Número de telefone como string
        
    Returns:
        URL do WhatsApp (wa.me)
    """
    formatted_number = format_whatsapp_number(number_str)
    if not formatted_number:
        return ""
    
    return f"https://wa.me/{formatted_number}"


def format_whatsapp_link(number_str: str) -> tuple:
    """
    Formata um número de telefone para um link do WhatsApp.
    Retorna tanto o link quanto o número original para exibição.
    
    Args:
        number_str: Número de telefone como string
        
    Returns:
        Tupla (link, numero_exibicao) - link do WhatsApp e número original
    """
    if not number_str:
        return "", ""
    
    # Remove todos os caracteres não numéricos
    digits_only = ''.join(filter(str.isdigit, number_str))
    
    # Se for um número brasileiro de 11 dígitos (DDD + 9 + número)
    # e não começar com 55, adiciona o código do Brasil
    if len(digits_only) == 11 and digits_only[0] in '123456789':
        full_number = f"55{digits_only}"
    else:
        full_number = digits_only
    
    link = f"https://wa.me/{full_number}"
    return link, number_str  # Retorna o link e o número original


def get_current_sheet_name() -> str:
    """
    Retorna o nome da aba correspondente ao mês/ano atual.
    Formato: 'Jan/25', 'Fev/25', 'Mar/25', etc.
    
    Returns:
        Nome da aba do mês atual (ex: 'Out/25' para outubro de 2025)
    """
    now = datetime.now()
    
    # Mapeamento de meses para abreviações em português
    meses_abrev = {
        1: 'Jan',
        2: 'Fev',
        3: 'Mar',
        4: 'Abr',
        5: 'Mai',
        6: 'Jun',
        7: 'Jul',
        8: 'Ago',
        9: 'Set',
        10: 'Out',
        11: 'Nov',
        12: 'Dez'
    }
    
    mes_abrev = meses_abrev[now.month]
    ano_abrev = str(now.year)[-2:]  # Últimos 2 dígitos do ano
    
    return f"{mes_abrev}/{ano_abrev}"


def get_sheet_range(sheet_name: str, columns: str = 'A:BT') -> str:
    """
    Cria o range completo incluindo o nome da aba.
    
    Args:
        sheet_name: Nome da aba
        columns: Range de colunas (padrão: 'A:BT')
    
    Returns:
        Range completo no formato: 'NomeAba!A:BT'
    """
    return f"'{sheet_name}'!{columns}"