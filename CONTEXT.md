# Summit

Gestao de uma academia de escalada: membros, planos, check-ins, pagamentos e relatorios para o dono.

## Language

### Clientes

**Membro**:
Pessoa cadastrada na academia, com um plano atual.
_Avoid_: Aluno, usuario, cliente (como entidade)

**Categoria de Cliente**:
Agrupamento de negocio dos planos, usado em relatorios: Assinante, Pacote, Avulso, Gym/Totalpass ou Sem Receita. Plano sem categoria aparece como "Outros".
_Avoid_: Tipo de cliente, tipo de plano

**Assinante**:
Membro em plano pago com vencimento (Mensal, Mens. c/ Treino, Trimestral, Semestral, Anual, Escolinha).
_Avoid_: Mensalista

**Pacote**:
Membro em plano de creditos pre-pagos (Pacote 10, Voucher).
_Avoid_: Quota

**Avulso**:
Membro que paga cada visita a preco cheio (Diaria, Diaria Boulder).

**Gym/Totalpass**:
Membro que entra pelo Gympass ou pelo Totalpass; a academia recebe um valor fixo por check-in do parceiro.
_Avoid_: Agregador, parceiro, app

**Sem Receita**:
Membro que treina sem gerar receita no sistema (Cortesia, Livre, Evento, Airbnb).
_Avoid_: Cortesia (como nome do grupo; Cortesia e so um dos planos), gratuito

### Frequencia

**Check-in**:
Registro de uma visita de um Membro; no maximo um por Membro por dia.
_Avoid_: Entrada, presenca, frequencia (como registro individual)

**Tipo do Check-in**:
O plano do Membro no momento do check-in, fixado no registro e nao alterado por trocas de plano posteriores.
_Avoid_: Plano do membro (quando se fala de historico)

**Semana**:
Segunda a sabado; a academia nao abre domingo. Check-ins excepcionais de domingo contam nos totais da Semana que ele encerra.

**Mes**:
Mes calendario fechado (dia 1 ao ultimo dia), usado no Resumo Mensal. A Semana que cruza a virada de mes fica inteira no Resumo Semanal e so e recortada na Evolucao do Resumo Mensal.
_Avoid_: Periodo de 30 dias

### Movimentacao

**Conversao**:
Membro cujo Tipo do Check-in muda de Gym/Totalpass para Assinante ou Pacote.
_Avoid_: Upgrade, migracao

**Perda para Gym/Totalpass**:
Membro cujo Tipo do Check-in muda de Assinante ou Pacote para Gym/Totalpass.
_Avoid_: Downgrade, churn (churn e sair da academia, nao trocar de plano)

**Candidato a Conversao**:
Membro Gym/Totalpass com 8 ou mais check-ins nas ultimas 4 Semanas.

### Receita

**Receita da Semana**:
Soma dos pagamentos recebidos na Semana (regime de caixa).
_Avoid_: Faturamento

**Valor por Visita**:
Quanto a academia ganha, em media, por check-in de uma Categoria de Cliente (regime de competencia: preco do plano rateado pelos dias e dividido pelos check-ins).
_Avoid_: Ticket medio (esse e por pagamento, nao por visita)

### Relatorios

**Resumo Semanal**:
Relatorio de uma tela so com os numeros-chave de uma Semana, comparados com a anterior, e uma lista de acoes.
_Avoid_: Dashboard, painel

**Resumo Mensal**:
Mesmo relatorio do Resumo Semanal com janela de Mes, mais membros novos, renovacoes, evolucao semana a semana e inativos.
_Avoid_: Fechamento do mes

**Relatorio de Detalhe**:
Um dos tres relatorios completos (Financeiro, Membros, Frequencia), usados para aprofundar o que o Resumo Semanal mostra.
