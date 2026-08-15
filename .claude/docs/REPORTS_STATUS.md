# Status dos Relatorios — Summit System

## Visao Geral

Tres relatorios HTML gerados via Jinja2 + Chart.js, abertos no navegador.
Publico-alvo: dono da academia (unico consumidor).

---

## Estado Atual vs Desejado

### Relatorio Financeiro (`src/reports/finance_report.py`)

**Template**: `src/templates/reports/finance_report.html`

#### O que tem hoje
- KPIs: Receita Bruta, Ticket Medio, Descontos (hardcoded 0), Receita Liquida
- KPIs secundarios: Taxa Inadimplencia, Projecao Mensal, Total Transacoes
- Comparativo com periodo anterior (delta %)
- DRE simplificado (mensalidades vs avulsos)
- Graficos: metodos de pagamento (doughnut) + receita por plano (bar)
- Extrato de pagamentos (limite 200)

#### Problemas conhecidos
1. **Receita de treino nao aparece separada** — misturada com outros pagamentos ou ausente
2. **Projecao de receita usa magic number** (12 checkins/mes) — deveria usar historico real
3. **Descontos sempre R$ 0.00** — campo hardcoded, nao reflete realidade
4. **DRE classifica por string matching** ("Plano" ou "Mensal" no tipo_transacao) — fragil
5. **Dados de chart agregados das 200 transacoes** — deveria usar breakdown do servico
6. **Bypass do service layer** — acessa `member_service.session.query(Membro)` direto
7. **Valores possivelmente errados** — usuario reportou receita desbalanceada ao gerar relatorio de 1 mes
8. **Membros PENDENTE incluidos** nas contagens de inadimplencia — devem ser excluidos

#### O que falta
- [x] Receita de treino como categoria separada no DRE — FEITO
- [x] Excluir membros PENDENTE de todas as contagens — FEITO
- [x] PlanService para precos (migrado de config.py) — FEITO
- [ ] Projecao baseada em dados historicos reais
- [ ] Remover campo de descontos ou implementar de verdade
- [ ] Validar que a receita bate com os pagamentos do periodo
- [ ] Receita por metodo deve vir do breakdown completo, nao das 200 transacoes

---

### Relatorio de Membros (`src/reports/members_report.py`)

**Template**: `src/templates/reports/members_report.html`

#### O que tem hoje
- KPIs: Total cadastrado, Ativos, Inativos, Periodo de Graca
- KPIs periodo: Novos no periodo, Churn, Taxa de Retencao
- Graficos: status (doughnut) + planos (bar horizontal)
- Tabela detalhada com busca e filtro por status
- Colunas: Nome, Plano, Status, Vencimento, Dias Restantes

#### Problemas conhecidos
1. **Status mistura conceitos** — usa `determine_status_simples()` que conflita com regras de negocio novas
2. **"Periodo de Graca" nao existe mais** — regra removida pelo dono (ver BUSINESS_RULES.md)
3. **Status deveria ser separado** — status do plano (EM DIA/VENCIDO) vs status do membro (ATIVO/INATIVO por frequencia)
4. **Churn detection fragil** — baseado em vencimento_plano no periodo + status INATIVO, sem considerar frequencia
5. **Membros PENDENTE incluidos** nos totais — devem ser excluidos
6. **Nao mostra inadimplencia detalhada** — quem deve, ha quanto tempo, quanto
7. **Dias restantes confuso** para planos sem vencimento (quota, per-checkin) — mostra 0

#### O que falta
- [x] Separar status do plano (EM DIA / VENCIDO / SEM VENCIMENTO) de status do membro (ATIVO / INATIVO por frequencia) — FEITO
- [x] Remover "Periodo de Graca" como conceito — FEITO
- [x] Excluir membros PENDENTE — FEITO
- [x] Status do membro baseado em ultimo check-in por tipo de plano — FEITO
- [x] Coluna "Ultimo Check-in" na tabela — FEITO
- [x] Tratar planos sem vencimento adequadamente (exibe dash ao inves de 0) — FEITO
- [ ] Adicionar secao de inadimplencia detalhada (membros com plano vencido + dias de atraso)

---

### Relatorio de Frequencia (`src/reports/frequency_report.py`)

**Template**: `src/templates/reports/frequency_report.html`

#### O que tem hoje
- KPIs: Total check-ins, Membros unicos, Media diaria, Dia mais movimentado
- Grafico de tendencia (linha, ultimos N dias)
- Tabelas: por dia da semana, por plano
- Top 10 membros mais frequentes
- Membros em risco de churn (ativos sem check-in no periodo)

#### Problemas conhecidos
1. **Dia mais movimentado** exibido em formato YYYY-MM-DD — deveria ser DD/MM/YYYY
2. **Membros em risco** so considera `estado_plano = 'ATIVO'` — deveria usar nova regra de status
3. **Porcentagem inconsistente** — top_members usa `total/dias` mas weekday usa `total/total_checkins`
4. **Membros PENDENTE** podem aparecer se estado_plano foi marcado errado
5. **Dados de dia da semana** usam `strftime('%w')` do SQLite — funciona mas e fragil

