# Resumo Mensal e ajustes de membro — Design

Glossario: [CONTEXT.md](../../../CONTEXT.md). Base: [Resumo Semanal](2026-09-28-resumo-semanal-design.md).

Quatro entregas independentes, na ordem de tamanho.

## 1. Plano errado ao editar membro

**Bug**: `EditMemberDialog` so lista planos *ativos* da tabela `Plano`. Se o plano do membro nao esta na lista (ex.: "Diaria Boulder"), `_populate_fields` nao seleciona nada, o Qt mostra o primeiro item ("Mensal") e o Salvar troca o plano do membro sem ninguem escolher.

**Correcao** (`src/ui/dialogs/edit_member_dialog.py`):
- Plano do membro fora da lista: entra no combo como item extra e vem selecionado. Salvar sem mexer mantem o plano (`plano_changed` falso).
- Membro sem plano: combo abre em branco. A validacao existente ("O plano do membro e obrigatorio") bloqueia o Salvar ate alguem escolher.

Fora do escopo: cadastrar como ativos os planos que faltam no banco (dado, nao codigo).

**Teste**: dialogo com `plano="Diária Boulder"` fora da lista mostra esse plano e nao marca troca ao salvar; com `plano=None` o combo fica em branco e o Salvar e bloqueado.

## 2. Perfil aberto pelo dashboard sem historicos

**Bug**: `on_dashboard_member_clicked` (`members_coordinator.py`) so chama `display_member_data`. A busca normal tambem chama `load_member_history` e `load_member_financial_history` (linhas 220-222), por isso as abas Frequencia e Financeiro ficam vazias.

**Correcao**: chamar as duas depois de `display_member_data`, com `member["nome"]`.

## 3. Mapa de calor do Resumo Semanal so da Semana

- `_mapa_de_calor` passa a receber os check-ins da Semana (`da_semana`), nao a janela de 4 Semanas.
- Titulo no template: "Lotação (desta semana)".
- Limite de destaque da celula cai de 5 para 3 no semanal (uma Semana tem poucos check-ins por dia x hora). O mensal mantem 5.
- Candidatos e Perfil continuam com a janela de 4 Semanas (regra do CONTEXT.md).

**Teste** (`tests/test_weekly_summary.py`): check-in de Semana anterior nao entra na celula do mapa.

## 4. Resumo Mensal

Mesmo relatorio, janela de **Mes** (calendario fechado, dia 1 ao ultimo dia), com 4 blocos extras.

### Reaproveitamento do motor

- `_semana(seg, ...)` vira `_periodo(ini, fim, ...)` (fim exclusivo, `fim - ini` em dias). O semanal chama com 7 dias.
- Parametros que mudam por chamada: limite de destaque do mapa (3 ou 5) e quantos periodos anteriores entram na media (4 Semanas ou 3 Meses).
- `janela` de Candidatos/Perfil passa a ser `[fim - 28 dias, fim)`. No semanal isso e igual a `seg - 21 dias`.
- `media4` vira `media`. O rotulo ("média 4 sem." / "média 3 meses") vem do template.
- `_carregar` passa a devolver tambem `member_id` dos pagamentos (necessario para Renovacoes).
- Modulos: o motor fica em `src/reports/weekly_summary.py`. `src/reports/monthly_summary.py` traz `mes_fechado(hoje)`, `montar_meses`, os blocos extras e `generate_monthly_summary`.

### Conteudo (ordem da tela)

Igual ao semanal, com "Semana" trocado por "Mes" (cabecalho "Setembro/2026", setas entre os ultimos 12 meses fechados; comparativos com o mes anterior e a media dos 3 anteriores), mais:

1. **Evolucao semana a semana**: blocos Segunda-Domingo recortados ao mes, com check-ins, % Gym/Totalpass e Receita de cada bloco (tabela).
2. **Membros novos**: `data_cadastro` dentro do mes, por Categoria de Cliente. Mostra "X de Y voltaram" (voltou = 2 ou mais check-ins ate o fim do mes).
3. **Renovacoes vs. nao renovacoes**: Assinantes com pagamento cuja `nova_data_vencimento` cai no mes. Renovou = existe pagamento posterior com `nova_data_vencimento` maior. Nao renovou vem com link `wa.me`. Renovacao tardia depois do mes conta como renovou.
4. **Inativos**: membros com check-in no mes anterior e nenhum neste mes, com `wa.me`, ordenados por check-ins do mes anterior.

Membros PENDENTE ficam fora de tudo (ja e regra do `_carregar`).

### Template

Um so template (`weekly_summary.html`), parametrizado por `DADOS.termos` (Semana/Mes, rotulos das medias) e por `DADOS.mensal`: os 4 blocos extras so aparecem quando o dado existe. Textos fixos como "nesta semana" e "em 4 semanas" passam a vir de `termos`.

### Acesso

- Botao "📆 Resumo Mensal" na sidebar, ao lado do semanal (`reports_monthly_clicked` -> `ReportsCoordinator.generate_monthly_summary`).
- Sem aviso automatico de inicio de mes (nao pedido).
- Arquivo gerado: `resumo_mensal_<timestamp>.html`.

### Documentacao a atualizar

`CONTEXT.md` (termo **Mes**), `.claude/docs/REPORTS_STATUS.md` e `scripts/seed_demo_db.py` (data_cadastro = dia do 1o check-in, para o demo ter Membros novos).

### Testes (`tests/test_monthly_summary.py`)

- `mes_fechado`: em qualquer dia de outubro devolve setembro; em janeiro devolve dezembro do ano anterior.
- Check-in fora do mes nao entra nos totais nem no mapa.
- Novos, Renovacoes e Inativos com casos pequenos montados em SQLite em memoria (como `test_weekly_summary.py`).
- Regressao: as saidas do semanal continuam iguais, exceto o mapa (item 3).

## Limites conhecidos

- Renovacoes so enxerga renovacoes com pagamento registrado (`nova_data_vencimento`). Renovacao lancada so por edicao manual do vencimento nao aparece.
- Como no semanal, Perdas para Gym/Totalpass anteriores a migracao do Tipo do Check-in ficam invisiveis.
