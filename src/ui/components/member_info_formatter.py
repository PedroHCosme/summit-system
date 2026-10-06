"""Módulo unificado para formatação de dados de membro em HTML.

Centraliza a geração de HTML para exibir o perfil completo de um membro,
usado por members_list_screen, member_search_screen e checkin_screen.
"""

from datetime import datetime
from typing import Any, Dict

from src.config import PLANOS_COM_VENCIMENTO


def format_member_data(member_data: dict, monthly_frequency: int = 0) -> str:
    """Formata os dados do membro em HTML.

    Args:
        member_data: Dicionário com os dados do membro.
        monthly_frequency: Número de check-ins do membro no mês atual.

    Returns:
        String HTML com os dados formatados.
    """
    html = """
        <div style="padding: 20px;">
            <h2 style="color: #007ACC; text-align: center; margin-bottom: 20px;">Dados do Membro</h2>
            <div style="background-color: #F8F8F8; border: 1px solid #DDDDDD; border-radius: 8px; padding: 15px;">
    """

    nome = member_data.get('nome', '')
    apelido = member_data.get('apelido', '')
    nome_display = f"{nome} ({apelido})" if apelido else (nome if nome else '<span style="color: #888888; font-style: italic;">Não informado</span>')

    html += f"""
        <div style="margin-bottom: 10px;">
            <strong style="color: #333333;">Nome:</strong>
            <span style="color: #555555;"> {nome_display}</span>
        </div>
    """

    data_nascimento = member_data.get('data_nascimento', '')
    html += f"""
        <div style="margin-bottom: 10px;">
            <strong style="color: #333333;">Data de Nascimento:</strong>
            <span style="color: #555555;"> {data_nascimento if data_nascimento else '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
        </div>
    """

    genero = member_data.get('genero', '')
    html += f"""
        <div style="margin-bottom: 10px;">
            <strong style="color: #333333;">Gênero:</strong>
            <span style="color: #555555;"> {genero if genero else '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
        </div>

        <div style="margin-bottom: 10px;">
            <strong style="color: #333333;">Profissão:</strong>
            <span style="color: #555555;"> {member_data.get('profissao', '') or '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
        </div>
    """

    whatsapp = member_data.get('whatsapp', '')
    if whatsapp:
        digits = ''.join(filter(str.isdigit, whatsapp))
        if len(digits) == 11:
            whatsapp_link = f"https://wa.me/55{digits}"
            html += f"""
                <div style="margin-bottom: 10px;">
                    <strong style="color: #333333;">WhatsApp:</strong>
                    <span style="color: #555555;"> {whatsapp}</span>
                    <a href="{whatsapp_link}" style="color: #007ACC; margin-left: 10px;">[Abrir WhatsApp]</a>
                </div>
            """
        else:
            html += f"""
                <div style="margin-bottom: 10px;">
                    <strong style="color: #333333;">WhatsApp:</strong>
                    <span style="color: #555555;"> {whatsapp}</span>
                </div>
            """
    else:
        html += f"""
            <div style="margin-bottom: 10px;">
                <strong style="color: #333333;">WhatsApp:</strong>
                <span style="color: #888888; font-style: italic;"> Não informado</span>
            </div>
        """

    html += f"""
        <div style="margin-bottom: 10px;">
            <strong style="color: #333333;">Contato de Emergência:</strong>
            <span style="color: #555555;"> {member_data.get('contato_emergencia', '') or '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
        </div>
    """

    email = member_data.get('email', '')
    html += f"""
        <div style="margin-bottom: 10px;">
            <strong style="color: #333333;">Email:</strong>
            <span style="color: #555555;"> {email if email else '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
        </div>
    """

    calcado = member_data.get('calcado', '')
    html += f"""
        <div style="margin-bottom: 10px;">
            <strong style="color: #333333;">Calçado:</strong>
            <span style="color: #555555;"> {calcado if calcado else '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
        </div>
    """

    data_cadastro = member_data.get('data_cadastro', '')
    html += f"""
        <div style="margin-bottom: 10px;">
            <strong style="color: #333333;">Data de Cadastro:</strong>
            <span style="color: #555555;"> {data_cadastro if data_cadastro else '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
        </div>
    """

    html += """
        <hr style="border: none; border-top: 1px solid #DDDDDD; margin: 15px 0;">
    """

    plano = member_data.get('plano', '')
    html += f"""
        <div style="margin-bottom: 10px;">
            <strong style="color: #333333;">Plano:</strong>
            <span style="color: #555555;"> {plano if plano else '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
        </div>
    """

    if plano in PLANOS_COM_VENCIMENTO:
        vencimento_plano = member_data.get('vencimento_plano', '')
        html += f"""
            <div style="margin-bottom: 10px;">
                <strong style="color: #333333;">Vencimento do Plano:</strong>
                <span style="color: #555555;"> {vencimento_plano if vencimento_plano else '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
            </div>
        """

    estado_plano = member_data.get('estado_plano', '')
    from src.core.plan_status import is_active as plan_is_active, INATIVO, display_label
    estado_color = '#28a745' if plan_is_active(estado_plano) else '#FF6B6B'
    html += f"""
        <div style="margin-bottom: 10px;">
            <strong style="color: #333333;">Estado do Plano:</strong>
            <span style="color: {estado_color}; font-weight: bold;"> {estado_plano if estado_plano else INATIVO}</span>
        </div>
    """

    from src.services.plan_service import get_plan_service
    is_quota_plan = get_plan_service().is_quota_plan(plano)
    if is_quota_plan:
        credits_val = member_data.get('voucher_credits', 0)
        credits_color = '#28a745' if credits_val > 0 else '#dc3545'
        html += f"""
            <div style="margin-bottom: 10px;">
                <strong style="color: #333333;">Saldo de Vouchers:</strong>
                <span style="color: {credits_color}; font-weight: bold;"> {credits_val}</span>
            </div>
        """

    treina = member_data.get('treina', 'Não')
    treina_color = '#28a745' if treina == 'Sim' else '#888888'
    html += f"""
        <div style="margin-bottom: 10px;">
            <strong style="color: #333333;">Treina:</strong>
            <span style="color: {treina_color}; font-weight: bold;"> {treina}</span>
        </div>

        <div style="margin-bottom: 10px;">
            <strong style="color: #333333;">Frequência (Meta):</strong>
            <span style="color: #555555;"> {member_data.get('frequencia', '') or '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
        </div>
    """

    if treina == 'Sim':
        vencimento_treino = member_data.get('vencimento_treino', '')
        html += f"""
            <div style="margin-bottom: 10px;">
                <strong style="color: #333333;">Vencimento do Treino:</strong>
                <span style="color: #555555;"> {vencimento_treino if vencimento_treino else '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
            </div>
        """

    html += f"""
        <div style="margin-bottom: 10px;">
            <strong style="color: #333333;">Frequência (Este Mês):</strong>
            <span style="color: #007ACC; font-weight: bold;"> {monthly_frequency} check-ins</span>
        </div>

        <hr style="border: none; border-top: 1px solid #DDDDDD; margin: 15px 0;">
        
        <div style="margin-bottom: 10px;">
            <strong style="color: #333333; display: block; margin-bottom: 5px;">Observações:</strong>
            <span style="color: #555555; white-space: pre-wrap;"> {member_data.get('observacoes') or '<span style="color: #888888; font-style: italic;">Nenhuma observação registrada</span>'}</span>
        </div>
    """

    html += """
            </div>
        </div>
    """

    return html


def calculate_monthly_frequency(member_id: int) -> int:
    """Calcula quantos check-ins o membro fez no mês atual.

    Args:
        member_id: ID do membro

    Returns:
        Número de check-ins no mês atual
    """
    if not member_id:
        return 0

    try:
        from src.data.data_provider import get_provider

        history = get_provider().get_member_checkin_history(member_id)

        if not history:
            return 0

        now = datetime.now()
        current_month = now.month
        current_year = now.year

        count = 0
        for checkin in history:
            checkin_datetime_str = checkin.get('checkin_datetime', '')

            try:
                checkin_dt = datetime.fromisoformat(checkin_datetime_str.replace(' ', 'T'))

                if checkin_dt.month == current_month and checkin_dt.year == current_year:
                    count += 1
            except (ValueError, AttributeError):
                continue

        return count

    except Exception as e:
        print(f"Erro ao calcular frequência mensal: {e}")
        return 0