#### O que falta
- [x] Formatar data do dia mais movimentado para DD/MM/YYYY — FEITO
- [x] Excluir membros PENDENTE — FEITO
- [x] Adicionar "ultimo check-in" na tabela de membros em risco — FEITO
- [ ] Usar nova regra de status do membro (calcular_status_membro) na query de risco em vez de estado_plano == ATIVO
- [ ] Unificar denominadores de porcentagem (top_members usa total/dias, weekday usa total/total_checkins)

---

## Problemas Transversais (afetam todos os relatorios)

### Dados
1. **Membros PENDENTE incluidos** — filtrar em todos os relatorios
2. **Status misturado** — separar status_plano de status_membro em todo o sistema
3. **config.py vs tabela Plano** — relatorios usam config.py para precos, deveria usar banco
4. **Bypass do service layer** — relatorios fazem queries diretas ao ORM

### Template/Visual
5. **Formato de data inconsistente** — DD/MM/YYYY no financeiro, YYYY-MM-DD na frequencia
6. **Formato de chart JSON diferente** entre os 3 relatorios — padronizar
7. **Print/PDF** — sem botao de exportacao nativo, usuario precisa usar print do browser

### Arquitetura
8. **Session management inconsistente** — financeiro recebe services, membros/frequencia recebem session
9. **Nenhum relatorio usa PlanService** — todos fazem queries diretas ou usam config.py
10. ~~**Helpers duplicados** — `_get_reports_dir()` e `_get_template_env()` repetidos em cada arquivo~~ — **RESOLVIDO em 2026-08-15**: extraidos para `src/reports/_common.py` (`get_reports_dir()`/`get_template_env()`, sem underscore), importados pelos 3 geradores.

---

## Roadmap de Melhorias

### Fase 1: Fundacao — CONCLUIDA (2026-04-08)
- [x] Implementar separacao status_plano vs status_membro em plan_status.py
      - calcular_status_plano(): EM DIA / VENCIDO / SEM VENCIMENTO (baseado em data)
      - calcular_status_membro(): ATIVO / INATIVO (baseado em frequencia de check-ins)
      - Thresholds: 14 dias (mensal/periodic), 45 dias (Gympass/Totalpass/Diaria/Cortesia), 30 dias + creditos (quota)
- [x] Filtrar PENDENTE em todos os relatorios (membros, financeiro, frequencia)
- [x] Migrar precos para PlanService (finance_report.py usa get_plan_prices() e get_checkin_payment_plans())
- [x] members_report.py: refatorado com subquery para ultimo check-in, dois status separados
- [x] finance_report.py: treino como categoria separada no DRE, PENDENTE excluido da inadimplencia
- [x] frequency_report.py: PENDENTE excluido, data do dia mais movimentado formatada DD/MM/YYYY,
      ultimo_checkin adicionado na tabela de membros em risco
- [x] members_report.html: redesenhado — tres graficos (status plano + atividade + planos),
      filtros duplos (plano + frequencia), coluna Ultimo Check-in, sem Periodo de Graca
- [x] frequency_report.html: coluna Ultimo Check-in adicionada na tabela de risco

### Fase 2: Relatorios Corretos — CONCLUIDA (2026-04-08)
- [x] DRE: classificacao robusta por tipo_transacao com _categoria_dre()
      - Palavras-chave para treino: TREINO, PERSONAL, PT
      - Palavras-chave para mensalidades: RENOVA, VOUCHER, COMPRA, MENSAL, TRIMEST, SEMEST, ANUAL, ESCOLINHA
      - Tudo mais vai para avulsos (Diaria, Gympass, Totalpass, Check-in...)
- [x] Auditoria DRE: bloco de reconciliacao mostra receita_bruta vs dre_total, flag verde/vermelho,
      mapeamento de tipo_transacao -> categoria em <details> expansivel
- [x] Descontos hardcoded removidos: campo total_descontos retirado de kpis e do DRE
      (modelo Pagamento nao tem campo desconto — nao rastrear o que nao existe)
- [x] Inadimplencia detalhada em members_report: lista de membros com plano VENCIDO,
      dias em atraso (3 faixas de cor: <30d amarelo, 31-60d laranja, >60d vermelho),
      valor do plano estimado (de PlanService), ultimo check-in
      Receita mensal total em risco exibida no cabecalho da secao
- [x] Validacao com dados simulados: test_reports_jinja.py cria DB em memoria com 18 membros,
      13 pagamentos, check-ins variados, e valida as 3 principais assercoes de cada relatorio
      Resultado: 3/3 relatorios, 0 erros

### Fase 3: Relatorios Ricos
- [ ] Projecao financeira baseada em historico real (media movel)
- [ ] Export PDF nativo
- [ ] Comparativo mes a mes (nao so periodo anterior)
- [ ] Dashboard de metricas no proprio app (sem abrir navegador)
