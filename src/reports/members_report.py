"""Gerador de relatório de membros."""

from __future__ import annotations

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


def _parse_date(date_str: str) -> datetime:
    """Parse date from database format."""
    if not date_str:
        return None
    try:
        # Try various formats
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
    except Exception:
        pass
    return None


def _get_status_info(vencimento_str: str) -> tuple[str, str]:
    """Retorna status e classe CSS baseado no vencimento."""
    if not vencimento_str:
        return ("Sem Data", "expired")
    
    vencimento = _parse_date(vencimento_str)
    if not vencimento:
        return ("Data Inválida", "expired")
    
    today = datetime.now()
    days_until = (vencimento - today).days
    
    if days_until < 0:
        return ("Vencido", "expired")
    elif days_until <= 7:
        return (f"Vence em {days_until}d", "expiring")
    else:
        return ("Ativo", "active")


def generate_members_report(db_manager: DatabaseManager) -> str:
    """
    Gera relatório completo de membros.
    
    Args:
        db_manager: Gerenciador do banco de dados
        
    Returns:
        Caminho do arquivo HTML gerado
    """
    if not db_manager.connection and not db_manager.connect():
        raise RuntimeError("Não foi possível conectar ao banco de dados")
    
    cursor = db_manager.connection.cursor()
    
    # Estatísticas gerais
    cursor.execute("SELECT COUNT(*) FROM membros")
    total_members = cursor.fetchone()[0]
    
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM membros WHERE vencimento_plano >= ?", (today,))
    active_members = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM membros WHERE vencimento_plano < ?", (today,))
    expired_members = cursor.fetchone()[0]
    
    week_ahead = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    cursor.execute("""
        SELECT COUNT(*) FROM membros 
        WHERE vencimento_plano >= ? AND vencimento_plano <= ?
    """, (today, week_ahead))
    expiring_soon = cursor.fetchone()[0]
    
    # Distribuição por plano
    cursor.execute("""
        SELECT plano, COUNT(*) as total
        FROM membros
        GROUP BY plano
        ORDER BY total DESC
    """)
    plan_distribution = cursor.fetchall()
    
    # Distribuição por gênero
    cursor.execute("""
        SELECT genero, COUNT(*) as total
        FROM membros
        GROUP BY genero
        ORDER BY total DESC
    """)
    gender_distribution = cursor.fetchall()
    
    # Lista completa de membros
    cursor.execute("""
        SELECT 
            nome,
            email,
            whatsapp,
            plano,
            vencimento_plano,
            genero,
            data_nascimento
        FROM membros
        ORDER BY nome
    """)
    members = cursor.fetchall()
    
    cursor.close()
    
    # Gerar HTML
    html = _generate_html_header("Relatório de Membros")
    
    html += f"""
    <div class="container">
        <div class="header">
            <h1>👤 Relatório de Membros</h1>
            <p class="subtitle">Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
        </div>
        
        <div class="content">
            <div class="stats-grid">
                <div class="stat-card blue">
                    <div class="label">Total de Membros</div>
                    <div class="value">{total_members}</div>
                </div>
                
                <div class="stat-card green">
                    <div class="label">Ativos</div>
                    <div class="value">{active_members}</div>
                </div>
                
                <div class="stat-card orange">
                    <div class="label">Vencendo (7 dias)</div>
                    <div class="value">{expiring_soon}</div>
                </div>
                
                <div class="stat-card">
                    <div class="label">Vencidos</div>
                    <div class="value">{expired_members}</div>
                </div>
            </div>
            
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
    
    for plan, count in plan_distribution:
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
    
    for gender, count in gender_distribution:
        percentage = (count / total_members * 100) if total_members > 0 else 0
        gender_label = gender or "Não Informado"
        html += f"""
                        <tr>
                            <td><strong>{gender_label}</strong></td>
                            <td>{count}</td>
                            <td>{percentage:.1f}%</td>
                        </tr>
        """
    
    html += """
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>📋 Lista Completa de Membros</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Nome</th>
                            <th>Plano</th>
                            <th>Status</th>
                            <th>Vencimento</th>
                            <th>Contato</th>
                            <th>Gênero</th>
                            <th>Nascimento</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for member in members:
        nome, email, whatsapp, plano, vencimento, genero, nascimento = member
        status_text, status_class = _get_status_info(vencimento)
        
        vencimento_display = _parse_date(vencimento).strftime('%d/%m/%Y') if vencimento and _parse_date(vencimento) else 'N/A'
        nascimento_display = _parse_date(nascimento).strftime('%d/%m/%Y') if nascimento and _parse_date(nascimento) else 'N/A'
        
        contact_info = []
        if email:
            contact_info.append(f"✉️ {email}")
        if whatsapp:
            contact_info.append(f"📱 {whatsapp}")
        contact_display = "<br>".join(contact_info) if contact_info else "Sem contato"
        
        html += f"""
                        <tr>
                            <td><strong>{nome}</strong></td>
                            <td><span class="plan-badge">{plano}</span></td>
                            <td><span class="status-badge {status_class}">{status_text}</span></td>
                            <td>{vencimento_display}</td>
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
    
    html += _generate_html_footer()
    
    # Salvar arquivo
    reports_dir = _get_reports_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"relatorio_membros_{timestamp}.html"
    filepath = reports_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return str(filepath)
