"""Gerador de relatório financeiro."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.data.database_manager import DatabaseManager


def _get_reports_dir() -> Path:
    """Retorna o diretório de relatórios, criando se não existir."""
    project_root = Path(__file__).parent.parent.parent
    reports_dir = project_root / "relatorios"
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def _generate_html_header(title: str) -> str:
    """Gera o cabeçalho e o CSS do relatório HTML."""
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f7fc;
            color: #333;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: auto;
            background: #fff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #6c5ce7;
            padding-bottom: 20px;
        }}
        .header h1 {{
            color: #6c5ce7;
            font-size: 2.5em;
        }}
        .header p {{
            font-size: 1.1em;
            color: #555;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #6c5ce7;
            font-size: 1.8em;
            margin-bottom: 20px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }}
        .section-description {{
            font-size: 1em;
            color: #555;
            margin-top: -15px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        .summary-card {{
            background: #f8f9fa;
            border-left: 5px solid #6c5ce7;
            padding: 20px;
            margin-bottom: 25px;
            border-radius: 8px;
        }}
        .summary-card p {{
            margin: 0;
            line-height: 1.6;
        }}
        .kpi-table th:nth-child(3), .kpi-table td:nth-child(3) {{
            text-align: right;
        }}
        .financial-table .level-2 {{
            padding-left: 30px;
        }}
        .financial-table .level-3 {{
            padding-left: 60px;
        }}
        .total-row {{
            font-weight: bold;
            background-color: #f8f9fa;
        }}
        .negative {{
            color: #d9534f;
        }}
        .positive {{
            color: #5cb85c;
        }}
        input[type="number"] {{
            width: 120px;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 5px;
            text-align: right;
            font-size: 1em;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #777;
        }}
    </style>
</head>
<body>
"""


def _generate_html_footer() -> str:
    """Gera o rodapé do HTML e o fechamento das tags."""
    return """
    <div class="footer">
        <p>Relatório gerado pelo Sistema de Gestão Summit</p>
    </div>
</body>
</html>
"""


