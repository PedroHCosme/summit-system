# Dicionario de Dados — Summit System

## Banco de Dados

SQLite local: `gym_database.db`
ORM: SQLAlchemy (modelos em `src/data/models.py`)

---

## Tabela: `membros`

| Campo | Tipo | Nullable | Descricao |
|-------|------|----------|-----------|
| id | INTEGER PK | Nao | ID autoincrement |
| nome | VARCHAR(255) | Nao | Nome completo (nome + sobrenome concatenados) |
| plano | VARCHAR(100) | Sim | Nome do plano atual (FK logica para tabela planos.nome) |
| vencimento_plano | DATE | Sim | Data de vencimento do plano. NULL para planos quota/per-checkin/cortesia |
| estado_plano | VARCHAR(20) | Sim | Status atual: ATIVO, INATIVO, PENDENTE. **ATENCAO: hoje mistura status de plano e membro — precisa ser separado** |
| data_nascimento | DATE | Sim | Data de nascimento |
| data_cadastro | DATE | Sim | Data de cadastro no sistema |
| whatsapp | VARCHAR(30) | Sim | Telefone WhatsApp (obrigatorio no cadastro mas nullable no banco) |
| genero | VARCHAR(20) | Sim | Masculino, Feminino, Outro |
| email | VARCHAR(255) | Sim | Email do membro |
| apelido | VARCHAR(100) | Sim | Como gosta de ser chamado |
| profissao | VARCHAR(100) | Sim | Profissao |
| contato_emergencia | VARCHAR(255) | Sim | Nome e telefone de emergencia |
| frequencia | TEXT | Sim | Campo legado (texto livre), nao mais usado ativamente |
| observacoes | TEXT | Sim | Notas livres sobre o membro |
| calcado | VARCHAR(10) | Sim | Numero do calcado (obrigatorio no cadastro mas nullable no banco) |
| voucher_credits | INTEGER | Nao | Saldo de creditos para planos quota. Default 0 |
| treina | VARCHAR(10) | Sim | "Sim" ou "Nao" — se contratou servico de treino |
| vencimento_treino | DATE | Sim | Vencimento do servico de treino (independente do plano) |
| created_at | DATETIME | Sim | Timestamp de criacao |
| updated_at | DATETIME | Sim | Timestamp de ultima atualizacao |

**Relacionamentos**:
- `checkins` -> Frequencia (1-N, cascade delete)
- `pagamentos` -> Pagamento (1-N, cascade delete)

---

## Tabela: `frequencia`

| Campo | Tipo | Nullable | Descricao |
|-------|------|----------|-----------|
| id | INTEGER PK | Nao | ID autoincrement |
| member_id | INTEGER FK | Nao | FK para membros.id (ON DELETE CASCADE) |
| checkin_datetime | DATETIME | Nao | Data e hora do check-in |
| created_at | DATETIME | Sim | Timestamp de criacao do registro |

**Regra de negocio**: Maximo 1 registro por member_id por dia (validado no CheckinService, nao no banco).

---

## Tabela: `pagamentos`

| Campo | Tipo | Nullable | Descricao |
|-------|------|----------|-----------|
| id | INTEGER PK | Nao | ID autoincrement |
| member_id | INTEGER FK | Sim | FK para membros.id (ON DELETE SET NULL). Nullable para vendas sem membro |
| data_pagamento | DATETIME | Sim | Data e hora do pagamento |
| tipo_transacao | VARCHAR(100) | Nao | Tipo: "Renovacao Plano", "Diaria", "Gympass", "Totalpass", "Treino", "Venda Produto" |
| descricao | TEXT | Sim | Descricao detalhada |
| valor | FLOAT | Nao | Valor em reais |
| metodo_pagamento | VARCHAR(50) | Sim | PIX, Cartao de Credito, Cartao de Debito, Dinheiro, Transferencia |
| nova_data_vencimento | DATE | Sim | Novo vencimento apos renovacao (quando aplicavel) |
| created_at | DATETIME | Sim | Timestamp de criacao |

**Observacao**: Nao existe campo de status (PAGO/CANCELADO/REEMBOLSO). Hoje tudo e assumido como PAGO.

---

## Tabela: `planos`

| Campo | Tipo | Nullable | Descricao |
|-------|------|----------|-----------|
| id | INTEGER PK | Nao | ID autoincrement |
| nome | VARCHAR(100) UNIQUE | Nao | Nome do plano |
| preco | FLOAT | Nao | Preco de renovacao. Default 0 |
| valor_por_checkin | FLOAT | Nao | Preco por check-in. Default 0. > 0 para Diaria, Gympass, Totalpass |
| requer_vencimento | BOOLEAN | Nao | Se o plano exige data de vencimento |
| ativo | BOOLEAN | Nao | Se o plano esta disponivel para selecao |
| is_quota | BOOLEAN | Nao | Se e plano baseado em creditos (Pacote 10 etc) |
| quota_amount | INTEGER | Nao | Quantidade de creditos por compra |
| created_at | DATETIME | Sim | Timestamp |
| updated_at | DATETIME | Sim | Timestamp |

**Duplicacao**: Mesmos dados existem em `config.py` (PLANOS_PRECOS, PLANOS_COM_VENCIMENTO etc). A tabela Plano e a fonte de verdade preferida — config.py esta sendo descontinuado.

---

## Tabela: `notas`

| Campo | Tipo | Nullable | Descricao |
|-------|------|----------|-----------|
| id | INTEGER PK | Nao | ID autoincrement |
| titulo | VARCHAR(255) | Nao | Titulo da nota. Default "Nova Nota" |
| conteudo | TEXT | Sim | Conteudo da nota |
| tipo | VARCHAR(20) | Nao | "bug", "ideia", "outro" |
| enviada | BOOLEAN | Nao | Se foi enviada por email ao dev |
| created_at | DATETIME | Sim | Timestamp |
| updated_at | DATETIME | Sim | Timestamp |

---

## Campos Computados (nao persistidos)

| Campo | Calculado de | Logica |
|-------|-------------|--------|
| status_plano | vencimento_plano vs hoje | EM DIA se >= hoje, VENCIDO se < hoje |
| status_membro | ultimo check-in vs threshold por plano | Ver BUSINESS_RULES.md secao 2.2 |
| dias_restantes | vencimento_plano - hoje | Positivo = dias restantes, negativo = dias vencido |
| idade | data_nascimento vs hoje | Anos completos |
| frequencia_mensal | COUNT checkins ultimos 30 dias | Por membro |

---

## Valores de Referencia

### estado_plano (valores atuais no banco)
- `"ATIVO"` — Plano ativo/membro aprovado
- `"INATIVO"` — Plano vencido ou membro desativado
- `"PENDENTE"` — Cadastro web nao aprovado

### tipo_transacao (valores comuns)
- `"Renovacao Plano"` — Renovacao de plano baseado em tempo
- `"Diaria"` — Pagamento por check-in de diaria
- `"Gympass"` — Pagamento por check-in Gympass
- `"Totalpass"` — Pagamento por check-in Totalpass
- `"Treino"` — Pagamento de treino
- `"Venda Produto"` — Venda avulsa

### metodo_pagamento (valores comuns)
- `"PIX"`, `"Cartao de Credito"`, `"Cartao de Debito"`, `"Dinheiro"`, `"Transferencia"`
