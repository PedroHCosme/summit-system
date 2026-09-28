# Resumo Semanal — Design

Glossario: [CONTEXT.md](../../../CONTEXT.md). Decisao de modelo: [ADR 0001](../../adr/0001-tipo-do-checkin-gravado-no-checkin.md).

## Problema

O dono nao usa os relatorios: sao longos, organizados por tabela do banco e nao pelas perguntas dele. A dor principal e o Gym/Totalpass, que e ~38% dos check-ins (banco real, dez/2025–jan/2026) e rende R$15 por visita.

## Objetivo

Ajudar o dono a (a) converter membros Gym/Totalpass, (b) ver a lotacao que eles causam e (c) decidir se vale continuar com os parceiros.

## Entrega

1. **Resumo Semanal**: novo relatorio HTML (Jinja + Chart.js, mesmo stack dos atuais), com tela unica e aberto sem dialogo de periodo.
   - Abre na ultima Semana fechada. Setas ← → navegam entre as 12 Semanas embutidas no arquivo. A semana parcial fica de fora.
   - Semana = segunda 00:00 ate domingo 23:59. Domingo conta nos totais, mas nao ganha coluna nos graficos por dia.
2. **Aviso de segunda-feira**: na primeira conexao do app numa segunda, pergunta "Abrir o resumo da semana passada?", uma vez por dia.
3. **Relatorios de Detalhe**: continuam os 3.
   - Frequencia passa a agrupar a tabela "por plano" pelo Tipo do Check-in.
   - Frequencia ganha botao na sidebar, porque hoje nao esta acessivel pela UI.
4. **Tipo do Check-in**: coluna `frequencia.plano`, gravada no check-in, com backfill feito uma unica vez (ADR 0001).
5. **Banco simulado** `demo_database.db`, gerado por `scripts/seed_demo_db.py`: fora do git, recusa gravar no banco real, e o app o usa via `SUMMIT_DB_PATH`.

## Conteudo do Resumo (ordem da tela)

1. Cabecalho "Semana dd/mm – dd/mm" com setas.
2. Numeros grandes. Cada um vem com a semana anterior e a media das 4 anteriores, para calcular a variacao.
   - Check-ins.
   - % Gym/Totalpass.
   - Receita da Semana (caixa: soma dos pagamentos com data na Semana).
   - Valor por Visita, Assinante vs Gym/Totalpass (competencia):
     - Gym/Totalpass = pagamentos Gympass/Totalpass da Semana ÷ check-ins Gym/Totalpass.
     - Assinante = receita rateada por dia dos pagamentos com `nova_data_vencimento` (exceto Treino) que cobrem a Semana ÷ check-ins de Assinante.
3. Check-ins por dia (seg–sab), em barras empilhadas por Categoria de Cliente.
4. Mapa de calor dia × hora das 4 Semanas terminando nesta. Frase com as 2 celulas de maior % Gym/Totalpass, considerando so celulas com 5 ou mais check-ins.
5. Conversoes e Perdas para Gym/Totalpass da Semana (nomes). O check-in da Semana e comparado com o check-in anterior do mesmo membro.
6. Acoes.
   - Candidatos a Conversao: membro Gym/Totalpass com 8 ou mais check-ins Gym/Totalpass nas 4 Semanas, com link `wa.me`.
   - "Vieram na semana e estao com plano vencido": Assinantes com check-in na Semana e `vencimento_plano < hoje`, com link `wa.me`.
7. Perfil Gym/Totalpass vs Assinante, por faixa etaria (ate 17, 18–24, 25–34, 35–44, 45+) e genero. Conta quem teve check-in nas 4 Semanas.

Membros PENDENTE ficam fora de tudo.

## Categorias (nome do plano, sem acento, por prefixo)

| Categoria | Planos |
|---|---|
| Gym/Totalpass | Gympass, Totalpass |
| Avulso | Diaria, Diaria Boulder |
| Pacote | Pacote 10, Voucher |
| Sem Receita | Cortesia, Livre, Evento, Airbnb |
| Assinante | Mensal, Mens. c/ Treino, Trimestral, Semestral, Anual, Escolinha* |
| Outros | qualquer outro |

## Limites conhecidos

- **Backfill**: erra check-ins antigos sem pagamento de quem trocou de plano. No banco real foram 15 check-ins de 2 membros, e aceitamos isso.
- **Perdas para Gym/Totalpass anteriores a migracao ficam invisiveis.** O check-in antigo de Assinante nao tem pagamento, entao o backfill atribui a ele o plano atual (Gym/Totalpass). Perdas so passam a ser medidas a partir da migracao. Conversoes antigas sao recuperadas, porque o historico Gym/Totalpass tem pagamento.
- **Horarios anteriores a nov/2025 no banco real sao hora cheia**, vindos da importacao. O mapa de calor usa so as 4 Semanas mais recentes.
- **"Vencidos" usa o vencimento de hoje.** Em Semanas antigas, a lista mostra quem veio naquela Semana e ainda nao renovou.