def _generate_report_body(period: str, db_data: dict) -> str:
    """Gera o corpo do relatório com os dados e campos de entrada."""
    # Dados extraídos do banco para usar no HTML
    receita_mensalidades = db_data.get("receita_mensalidades", 0)
    passes_diarios_receita = db_data.get("passes_diarios_receita", 0)
    membros_ativos = db_data.get("membros_ativos", 0)
    novos_membros = db_data.get("novos_membros", 0)
    passes_diarios_vendidos = db_data.get("passes_diarios_vendidos", 0)

    return f"""
    <div class="container">
        <div class="header">
            <h1>Relatório Financeiro</h1>
            <p>Período de Análise: {period}</p>
        </div>

        <!-- 1. Sumário Executivo -->
        <div class="section">
            <h2>1. Sumário Executivo</h2>
            <p class="section-description">
                Uma visão geral e rápida dos resultados financeiros mais importantes do período. Ideal para uma análise imediata da saúde financeira.
            </p>
            <div class="summary-card">
                <p><strong>Visão Geral:</strong> <span id="summary-overview">O mês de {period} apresentou os seguintes resultados. Preencha os campos abaixo para uma análise completa.</span></p>
                <p><strong>Receita Total:</strong> <span id="summary-receita-total" class="positive">R$ 0,00</span></p>
                <p><strong>Despesas Totais:</strong> <span id="summary-despesas-totais" class="negative">R$ 0,00</span></p>
                <p><strong>Lucro/Prejuízo Líquido:</strong> <span id="summary-lucro-liquido">R$ 0,00</span></p>
                <p><strong>Saldo de Caixa Atual:</strong> <span id="summary-saldo-caixa">R$ 0,00</span></p>
            </div>
        </div>

        <!-- 2. KPIs -->
        <div class="section">
            <h2>2. KPIs (Indicadores-Chave de Desempenho)</h2>
            <p class="section-description">
                Métricas vitais que mostram a saúde operacional e o crescimento do negócio, comparando o desempenho atual com o período anterior.
            </p>
            <table class="kpi-table">
                <thead>
                    <tr>
                        <th>Indicador</th>
                        <th>Período Atual</th>
                        <th>Período Anterior</th>
                        <th>Variação (%)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Membros Ativos (Total)</td>
                        <td>{membros_ativos}</td>
                        <td><input type="number" id="kpi-membros-ativos-anterior" value="0" oninput="calculateAll()"></td>
                        <td id="kpi-membros-ativos-variacao">0,00%</td>
                    </tr>
                    <tr>
                        <td>Novos Membros</td>
                        <td>{novos_membros}</td>
                        <td><input type="number" id="kpi-novos-membros-anterior" value="0" oninput="calculateAll()"></td>
                        <td id="kpi-novos-membros-variacao">0,00%</td>
                    </tr>
                    <tr>
                        <td>Passes Diários Vendidos</td>
                        <td>{passes_diarios_vendidos}</td>
                        <td><input type="number" id="kpi-passes-diarios-anterior" value="0" oninput="calculateAll()"></td>
                        <td id="kpi-passes-diarios-variacao">0,00%</td>
                    </tr>
                    <tr>
                        <td>Alunos em Cursos/Aulas</td>
                        <td><input type="number" id="kpi-alunos-cursos-atual" value="0" oninput="calculateAll()"></td>
                        <td><input type="number" id="kpi-alunos-cursos-anterior" value="0" oninput="calculateAll()"></td>
                        <td id="kpi-alunos-cursos-variacao">0,00%</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- 3. DRE -->
        <div class="section">
            <h2>3. DRE (Demonstrativo do Resultado do Exercício)</h2>
            <p class="section-description">
                O DRE confronta receitas e despesas para determinar se a academia obteve lucro ou prejuízo no período (visão de competência).
            </p>
            <table class="financial-table">
                <tbody>
                    <tr class="total-row"><td>A. Receitas</td><td></td></tr>
                    <tr><td class="level-2">Receita com Mensalidades</td><td id="dre-receita-mensalidades">R$ {receita_mensalidades:,.2f}</td></tr>
                    <tr><td class="level-2">Receita com Visitantes (Passes Diários)</td><td id="dre-receita-passes">R$ {passes_diarios_receita:,.2f}</td></tr>
                    <tr class="total-row"><td>RECEITA BRUTA TOTAL</td><td id="dre-receita-bruta">R$ 0,00</td></tr>
                    <tr><td class="level-2">(- Impostos sobre Vendas/Serviços)</td><td>(<input type="number" id="dre-impostos-vendas" value="0" oninput="calculateAll()">)</td></tr>
                    <tr class="total-row"><td>= RECEITA LÍQUIDA</td><td id="dre-receita-liquida">R_CLIENT_SIDE</td></tr>

                    <tr class="total-row"><td>B. Despesas</td><td></td></tr>
                    <tr><td class="level-2">Despesas de Ocupação</td><td></td></tr>
                    <tr><td class="level-3">IPTU</td><td>(<input type="number" id="dre-despesa-iptu" value="0" oninput="calculateAll()">)</td></tr>
                    <tr><td class="level-3">Contas (Água, Luz, Internet)</td><td>(<input type="number" id="dre-despesa-contas" value="0" oninput="calculateAll()">)</td></tr>
                    <tr><td class="level-2">Despesas Operacionais</td><td></td></tr>
                    <tr><td class="level-3">Manutenção de Paredes e Agarras</td><td>(<input type="number" id="dre-despesa-manutencao-paredes" value="0" oninput="calculateAll()">)</td></tr>
                    <tr><td class="level-3">Manutenção de Equipamentos de Segurança</td><td>(<input type="number" id="dre-despesa-manutencao-equipamentos" value="0" oninput="calculateAll()">)</td></tr>
                    <tr><td class="level-3">Material de Limpeza e Escritório</td><td>(<input type="number" id="dre-despesa-material" value="0" oninput="calculateAll()">)</td></tr>
                    <tr class="total-row"><td>DESPESAS TOTAIS</td><td id="dre-despesas-totais">(R$ 0,00)</td></tr>

                    <tr class="total-row"><td>C. Resultado</td><td></td></tr>
                    <tr><td>EBITDA</td><td id="dre-ebitda">R$ 0,00</td></tr>
                    <tr><td class="level-2">(- Depreciação/Amortização)</td><td>(<input type="number" id="dre-depreciacao" value="0" oninput="calculateAll()">)</td></tr>
                    <tr><td>LUCRO OPERACIONAL (EBIT)</td><td id="dre-ebit">R$ 0,00</td></tr>
                    <tr><td class="level-2">(- Despesas Financeiras / Juros)</td><td>(<input type="number" id="dre-despesas-financeiras" value="0" oninput="calculateAll()">)</td></tr>
                    <tr><td>LUCRO LÍQUIDO (Antes dos Impostos)</td><td id="dre-lucro-antes-impostos">R$ 0,00</td></tr>
                    <tr><td class="level-2">(- Impostos sobre o Lucro)</td><td>(<input type="number" id="dre-impostos-lucro" value="0" oninput="calculateAll()">)</td></tr>
                    <tr class="total-row"><td>= LUCRO/PREJUÍZO LÍQUIDO</td><td id="dre-lucro-liquido">R$ 0,00</td></tr>
                </tbody>
            </table>
        </div>

        <!-- 4. DFC -->
        <div class="section">
            <h2>4. DFC (Demonstrativo de Fluxo de Caixa) - Método Direto</h2>
            <p class="section-description">
                O DFC rastreia o dinheiro que efetivamente entrou e saiu do caixa, mostrando a liquidez real da empresa no período.
            </p>
            <table class="financial-table">
                <tbody>
                    <tr><td>Saldo Inicial em Caixa</td><td><input type="number" id="dfc-saldo-inicial" value="0" oninput="calculateAll()"></td></tr>
                    <tr class="total-row"><td>A. Entradas de Caixa (Operacionais)</td><td></td></tr>
                    <tr><td class="level-2">Recebimento de Mensalidades</td><td id="dfc-entrada-mensalidades">R$ {receita_mensalidades:,.2f}</td></tr>
                    <tr><td class="level-2">Recebimento de Passes Diários</td><td id="dfc-entrada-passes">R$ {passes_diarios_receita:,.2f}</td></tr>
                    <tr class="total-row"><td>B. Saídas de Caixa (Operacionais)</td><td></td></tr>
                    <tr><td class="level-2">Pagamento de Despesas de Ocupação</td><td id="dfc-saida-ocupacao">(R$ 0,00)</td></tr>
                    <tr><td class="level-2">Pagamento de Despesas Operacionais</td><td id="dfc-saida-operacionais">(R$ 0,00)</td></tr>
                    <tr class="total-row"><td>= FLUXO DE CAIXA OPERACIONAL</td><td id="dfc-fluxo-caixa-op">R$ 0,00</td></tr>
                    <tr class="total-row"><td>C. Atividades de Investimento</td><td></td></tr>
                    <tr><td class="level-2">Compra de novas agarras ou equipamentos</td><td>(<input type="number" id="dfc-investimento-agarras" value="0" oninput="calculateAll()">)</td></tr>
                    <tr><td class="level-2">Reforma ou expansão da parede</td><td>(<input type="number" id="dfc-investimento-reforma" value="0" oninput="calculateAll()">)</td></tr>
                    <tr class="total-row"><td>= FLUXO DE CAIXA DE INVESTIMENTO</td><td id="dfc-fluxo-caixa-inv">(R$ 0,00)</td></tr>
                    <tr class="total-row"><td>SALDO FINAL DE CAIXA</td><td id="dfc-saldo-final">R$ 0,00</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    """


