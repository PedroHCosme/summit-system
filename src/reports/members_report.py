"""Gerador de relatório de membros."""

from __future__ import annotations

from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from html import escape

from sqlalchemy import text
from sqlalchemy.orm import Session
from src.data.db import create_session
from src.utils.date_utils import parse_date_to_date


def _get_reports_dir() -> Path:
    """Retorna o diretório de relatórios, criando se não existir."""
    project_root = Path(__file__).parent.parent.parent
    reports_dir = project_root / "relatorios"
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def _generate_html_header(title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .stat-card.blue {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}
        
        .stat-card.green {{
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }}
        
        .stat-card.orange {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }}
        
        .stat-card.purple {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.2);
        }}
        
        .stat-card .label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }}
        
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
        }}
        
        .stat-card .hint {{
            font-size: 0.75em;
            opacity: 0.8;
            margin-top: 5px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .filter-bar {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            font-size: 0.9em;
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 10px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }}
        
        td {{
            padding: 10px;
            border-bottom: 1px solid #f0f0f0;
        }}
        
        tr:hover {{
            background-color: #f8f9fa;
        }}
        
        tr:nth-child(even) {{
            background-color: #fafafa;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #e0e0e0;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .status-badge.active {{
            background: #d4edda;
            color: #155724;
        }}
        
        .status-badge.expiring {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .status-badge.expired {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .contact {{
            font-size: 0.85em;
            color: #666;
        }}
        
        .plan-badge {{
            background: #e7f3ff;
            color: #0056b3;
            padding: 3px 8px;
            border-radius: 8px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .filter-buttons {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .filter-btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9em;
        }}
        
        .filter-btn.active {{
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
        
        .filter-btn.all {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .filter-btn.active-filter {{
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            color: white;
        }}
        
        .filter-btn.expiring-filter {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            color: white;
        }}
        
        .filter-btn.expired-filter {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }}
        
        .filter-btn.inactive-filter {{
            background: linear-gradient(135deg, #ff9a56 0%, #ff6a88 100%);
            color: white;
        }}
        
        .plan-filter {{
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .plan-filter label {{
            font-weight: 600;
            color: #667eea;
        }}
        
        .plan-filter select {{
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid #d0d0d0;
            font-size: 0.9em;
            min-width: 220px;
        }}
        
        .hidden {{
            display: none !important;
        }}
        
        .info-box {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}
        
        .info-box h3 {{
            color: #667eea;
            margin-bottom: 10px;
        }}
        
        .info-box ul {{
            margin-left: 20px;
            line-height: 1.8;
        }}
        
        .alert-box {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}
        
        .alert-box h3 {{
            color: #856404;
            margin-bottom: 10px;
        }}
        
        .success-box {{
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}
        
        .success-box h3 {{
            color: #155724;
            margin-bottom: 10px;
        }}
        
        .member-count {{
            font-weight: bold;
            color: #667eea;
        }}
    </style>
</head>
<body>
"""


def _generate_html_footer() -> str:
    return """
    <div class="footer">
        <p>Relatório gerado automaticamente pelo Sistema de Gestão Summit</p>
        <p>© 2025 Summit Climbing Gym</p>
    </div>
</body>
</html>
"""


def _parse_date(date_str: Optional[Union[str, datetime, date]]) -> Optional[datetime]:
    """Parse date from database format usando a mesma lógica do sistema."""
    if not date_str:
        return None

    if isinstance(date_str, datetime):
        return date_str

    if isinstance(date_str, date):
        return datetime.combine(date_str, datetime.min.time())

    try:
        # Tentar interpretar strings completas de datetime (ex: "2025-01-07 19:00:00")
        # Isso preserva o horário para ordenação correta dos check-ins.
        return datetime.fromisoformat(date_str)
    except (TypeError, ValueError):
        pass
    
    # Usar a função parse_date_to_date do sistema que já funciona
    date_obj = parse_date_to_date(date_str)
    if date_obj:
        # Converter date para datetime
        return datetime.combine(date_obj, datetime.min.time())
    
    return None


def _get_status_info(vencimento_str: str) -> tuple[str, str]:
    """Retorna status de display e classe CSS baseado no vencimento.
    
    NOTA: Os valores retornados ('Vencido', 'Ativo') são LABELS DE DISPLAY,
    não valores persistidos no banco. O banco usa exclusivamente
    ATIVO/INATIVO (ver src/core/plan_status.py).
    """
    from src.core.plan_status import DISPLAY_LABEL_ATIVO, DISPLAY_LABEL_PLANO_VENCIDO
    
    if not vencimento_str:
        return ("Sem Data", "expired")
    
    vencimento = _parse_date(vencimento_str)
    if not vencimento:
        return ("Data Inválida", "expired")
    
    today = datetime.now()
    days_until = (vencimento - today).days
    
    if days_until < 0:
        return (DISPLAY_LABEL_PLANO_VENCIDO, "expired")
    elif days_until <= 7:
        return (f"Vence em {days_until}d", "expiring")
    else:
        return (DISPLAY_LABEL_ATIVO, "active")


def generate_members_report(
    db_session: Optional[Session] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period_label: Optional[str] = None,
) -> str:
    """
    Gera relatório completo de membros.
    
    Args:
        db_session: Sessão SQLAlchemy (nova sessão será criada se None)
        start_date: Data inicial do período (opcional)
        end_date: Data final do período (opcional)
        period_label: Rótulo legível do período (opcional)
        
    Returns:
        Caminho do arquivo HTML gerado
    """
    close_session = False
    if db_session is None:
        db_session = create_session()
        close_session = True

    # Resolver período padrão
    if start_date is None:
        start_date = date(2000, 1, 1)
    if end_date is None:
        end_date = date.today()
    if period_label is None:
        period_label = f"{start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}"
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    try:
        # Estatísticas gerais
        total_members = db_session.execute(text("SELECT COUNT(*) FROM membros")).scalar() or 0
        
        # Calcular contadores usando parse de datas (mesmo método do dialog)
        today = datetime.now().date()
        week_ahead = today + timedelta(days=7)
        
        # Planos que não têm conceito de vencimento (pagos por check-in)
        # Derivado da tabela 'planos' (fonte de verdade) em vez de set hardcoded
        per_checkin_plans_query = db_session.execute(
            text("SELECT nome FROM planos WHERE valor_por_checkin > 0 AND ativo = 1")
        ).fetchall()
        per_checkin_plans = {row[0] for row in per_checkin_plans_query} if per_checkin_plans_query else set()
        # Fallback: se a tabela planos não tem dados, usar config
        if not per_checkin_plans:
            from src.config import PLANOS_PAGAMENTO_POR_CHECKIN
            per_checkin_plans = set(PLANOS_PAGAMENTO_POR_CHECKIN.keys())
        
        # Buscar todos os membros com seus planos para calcular estatísticas
        all_members_data = db_session.execute(text("SELECT vencimento_plano, plano FROM membros")).fetchall()
        
        active_members = 0
        expired_members = 0
        expiring_soon = 0
        
        for row in all_members_data:
            vencimento_str = row[0]
            plano = row[1]
            
            # Planos por check-in não contam como vencidos
            if plano in per_checkin_plans:
                continue
                
            if not vencimento_str:
                expired_members += 1
                continue
            
            vencimento = parse_date_to_date(vencimento_str)
            if not vencimento:
                expired_members += 1
                continue
            
            if vencimento >= today:
                active_members += 1
                if today <= vencimento <= week_ahead:
                    expiring_soon += 1
            else:
                expired_members += 1
        
        # Distribuição por plano
        plan_distribution = db_session.execute(text("""
            SELECT plano, COUNT(*) as total
            FROM membros
            GROUP BY plano
            ORDER BY total DESC
        """)).fetchall()

        plan_value_order: List[str] = []
        seen_plan_values: set[str] = set()
        for row in plan_distribution:
            plan_name = row[0]
            plan_value = plan_name or "Sem Plano"
            if plan_value in seen_plan_values:
                continue
            seen_plan_values.add(plan_value)
            plan_value_order.append(plan_value)
        
        # Distribuição por gênero
        gender_distribution = db_session.execute(text("""
            SELECT genero, COUNT(*) as total
            FROM membros
            GROUP BY genero
            ORDER BY total DESC
        """)).fetchall()
        
        # Lista completa de membros
        members = db_session.execute(text("""
            SELECT 
                nome,
                email,
                whatsapp,
                plano,
                vencimento_plano,
                genero,
                data_nascimento,
                id
            FROM membros
            ORDER BY nome
        """)).fetchall()
        
        # Criar mapa de membros para acesso rápido por ID
        # row[-1] é o id
        members_by_id = {row[-1]: row for row in members}

        # Mapear última visita de cada membro utilizando parse consistente
        raw_checkins = db_session.execute(text("""
            SELECT member_id, checkin_datetime
            FROM frequencia
            WHERE checkin_datetime IS NOT NULL
              AND DATE(checkin_datetime) >= :start
              AND DATE(checkin_datetime) <= :end
        """), {"start": start_str, "end": end_str}).fetchall()
        
        print(f"[DEBUG] Total de check-ins retornados: {len(raw_checkins)}")
        if raw_checkins:
            print(f"[DEBUG] Primeiros check-ins recebidos: {raw_checkins[:5]}")

        last_visits_map: Dict[int, datetime] = {}
        debug_failures = 0
        for row in raw_checkins:
            member_id = row[0]
            checkin_str = row[1]
            
            visit_dt = _parse_date(checkin_str)
            if not visit_dt:
                if debug_failures < 10:
                    print(f"[DEBUG] Falha ao converter check-in. member_id={member_id}, valor='{checkin_str}'")
                    debug_failures += 1
                continue
            previous_visit = last_visits_map.get(member_id)
            if not previous_visit or visit_dt > previous_visit:
                last_visits_map[member_id] = visit_dt
                print(f"[DEBUG] Atualizando última visita: member_id={member_id}, visita={visit_dt}")
        print(f"[DEBUG] Membros com última visita registrada: {len(last_visits_map)}")

        # Análise de retenção: membros que frequentaram nos últimos 3 meses mas não voltam há 1 mês
        three_months_ago = datetime.now() - timedelta(days=90)
        one_month_ago = datetime.now() - timedelta(days=30)

        inactive_members = []
        for member_id, last_visit_dt in last_visits_map.items():
            if three_months_ago <= last_visit_dt < one_month_ago:
                member_data = members_by_id.get(member_id)
                if not member_data:
                    continue
                # Desempacotar dados do membro
                nome = member_data[0]
                email = member_data[1]
                whatsapp = member_data[2]
                plano = member_data[3]
                vencimento_plano = member_data[4]
                # genero = member_data[5]
                # data_nascimento = member_data[6]
                
                inactive_members.append(
                    (
                        member_id,
                        nome,
                        plano,
                        email,
                        whatsapp,
                        vencimento_plano,
                        last_visit_dt,
                    )
                )

        # Ordenar membros inativos por data da última visita (mais recente primeiro)
        inactive_members.sort(key=lambda item: item[-1], reverse=True)

        plan_options_html = "".join(
            f'<option value="{escape(plan_value, quote=True)}">{escape(plan_value)}</option>'
            for plan_value in plan_value_order
        )

        inactive_plan_labels = {member[2] or "Sem Plano" for member in inactive_members}
        inactive_plan_options_html = "".join(
            f'<option value="{escape(plan_value, quote=True)}">{escape(plan_value)}</option>'
            for plan_value in plan_value_order
            if plan_value in inactive_plan_labels
        )

        # Membros que vencem nos próximos 7 dias (detalhados)
        expiring_members_details = []
        for row in all_members_data:
            vencimento_str = row[0]
            plano = row[1]
            
            # Planos por check-in não têm vencimento
            if plano in per_checkin_plans:
                continue
                
            if not vencimento_str:
                continue
            vencimento = parse_date_to_date(vencimento_str)
            if not vencimento:
                continue
            if today <= vencimento <= week_ahead:
                # Buscar detalhes do membro
                result = db_session.execute(text("""
                    SELECT nome, email, whatsapp, plano, vencimento_plano, id
                    FROM membros
                    WHERE vencimento_plano = :venc AND plano = :plano
                """), {"venc": vencimento_str, "plano": plano}).fetchone()
                
                if result:
                    days_remaining = (vencimento - today).days
                    # Converter result para tupla/lista e adicionar days_remaining
                    expiring_members_details.append((*result, days_remaining))
        
        # Análise de conversão por plano (dentro do período selecionado)
        new_members_by_plan = db_session.execute(text("""
            SELECT plano, COUNT(*) as novos_membros
            FROM membros
            WHERE DATE(created_at) >= :start AND DATE(created_at) <= :end
            GROUP BY plano
            ORDER BY novos_membros DESC
        """), {"start": start_str, "end": end_str}).fetchall()
        
        # Gerar HTML
        html = _generate_html_header(f"Relatório de Membros — {period_label}")
        
        html += f"""
        <div class="container">
            <div class="header">
                <h1>👤 Relatório de Membros</h1>
                <p class="subtitle">Período: {period_label}</p>
                <p class="subtitle">Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
            </div>
            
            <div class="content">
                <div class="info-box">
                    <h3>📊 Como usar este relatório</h3>
                    <ul>
                        <li><strong>Cards Clicáveis:</strong> Clique nos cards coloridos para filtrar membros por status</li>
                        <li><strong>Membros Ativos:</strong> Planos com vencimento futuro (data de vencimento ≥ hoje)</li>
                        <li><strong>Vencendo:</strong> Planos que expiram nos próximos 7 dias (oportunidade de renovação!)</li>
                        <li><strong>Vencidos:</strong> Planos com data de vencimento no passado</li>
                        <li><strong>Inativos:</strong> Membros que frequentaram nos últimos 3 meses mas não voltam há 1 mês (risco de cancelamento!)</li>
                    </ul>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card blue" onclick="showAllMembers()">
                        <div class="label">Total de Membros</div>
                        <div class="value">{total_members}</div>
                        <div class="hint">👆 Clique para ver todos</div>
                    </div>
                    
                    <div class="stat-card green" onclick="filterMembers('active')">
                        <div class="label">Ativos</div>
                        <div class="value">{active_members}</div>
                        <div class="hint">👆 Clique para ver lista</div>
                    </div>
                    
                    <div class="stat-card orange" onclick="filterMembers('expiring')">
                        <div class="label">Vencendo (7 dias)</div>
                        <div class="value">{expiring_soon}</div>
                        <div class="hint">👆 Clique para ver quem</div>
                    </div>
                    
                    <div class="stat-card" onclick="filterMembers('expired')">
                        <div class="label">Vencidos</div>
                        <div class="value">{expired_members}</div>
                        <div class="hint">👆 Clique para ver lista</div>
                    </div>
                </div>
                
                <!-- Alerta de Retenção -->"""
        
        if len(inactive_members) > 0:
            html += f"""
                <div class="alert-box">
                    <h3>⚠️ Alerta de Retenção: {len(inactive_members)} membro(s) em risco!</h3>
                    <p>Estes membros frequentaram nos últimos 3 meses mas não aparecem há mais de 1 mês. 
                       <strong>Ação recomendada:</strong> Entre em contato para reengajar antes do cancelamento!</p>
                </div>"""
        else:
            html += """
                <div class="success-box">
                    <h3>✅ Retenção Excelente!</h3>
                    <p>Nenhum membro ativo apresenta sinais de abandono. Continue com o excelente trabalho!</p>
                </div>"""
        
        html += f"""
                
                <!-- Seção de Membros Inativos -->
                <div class="section" id="inactive-section" {"" if len(inactive_members) > 0 else 'style="display:none;"'}>
                    <h2>🔴 Membros em Risco de Cancelamento (<span id="inactive-count">{len(inactive_members)}</span>)</h2>
                    <p style="margin-bottom: 15px; color: #856404;">
                        <strong>Estratégia de Retenção:</strong> Estes membros estavam ativos mas pararam de frequentar. 
                        Entre em contato oferecendo: desconto na renovação, sessão gratuita com instrutor, ou novos horários/atividades.
                    </p>
                    <div class="plan-filter">
                        <label for="inactive-plan-filter">Filtrar por plano:</label>
                        <select id="inactive-plan-filter">
                            <option value="all">Todos os planos</option>
                            {inactive_plan_options_html}
                        </select>
                    </div>
                    <table id="inactive-members-table">
                        <thead>
                            <tr>
                                <th>Nome</th>
                                <th>Plano</th>
                                <th>Último Check-in</th>
                                <th>Status do Plano</th>
                                <th>Contato</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for member in inactive_members:
            member_id, nome, plano, email, whatsapp, vencimento_str, ultimo_checkin_dt = member
            
            ultimo_checkin_display = ultimo_checkin_dt.strftime('%d/%m/%Y')
            days_inactive = (datetime.now() - ultimo_checkin_dt).days

            plan_display = plano or 'Sem Plano'
            plan_attr_value = escape(plan_display, quote=True)
            
            vencimento_parsed = parse_date_to_date(vencimento_str) if vencimento_str else None
            # NOTA: 'Ativo'/'Plano vencido' são labels de display, não valores de DB
            from src.core.plan_status import DISPLAY_LABEL_ATIVO, DISPLAY_LABEL_PLANO_VENCIDO
            status_plano = DISPLAY_LABEL_ATIVO if vencimento_parsed and vencimento_parsed >= today else DISPLAY_LABEL_PLANO_VENCIDO
            status_class = "active" if status_plano == DISPLAY_LABEL_ATIVO else "expired"
            
            contact_info = []
            if email:
                contact_info.append(f"✉️ {escape(email)}")
            if whatsapp:
                whatsapp_clean = ''.join(filter(str.isdigit, whatsapp))
                whatsapp_link = f"https://wa.me/{whatsapp_clean}" if whatsapp_clean else None
                whatsapp_display = escape(whatsapp)
                if whatsapp_link:
                    contact_info.append(f"📱 <a href=\"{whatsapp_link}\" target=\"_blank\" rel=\"noopener\">{whatsapp_display}</a>")
                else:
                    contact_info.append(f"📱 {whatsapp_display}")
            contact_display = "<br>".join(contact_info) if contact_info else "Sem contato"
            
            html += f"""
                            <tr data-plan="{plan_attr_value}">
                                <td><strong>{nome}</strong></td>
                                <td><span class="plan-badge">{plan_display}</span></td>
                                <td>{ultimo_checkin_display} <span style="color: #dc3545;">({days_inactive}d atrás)</span></td>
                                <td><span class="status-badge {status_class}">{status_plano}</span></td>
                                <td class="contact">{contact_display}</td>
                            </tr>
            """
        
        html += """
                        </tbody>
                    </table>
                </div>
                
                <!-- Análise de Novos Membros (últimos 30 dias) -->"""
        
        total_new = sum(row[1] for row in new_members_by_plan)
        if total_new > 0:
            html += f"""
                <div class="section">
                    <h2>🎉 Novos Membros (últimos 30 dias): {total_new}</h2>
                    <p style="margin-bottom: 15px; color: #155724;">
                        <strong>Análise de Conversão:</strong> Acompanhe quais planos estão vendendo mais para otimizar estratégias de marketing.
                    </p>
                    <table>
                        <thead>
                            <tr>
                                <th>Plano</th>
                                <th>Novos Membros</th>
                                <th>% do Total de Novos</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for row in new_members_by_plan:
                plano = row[0]
                count = row[1]
                percentage = (count / total_new * 100) if total_new > 0 else 0
                html += f"""
                            <tr>
                                <td><strong>{plano}</strong></td>
                                <td>{count}</td>
                                <td>{percentage:.1f}%</td>
                            </tr>
                """
            
            html += """
                        </tbody>
                    </table>
                </div>
            """
        
        html += """
                
                <div class="section">
                    <h2>📊 Distribuição por Plano</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Plano</th>
                                <th>Total de Membros</th>
                                <th>Percentual</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for row in plan_distribution:
            plan = row[0]
            count = row[1]
            percentage = (count / total_members * 100) if total_members > 0 else 0
            html += f"""
                            <tr>
                                <td><strong>{plan}</strong></td>
                                <td>{count}</td>
                                <td>{percentage:.1f}%</td>
                            </tr>
            """
        
        html += """
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h2>👥 Distribuição por Gênero</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Gênero</th>
                                <th>Total de Membros</th>
                                <th>Percentual</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for row in gender_distribution:
            gender = row[0]
            count = row[1]
            percentage = (count / total_members * 100) if total_members > 0 else 0
            gender_label = gender or "Não Informado"
            html += f"""
                            <tr>
                                <td><strong>{gender_label}</strong></td>
                                <td>{count}</td>
                                <td>{percentage:.1f}%</td>
                            </tr>
            """
        
        html += f"""
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h2>📋 Lista Completa de Membros</h2>
                    
                    <div class="filter-buttons">
                        <button class="filter-btn all active" onclick="showAllMembers()">
                            👥 Todos ({total_members})
                        </button>
                        <button class="filter-btn active-filter" onclick="filterMembers('active')">
                            ✅ Ativos ({active_members})
                        </button>
                        <button class="filter-btn expiring-filter" onclick="filterMembers('expiring')">
                            ⚠️ Vencendo ({expiring_soon})
                        </button>
                        <button class="filter-btn expired-filter" onclick="filterMembers('expired')">
                            ❌ Vencidos ({expired_members})
                        </button>
                        <button class="filter-btn inactive-filter" onclick="filterMembers('inactive')">
                            🔴 Inativos ({len(inactive_members)})
                        </button>
                    </div>

                    <div class="plan-filter">
                        <label for="plan-filter">Filtrar por plano:</label>
                        <select id="plan-filter">
                            <option value="all">Todos os planos</option>
                            {plan_options_html}
                        </select>
                    </div>
                    
                    <div id="filter-info" style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 8px; display: none;">
                        <strong>Filtro ativo:</strong> <span id="filter-description"></span>
                    </div>
                    
                    <table id="members-table">
                        <thead>
                            <tr>
                                <th>Nome</th>
                                <th>Plano</th>
                                <th>Status</th>
                                <th>Vencimento</th>
                                <th>Última Visita</th>
                                <th>Contato</th>
                                <th>Gênero</th>
                                <th>Nascimento</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # Mapa de últimas visitas calculado anteriormente
        last_visits = last_visits_map
        
        for member in members:
            nome = member[0]
            email = member[1]
            whatsapp = member[2]
            plano = member[3]
            vencimento = member[4]
            genero = member[5]
            nascimento = member[6]
            member_id = member[7]
            
            status_text, status_class = _get_status_info(vencimento)
            
            # Determinar categoria do membro
            vencimento_parsed = parse_date_to_date(vencimento) if vencimento else None
            is_active = vencimento_parsed and vencimento_parsed >= today
            is_expiring = vencimento_parsed and today <= vencimento_parsed <= week_ahead
            
            # Para planos por check-in, não mostrar como "vencido"
            # Eles não têm conceito de vencimento de plano
            if plano in per_checkin_plans:
                is_expired = False
            else:
                is_expired = not vencimento_parsed or vencimento_parsed < today
            
            # Verificar se está na lista de inativos
            is_inactive = any(m[0] == member_id for m in inactive_members)
            
            categories = []
            if is_active:
                categories.append('active')
            if is_expiring:
                categories.append('expiring')
            if is_expired:
                categories.append('expired')
            if is_inactive:
                categories.append('inactive')
            
            categories_str = ' '.join(categories)
            
            plan_display = plano or 'Sem Plano'
            plan_attr_value = escape(plan_display, quote=True)

            vencimento_dt = _parse_date(vencimento) if vencimento else None
            vencimento_display = vencimento_dt.strftime('%d/%m/%Y') if vencimento_dt else 'N/A'

            nascimento_dt = _parse_date(nascimento) if nascimento else None
            nascimento_display = nascimento_dt.strftime('%d/%m/%Y') if nascimento_dt else 'N/A'

            # Última visita
            last_visit_date = last_visits.get(member_id)
            if last_visit_date:
                last_visit_display = last_visit_date.strftime('%d/%m/%Y')
            else:
                last_visit_display = 'Nunca'
            
            contact_info = []
            if email:
                contact_info.append(f"✉️ {escape(email)}")
            if whatsapp:
                whatsapp_clean = ''.join(filter(str.isdigit, whatsapp))
                whatsapp_link = f"https://wa.me/{whatsapp_clean}" if whatsapp_clean else None
                whatsapp_display = escape(whatsapp)
                if whatsapp_link:
                    contact_info.append(f"📱 <a href=\"{whatsapp_link}\" target=\"_blank\" rel=\"noopener\">{whatsapp_display}</a>")
                else:
                    contact_info.append(f"📱 {whatsapp_display}")
            contact_display = "<br>".join(contact_info) if contact_info else "Sem contato"
            
            html += f"""
                            <tr class="member-row" data-categories="{categories_str}" data-plan="{plan_attr_value}">
                                <td><strong>{nome}</strong></td>
                                <td><span class="plan-badge">{plan_display}</span></td>
                                <td><span class="status-badge {status_class}">{status_text}</span></td>
                                <td>{vencimento_display}</td>
                                <td>{last_visit_display}</td>
                                <td class="contact">{contact_display}</td>
                                <td>{genero or 'N/A'}</td>
                                <td>{nascimento_display}</td>
                            </tr>
            """
        
        html += """
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        """
        
        html += """
        
        <script>
            let currentFilter = 'all';
            let currentPlan = 'all';
            const planLabels = { all: 'Todos os planos' };

            function showAllMembers() {
                currentFilter = 'all';
                updateFilterButtons('all');
                applyFilters();
            }

            function filterMembers(category) {
                currentFilter = category;
                updateFilterButtons(category);
                applyFilters();
            }

            function applyFilters() {
                const rows = document.querySelectorAll('.member-row');
                let visibleCount = 0;

                rows.forEach(row => {
                    const categories = (row.dataset.categories || '').split(' ').filter(Boolean);
                    const planValue = row.dataset.plan || '';
                    const matchesCategory = currentFilter === 'all' || categories.includes(currentFilter);
                    const matchesPlan = currentPlan === 'all' || planValue === currentPlan;

                    if (matchesCategory && matchesPlan) {
                        row.style.display = '';
                        visibleCount++;
                    } else {
                        row.style.display = 'none';
                    }
                });

                updateMemberCount(visibleCount);

                if (currentFilter === 'all' && currentPlan === 'all') {
                    hideFilterInfo();
                } else {
                    showFilterInfo(currentFilter, currentPlan, visibleCount);
                }
            }

            function updateFilterButtons(activeCategory) {
                const buttons = document.querySelectorAll('.filter-btn');
                buttons.forEach(btn => btn.classList.remove('active'));

                if (activeCategory === 'all') {
                    const allButton = document.querySelector('.filter-btn.all');
                    if (allButton) {
                        allButton.classList.add('active');
                    }
                } else {
                    const targetButton = document.querySelector(`.filter-btn.${activeCategory}-filter`);
                    if (targetButton) {
                        targetButton.classList.add('active');
                    }
                }
            }

            function showFilterInfo(category, planValue, count) {
                const info = document.getElementById('filter-info');
                const description = document.getElementById('filter-description');

                const descriptions = {
                    all: qty => `Mostrando ${qty} membro(s)`,
                    active: qty => `Mostrando ${qty} membro(s) com planos ativos (vencimento futuro)`,
                    expiring: qty => `Mostrando ${qty} membro(s) com planos vencendo nos próximos 7 dias - CONTATE URGENTE para renovação!`,
                    expired: qty => `Mostrando ${qty} membro(s) com planos vencidos - Oportunidade de reengajamento`,
                    inactive: qty => `Mostrando ${qty} membro(s) em risco - Frequentaram nos últimos 3 meses mas não voltam há 1 mês`
                };

                const statusMessage = (descriptions[category] || descriptions.all)(count);
                let message = statusMessage;

                if (planValue !== 'all') {
                    const planLabel = planLabels[planValue] || planValue;
                    message += ` | Plano filtrado: ${planLabel}`;
                }

                description.textContent = message;
                info.style.display = 'block';
            }

            function hideFilterInfo() {
                const info = document.getElementById('filter-info');
                if (info) {
                    info.style.display = 'none';
                }
            }

            function updateMemberCount(count) {
                console.log(`Exibindo ${count} membro(s)`);
            }

            function applyInactivePlanFilter() {
                const select = document.getElementById('inactive-plan-filter');
                if (!select) {
                    return;
                }

                const selected = select.value;
                const rows = document.querySelectorAll('#inactive-members-table tbody tr');
                let visible = 0;

                rows.forEach(row => {
                    const planValue = row.dataset.plan || '';
                    if (selected === 'all' || planValue === selected) {
                        row.style.display = '';
                        visible++;
                    } else {
                        row.style.display = 'none';
                    }
                });

                const countElement = document.getElementById('inactive-count');
                if (countElement) {
                    countElement.textContent = visible;
                }
            }

            function setupPlanFilters() {
                const planSelect = document.getElementById('plan-filter');
                if (planSelect) {
                    Array.from(planSelect.options).forEach(option => {
                        planLabels[option.value] = option.textContent;
                    });

                    planSelect.addEventListener('change', () => {
                        currentPlan = planSelect.value;
                        applyFilters();
                    });
                }

                const inactivePlanSelect = document.getElementById('inactive-plan-filter');
                if (inactivePlanSelect) {
                    inactivePlanSelect.addEventListener('change', applyInactivePlanFilter);
                    applyInactivePlanFilter();
                }
            }

            document.querySelectorAll('.stat-card').forEach(card => {
                card.addEventListener('click', () => {
                    setTimeout(() => {
                        const membersTable = document.getElementById('members-table');
                        if (membersTable) {
                            membersTable.scrollIntoView({
                                behavior: 'smooth',
                                block: 'start'
                            });
                        }
                    }, 100);
                });
            });

            setupPlanFilters();
            applyFilters();
        </script>
        """
        
        html += _generate_html_footer()
        
        # Salvar arquivo
        reports_dir = _get_reports_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"relatorio_membros_{timestamp}.html"
        filepath = reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return str(filepath)
    finally:
        if close_session:
            db_session.close()
