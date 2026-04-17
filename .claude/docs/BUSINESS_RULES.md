# Regras de Negocio — Summit Climbing Gym

## Contexto

A Summit e uma academia de escalada. O dono usa a aplicacao desktop (PyQt6) para gestao diaria. Membros usam o front-end web (Flask) para se cadastrar e fazer check-in pelo celular.

---

## 1. Tipos de Plano

### 1.1 Planos baseados em tempo (com vencimento)

| Plano | Preco Renovacao | Duracao | Renovavel |
|-------|----------------|---------|-----------|
| Mensal | R$ 190 | 30 dias | Sim |
| Mens. c/ Treino | R$ 280 | 30 dias | Sim |
| Trimestral | R$ 500 | 90 dias | Sim |
| Semestral | R$ 950 | 180 dias | Sim |
| Anual | R$ 1.900 | 365 dias | Sim |
| Escolinha 1x | config | 30 dias | Sim |
| Escolinha 2x | config | 30 dias | Sim |

- Tem campo `vencimento_plano` (Date)
- Renovacao gera registro de `Pagamento`
- Preco definido na tabela `Plano` no banco (migrando de `config.py`)

### 1.2 Planos per-checkin (pagamento por uso)

| Plano | Preco por Check-in | Renovavel |
|-------|-------------------|-----------|
| Diaria | R$ 35 | Nao |
| Gympass | R$ 15 | Nao |
| Totalpass | R$ 15 | Nao |

- NAO tem vencimento (sem `vencimento_plano`)
- Cada check-in gera automaticamente um registro de `Pagamento`
- Logica em `CheckinService.ensure_payment_for_checkin()`
- Diaria = membro avulso, mas CONTA como membro nos relatorios

### 1.3 Planos quota (creditos pre-pagos)

| Plano | Exemplo |
|-------|---------|
| Pacote 10 | 10 diarias pre-pagas |

- Campo `is_quota=True` na tabela `Plano`
- `voucher_credits` no Membro = saldo de creditos
- Cada check-in decrementa 1 credito (nao gera Pagamento)
- SEM vencimento (`vencimento_plano = NULL`)
- Creditos acumulam se comprar mais pacotes
- Aviso quando saldo = 0

### 1.4 Planos especiais

| Plano | Comportamento |
|-------|---------------|
| Cortesia | Sem custo, sem vencimento, sem pagamento |

---

## 2. Status do Plano vs Status do Membro

**REGRA FUNDAMENTAL: Sao dois conceitos SEPARADOS.**

### 2.1 Status do Plano (baseado em data de vencimento)

| Status | Condicao |
|--------|----------|
| EM DIA | `vencimento_plano >= hoje` |
| VENCIDO | `vencimento_plano < hoje` |
| SEM VENCIMENTO | Planos quota, per-checkin, ou Cortesia (sem `vencimento_plano`) |
| PENDENTE | Cadastro web nao aprovado pelo dono |

- E o que aparece na **dashboard** e na **lista de membros**
- Troca para VENCIDO automaticamente (sem periodo de graca)
- Check-in AINDA e permitido com plano vencido, mas emite aviso na tela
- NAO existe mais "Periodo de Graca" como conceito persistido

### 2.2 Status do Membro (baseado em frequencia/atividade)

Depende do tipo de plano:

| Tipo de plano | ATIVO se | INATIVO se |
|---------------|----------|------------|
| Mensal, Trimestral, Semestral, Anual, Mens. c/ Treino, Escolinha | Ultimo check-in <= 14 dias atras | Ultimo check-in > 14 dias atras |
| Gympass, Totalpass, Diaria, Cortesia | Ultimo check-in <= 45 dias atras | Ultimo check-in > 45 dias atras |
| Quota (Pacote) | Creditos > 0 E ultimo check-in <= 30 dias | Creditos = 0 OU ultimo check-in > 30 dias |

- **Quando membro inativo faz check-in -> volta a ATIVO automaticamente e imediatamente**
- E usado em **relatorios** e **metricas de negocio**
- NAO e o que aparece na dashboard (la e status do plano)

### 2.3 Onde cada status aparece

| Local | Mostra qual status |
|-------|-------------------|
| Dashboard (check-ins de hoje) | Status do PLANO (em dia / vencido) |
| Lista de membros | Status do PLANO |
| Relatorio de Membros | AMBOS (plano + membro) |
| Relatorio Financeiro | Status do PLANO (para inadimplencia) |
| Relatorio de Frequencia | Status do MEMBRO (para risco de churn) |

---

## 3. Check-in

- **1 check-in por membro por dia** (regra dura, validada no CheckinService)
- Check-in com plano vencido: PERMITIDO, mas aviso visual na tela
- Check-in com plano quota e saldo 0: PERMITIDO, mas aviso visual
- Planos per-checkin: check-in gera `Pagamento` automatico
- Planos quota: check-in decrementa `voucher_credits`
- Planos tempo: check-in nao gera pagamento

---

## 4. Treino

- Servico SEPARADO do plano (nao e um plano)
- Preco: R$ 90/mes
- Validade: 30 dias (campo `vencimento_treino`)
- Vencimento do treino e INDEPENDENTE do vencimento do plano
- Ativacao de treino DEVE gerar registro de `Pagamento` (tipo "Treino")
- Campo `treina` no Membro: "Sim" ou "Nao"
- Deve aparecer como **receita separada** nos relatorios financeiros

---

## 5. Cadastro de Membros

### 5.1 Campos obrigatorios
- Nome, Sobrenome, WhatsApp, Calcado, Plano, Data de Nascimento, Genero

### 5.2 Fluxo web (celular)
1. Membro preenche formulario no celular
2. Sistema salva com `estado_plano = 'PENDENTE'`
3. Dono aprova na tela de "Membros Pendentes" no desktop
4. Membro aprovado muda para ATIVO e pode fazer check-in

### 5.3 Fluxo desktop
1. Dono cadastra membro direto com todos os dados
2. Membro ja fica ativo imediatamente

---

## 6. Pagamentos

### 6.1 Tipos de transacao
- `Renovacao Plano` — renovacao de plano baseado em tempo
- `Diaria` / `Gympass` / `Totalpass` — pagamento por check-in
- `Treino` — ativacao/renovacao de treino
- `Venda Produto` — vendas avulsas

### 6.2 Metodos de pagamento
- PIX, Cartao de Credito, Cartao de Debito, Dinheiro, Transferencia

### 6.3 Registro automatico
- Check-in em plano per-checkin -> Pagamento automatico
- Renovacao de plano -> Pagamento automatico (quando metodo selecionado)
- Ativacao de treino -> DEVERIA gerar Pagamento (verificar se esta implementado)

---

## 7. Relatorios

### 7.1 Publico-alvo
- Dono da academia (unico usuario dos relatorios)
- Precisa de visao clara de: receita, membros ativos, inadimplencia, churn

### 7.2 Regra de filtragem
- Membros com `estado_plano = 'PENDENTE'` NAO aparecem em nenhum relatorio
- Relatorios devem usar os dois conceitos de status (plano e membro)

### 7.3 Tipos de relatorio
- **Financeiro**: Receita, DRE, breakdown por metodo/plano, comparativo, projecao. Treino como receita separada.
- **Membros**: Totais, status plano, status membro, novos, churn, retencao, inadimplencia detalhada
- **Frequencia**: Check-ins, tendencias, membros em risco, distribuicao por dia/plano