def _generate_javascript(db_data: dict) -> str:
    """Gera o bloco de script com a lógica de cálculo."""
    # Dados do DB para injetar no JS
    receita_mensalidades = db_data.get("receita_mensalidades", 0)
    passes_diarios_receita = db_data.get("passes_diarios_receita", 0)
    membros_ativos = db_data.get("membros_ativos", 0)
    novos_membros = db_data.get("novos_membros", 0)
    passes_diarios_vendidos = db_data.get("passes_diarios_vendidos", 0)

    return f"""
    <script>
        const DB_DATA = {{
            receitaMensalidades: {receita_mensalidades},
            passesDiariosReceita: {passes_diarios_receita},
            membrosAtivos: {membros_ativos},
            novosMembros: {novos_membros},
            passesDiariosVendidos: {passes_diarios_vendidos}
        }};

        function getVal(id) {{
            return parseFloat(document.getElementById(id).value) || 0;
        }}

        function setHtml(id, value, isCurrency = true) {{
            const element = document.getElementById(id);
            if (!element) return;

            let formattedValue = isCurrency ? `R$ ${{value.toFixed(2).replace('.', ',')}}` : value;
            if (typeof value === 'string' && value.includes('%')) {{
                formattedValue = value;
            }}
            
            element.innerHTML = formattedValue;
            element.classList.remove('positive', 'negative');
            if (value > 0) {{
                element.classList.add('positive');
            }} else if (value < 0) {{
                element.classList.add('negative');
            }}
        }}

        function calculateAll() {{
            // KPI Calculations
            const kpiMembrosAtivosAnterior = getVal('kpi-membros-ativos-anterior');
            const kpiNovosMembrosAnterior = getVal('kpi-novos-membros-anterior');
            const kpiPassesDiariosAnterior = getVal('kpi-passes-diarios-anterior');
            const kpiAlunosCursosAtual = getVal('kpi-alunos-cursos-atual');
            const kpiAlunosCursosAnterior = getVal('kpi-alunos-cursos-anterior');

            const calcVariacao = (atual, anterior) => anterior > 0 ? ((atual / anterior) - 1) * 100 : (atual > 0 ? 100 : 0);
            
            setHtml('kpi-membros-ativos-variacao', `${{calcVariacao(DB_DATA.membrosAtivos, kpiMembrosAtivosAnterior).toFixed(2)}}%`, false);
            setHtml('kpi-novos-membros-variacao', `${{calcVariacao(DB_DATA.novosMembros, kpiNovosMembrosAnterior).toFixed(2)}}%`, false);
            setHtml('kpi-passes-diarios-variacao', `${{calcVariacao(DB_DATA.passesDiariosVendidos, kpiPassesDiariosAnterior).toFixed(2)}}%`, false);
            setHtml('kpi-alunos-cursos-variacao', `${{calcVariacao(kpiAlunosCursosAtual, kpiAlunosCursosAnterior).toFixed(2)}}%`, false);

            // DRE Calculations
            const receitaBruta = DB_DATA.receitaMensalidades + DB_DATA.passesDiariosReceita;
            setHtml('dre-receita-bruta', receitaBruta);

            const impostosVendas = getVal('dre-impostos-vendas');
            const receitaLiquida = receitaBruta - impostosVendas;
            setHtml('dre-receita-liquida', receitaLiquida);

            const despesaIptu = getVal('dre-despesa-iptu');
            const despesaContas = getVal('dre-despesa-contas');
            const despesaManutencaoParedes = getVal('dre-despesa-manutencao-paredes');
            const despesaManutencaoEquip = getVal('dre-despesa-manutencao-equipamentos');
            const despesaMaterial = getVal('dre-despesa-material');
            const despesasTotais = despesaIptu + despesaContas + despesaManutencaoParedes + despesaManutencaoEquip + despesaMaterial;
            setHtml('dre-despesas-totais', despesasTotais);

            const ebitda = receitaLiquida - despesasTotais;
            setHtml('dre-ebitda', ebitda);

            const depreciacao = getVal('dre-depreciacao');
            const ebit = ebitda - depreciacao;
            setHtml('dre-ebit', ebit);

            const despesasFinanceiras = getVal('dre-despesas-financeiras');
            const lucroAntesImpostos = ebit - despesasFinanceiras;
            setHtml('dre-lucro-antes-impostos', lucroAntesImpostos);

            const impostosLucro = getVal('dre-impostos-lucro');
            const lucroLiquido = lucroAntesImpostos - impostosLucro;
            setHtml('dre-lucro-liquido', lucroLiquido);

            // DFC Calculations
            const saldoInicial = getVal('dfc-saldo-inicial');
            const saidaOcupacao = despesaIptu + despesaContas;
            setHtml('dfc-saida-ocupacao', -saidaOcupacao);
            const saidaOperacionais = despesaManutencaoParedes + despesaManutencaoEquip + despesaMaterial;
            setHtml('dfc-saida-operacionais', -saidaOperacionais);
            
            const fluxoCaixaOp = receitaBruta - saidaOcupacao - saidaOperacionais;
            setHtml('dfc-fluxo-caixa-op', fluxoCaixaOp);

            const investimentoAgarras = getVal('dfc-investimento-agarras');
            const investimentoReforma = getVal('dfc-investimento-reforma');
            const fluxoCaixaInv = -investimentoAgarras - investimentoReforma;
            setHtml('dfc-fluxo-caixa-inv', fluxoCaixaInv);

            const saldoFinal = saldoInicial + fluxoCaixaOp + fluxoCaixaInv;
            setHtml('dfc-saldo-final', saldoFinal);

            // Update Summary
            setHtml('summary-receita-total', receitaBruta);
            setHtml('summary-despesas-totais', despesasTotais);
            setHtml('summary-lucro-liquido', lucroLiquido);
            setHtml('summary-saldo-caixa', saldoFinal);
        }}

        // Initial calculation on page load
        window.onload = calculateAll;
    </script>
    """


def generate_finance_report(db_manager: DatabaseManager, period: str) -> str:
    """
    Gera o relatório financeiro completo para um dado período.
    
    Args:
        db_manager: Gerenciador do banco de dados.
        period: String descrevendo o período (ex: "Novembro/2025").
        
    Returns:
        Caminho do arquivo HTML gerado.
    """
    if not db_manager.connection and not db_manager.connect():
        raise RuntimeError("Não foi possível conectar ao banco de dados.")

    # TODO: Implementar a lógica de busca no banco de dados baseada no período.
    # Por enquanto, usaremos dados mocados para a estrutura.
    db_data = {
        "receita_mensalidades": 15000,
        "passes_diarios_receita": 2500,
        "membros_ativos": 150,
        "novos_membros": 12,
        "passes_diarios_vendidos": 50,
    }

    html = _generate_html_header(f"Relatório Financeiro - {period}")
    html += _generate_report_body(period, db_data)
    html += _generate_javascript(db_data)
    html += _generate_html_footer()

    # Salvar arquivo
    reports_dir = _get_reports_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"relatorio_financeiro_{timestamp}.html"
    filepath = reports_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return str(filepath)
