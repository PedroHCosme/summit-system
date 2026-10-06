# Membros arquivados e legenda de classificacao — Design

Glossario: [CONTEXT.md](../../../CONTEXT.md). Relatorios: `.claude/docs/REPORTS_STATUS.md`.

## Problema

Quem parou de ir a academia ha meses continua na base e distorce os relatorios: infla "inativos", "risco" e "reativacao urgente" e dilui os percentuais. O dono tambem nao ve, nos relatorios de Membros e Financeiro, o que significa "ativo", "estavel" ou "em risco".

## 1. Regra de Arquivado

Um membro esta **arquivado** quando todas as condicoes valem:

1. Passaram mais de **90 dias** (`DIAS_ARQUIVAR`) desde o ultimo check-in. Quem nunca fez check-in conta desde `data_cadastro`. Sem check-in e sem cadastro, conta como arquivado.
2. Nenhum plano vigente: `vencimento_plano` e `vencimento_treino` anteriores a hoje (ou vazios).
3. Nenhum pagamento nos ultimos 90 dias.

- Calculado na hora de gerar o relatorio. **Nada novo no banco** e nenhum botao: um check-in ou pagamento novo desarquiva sozinho.
- 90 dias exatos ainda nao arquivam; 91 arquivam.
- Funcao pura `esta_arquivado(...)` em `src/core/plan_status.py`; `ids_arquivados(session, hoje)` em `src/reports/_common.py` devolve o conjunto de ids (uma consulta de ultimo check-in e uma de ultimo pagamento por membro).

## 2. Onde o Arquivado sai

| Relatorio | Efeito |
|---|---|
| Membros | Fora de contagens, segmentos, filas e lista. Rodape: "N membros arquivados nao entram nestas contagens". Sem lista de arquivados. |
| Financeiro | Fora das contagens de membros e dos segmentos de retencao. **Receita, ticket, DRE, extrato e o ranking por plano ficam intactos** (o ranking por plano usa todos os membros para continuar batendo com a receita). Mesmo rodape. |
| Frequencia | Fora de "membros em risco". |
| Resumo Semanal e Mensal | Fora so das listas de contato: Candidatos, Vencidos que vieram e Inativos. Numeros (check-ins, receita, mapa, renovacoes) nao mudam: quem esta arquivado nao tem check-in nos ultimos 90 dias. No semanal so Candidatos pode mudar (12 Semanas cobrem ~84 dias, entao "Vencidos que vieram" nunca tem arquivado); Vencidos e Inativos mudam no mensal, que olha 12 meses para tras. |

Decisoes do dono: mecanismo automatico e calculado; plano em dia protege; so a "foto de hoje" some nos resumos; receita fica intacta.

Limites conhecidos:
- Listas de contato de Periodos antigos perdem quem foi arquivado depois.
- Renovacoes nao e filtrado, para "Renovaram X de Y" continuar batendo com a lista de nao renovaram.
- Pacote (quota) com creditos sobrando mas sem check-in nem pagamento ha 90 dias e arquivado.
- `data_cadastro` de importados de planilha e a data da importacao, o que da 90 dias de folga a quem nunca fez check-in.

## 3. Legenda "Como classificamos os membros"

Secao no fim dos Relatorios de Membros e Financeiro, gerada por `legenda_segmentos()` (`src/reports/analytics.py`) a partir das constantes de `plan_status.py`, para nao desatualizar. Mostra:

- **Ativo** (KPI "Ativos"): ultimo check-in dentro do limite do plano (14 dias mensal e similares, 30 pacote, 45 Gympass/Totalpass/diaria/cortesia; pacote tambem exige creditos).
- As cinco faixas com a regra em dias para os tres grupos: Muito ativo, Estavel, Risco moderado (limite), Risco alto (limite + 14, ou plano vencido com mais de 14 dias), Reativacao urgente (limite + 30).
- **Arquivado**: a regra da secao 1 e o aviso de que fica fora dos relatorios.

Nomes mantidos como ja existem ("moderadamente ativo" = Estavel; "em risco" = as tres faixas de risco).

## Testes

- `esta_arquivado`: 90/91 dias, plano e treino vigentes, pagamento recente (89/91), sem check-in com cadastro, sem nada.
- `ids_arquivados` com banco em memoria.
- Analytics e Financeiro: arquivado sai das contagens e filas, continua na receita por plano, rodape e legenda aparecem.
- Frequencia, Semanal e Mensal: arquivado sai das listas de contato.
