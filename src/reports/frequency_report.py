"""Gerador de relatório de frequência."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

from src.data.database_manager import DatabaseManager


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
            max-width: 1400px;
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
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .stat-card.blue {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}
        
        .stat-card.green {{
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }}
        
        .stat-card.purple {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
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
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px 15px;
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
        
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .badge.high {{
            background: #d4edda;
            color: #155724;
        }}
        
        .badge.medium {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .badge.low {{
            background: #f8d7da;
            color: #721c24;
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



from src.data.db import create_session
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional

def generate_frequency_report(
    db_session: Optional[Session] = None,
    days: int = 30
) -> str:
    """
    Gera relatório de frequência dos últimos N dias.
    
    Args:
        db_session: Sessão SQLAlchemy (nova sessão será criada se None)
        days: Número de dias a analisar
        
    Returns:
        Caminho do arquivo HTML gerado
    """
    close_session = False
    if db_session is None:
        db_session = create_session()
        close_session = True
        
    try:
        # Período de análise
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Estatísticas gerais
        result = db_session.execute(text("""
            SELECT COUNT(*) as total_checkins
            FROM frequencia
            WHERE checkin_datetime >= :start AND checkin_datetime <= :end
        """), {"start": start_str, "end": end_str})
        total_checkins = result.scalar() or 0
        
        result = db_session.execute(text("""
            SELECT COUNT(DISTINCT member_id) as unique_members
            FROM frequencia
            WHERE checkin_datetime >= :start AND checkin_datetime <= :end
        """), {"start": start_str, "end": end_str})
        unique_members = result.scalar() or 0
        
        result = db_session.execute(text("""
            SELECT DATE(checkin_datetime) as dia, COUNT(*) as total
            FROM frequencia
            WHERE checkin_datetime >= :start AND checkin_datetime <= :end
            GROUP BY DATE(checkin_datetime)
            ORDER BY total DESC
            LIMIT 1
        """), {"start": start_str, "end": end_str})
        busiest_day = result.fetchone()
        
        avg_daily = total_checkins / days if days > 0 else 0
        
        # Top 10 membros mais frequentes
        result = db_session.execute(text("""
            SELECT m.nome, m.plano, COUNT(*) as total_checkins
            FROM frequencia f
            JOIN membros m ON f.member_id = m.id
            WHERE f.checkin_datetime >= :start AND f.checkin_datetime <= :end
            GROUP BY f.member_id, m.nome, m.plano
            ORDER BY total_checkins DESC
            LIMIT 10
        """), {"start": start_str, "end": end_str})
        top_members = result.fetchall()
        
        # Frequência por dia da semana
        result = db_session.execute(text("""
            SELECT 
                CASE CAST(strftime('%w', checkin_datetime) AS INTEGER)
                    WHEN 0 THEN 'Domingo'
                    WHEN 1 THEN 'Segunda'
                    WHEN 2 THEN 'Terça'
                    WHEN 3 THEN 'Quarta'
                    WHEN 4 THEN 'Quinta'
                    WHEN 5 THEN 'Sexta'
                    WHEN 6 THEN 'Sábado'
                END as dia_semana,
                COUNT(*) as total
            FROM frequencia
            WHERE checkin_datetime >= :start AND checkin_datetime <= :end
            GROUP BY CAST(strftime('%w', checkin_datetime) AS INTEGER)
            ORDER BY total DESC
        """), {"start": start_str, "end": end_str})
        weekday_stats = result.fetchall()
        
        # Frequência por plano
        result = db_session.execute(text("""
            SELECT m.plano, COUNT(*) as total_checkins
            FROM frequencia f
            JOIN membros m ON f.member_id = m.id
            WHERE f.checkin_datetime >= :start AND f.checkin_datetime <= :end
            GROUP BY m.plano
            ORDER BY total_checkins DESC
        """), {"start": start_str, "end": end_str})
        plan_stats = result.fetchall()
        
        # Gerar HTML
        html = _generate_html_header("Relatório de Frequência")
        
        html += f"""
        <div class="container">
            <div class="header">
                <h1>📅 Relatório de Frequência</h1>
                <p class="subtitle">Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')} ({days} dias)</p>
                <p class="subtitle">Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
            </div>
            
            <div class="content">
                <div class="stats-grid">
                    <div class="stat-card blue">
                        <div class="label">Total de Check-ins</div>
                        <div class="value">{total_checkins}</div>
                    </div>
                    
                    <div class="stat-card green">
                        <div class="label">Membros Únicos</div>
                        <div class="value">{unique_members}</div>
                    </div>
                    
                    <div class="stat-card purple">
                        <div class="label">Média Diária</div>
                        <div class="value">{avg_daily:.1f}</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="label">Dia Mais Movimentado</div>
                        <div class="value">{busiest_day[1] if busiest_day else 0}</div>
                        <div class="label" style="margin-top: 5px;">{busiest_day[0] if busiest_day else 'N/A'}</div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>🏆 Top 10 Membros Mais Frequentes</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Posição</th>
                                <th>Nome</th>
                                <th>Plano</th>
                                <th>Check-ins</th>
                                <th>Frequência</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for idx, member in enumerate(top_members, 1):
            freq_percentage = (member[2] / days) * 100
            badge_class = "high" if freq_percentage > 70 else "medium" if freq_percentage > 40 else "low"
            html += f"""
                            <tr>
                                <td><strong>#{idx}</strong></td>
                                <td>{member[0]}</td>
                                <td>{member[1]}</td>
                                <td>{member[2]}</td>
                                <td><span class="badge {badge_class}">{freq_percentage:.1f}%</span></td>
                            </tr>
            """
        
        html += """
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h2>📊 Distribuição por Dia da Semana</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Dia da Semana</th>
                                <th>Total de Check-ins</th>
                                <th>Percentual</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for day_stat in weekday_stats:
            percentage = (day_stat[1] / total_checkins * 100) if total_checkins > 0 else 0
            html += f"""
                            <tr>
                                <td><strong>{day_stat[0]}</strong></td>
                                <td>{day_stat[1]}</td>
                                <td>{percentage:.1f}%</td>
                            </tr>
            """
        
        html += """
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h2>💳 Frequência por Tipo de Plano</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Plano</th>
                                <th>Total de Check-ins</th>
                                <th>Percentual</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for plan_stat in plan_stats:
            percentage = (plan_stat[1] / total_checkins * 100) if total_checkins > 0 else 0
            html += f"""
                            <tr>
                                <td><strong>{plan_stat[0]}</strong></td>
                                <td>{plan_stat[1]}</td>
                                <td>{percentage:.1f}%</td>
                            </tr>
            """
        
        html += """
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        """
        
        html += _generate_html_footer()
        
        # Salvar arquivo
        reports_dir = _get_reports_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"relatorio_frequencia_{timestamp}.html"
        filepath = reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return str(filepath)
    finally:
        if close_session:
            db_session.close()
