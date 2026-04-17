# Arquitetura do Summit System

## Visao Geral

```
run.py (entry point)
  |
  +-- Flask web server (background process)
  |     src/web/app.py
  |     src/web/templates/ (checkin.html, register.html)
  |
  +-- PyQt6 GUI (main thread)
        src/ui/main_window.py (orquestrador central, ~1700 linhas)
        src/ui/screens/ (10 telas)
        src/ui/dialogs/ (13 dialogos)
        src/ui/components/ (sidebar, member_info_formatter)
        src/ui/workers/ (7 workers assincronos)
        src/ui/styles.py (tema visual)
```

---

## Camadas

### 1. UI Layer (`src/ui/`)

#### Main Window (`main_window.py`)
- Orquestra TUDO: navegacao, sinais, workers, dialogos
- ~60 operacoes diferentes
- **Problema conhecido**: God Object — muita logica de negocio embutida aqui
- Sidebar com contextos: HOME, MEMBERS, CHECKIN, FINANCIAL, SETTINGS, REPORTS, NOTES

#### Telas (`src/ui/screens/`)
| Arquivo | Proposito | Linhas |
|---------|-----------|--------|
| `dashboard_screen.py` | Check-ins de hoje, status em tempo real | ~434 |
| `home_screen.py` | Splash/loading durante conexao | ~52 |
| `checkin_screen.py` | Busca + confirma check-in | ~269 |
| `member_search_screen.py` | Busca membro + perfil detalhado (3 tabs) | ~658 |
| `members_list_screen.py` | Lista paginada com filtros | ~674 |
| `pending_members_screen.py` | Aprovacao de cadastros web | ~217 |
| `financial_screen.py` | Dashboard financeiro com periodo | ~389 |
| `plans_screen.py` | CRUD de planos (cards + editor) | ~653 |
| `aniversariantes_screen.py` | Aniversariantes do mes | ~99 |
| `notes_screen.py` | Bloco de notas do staff | ~513 |

#### Dialogos (`src/ui/dialogs/`)
| Arquivo | Proposito |
|---------|-----------|
| `add_member_dialog.py` | Cadastro de novo membro |
| `edit_member_dialog.py` | Edicao de membro existente |
| `delete_member_dialog.py` | Confirmacao de exclusao |
| `member_details_dialog.py` | Perfil read-only |
| `renew_plan_dialog.py` | Renovacao de plano com pagamento |
| `manage_plans_dialog.py` | Gestao de planos (LEGACY, substituido por plans_screen) |
| `payment_method_dialog.py` | Selecao de metodo de pagamento |
| `edit_checkin_dialog.py` | Edicao de data/hora de check-in |
| `report_period_dialog.py` | Selecao de periodo para relatorios |
| `expiring_plans_dialog.py` | Membros com plano vencendo |
| `plan_distribution_dialog.py` | Distribuicao de membros por plano |
| `sync_dialog.py` | Sincronizacao com Google Sheets |
| `finance_graphs.py` | Graficos financeiros (matplotlib) |

#### Workers (`src/ui/workers/`)
- `checkin_worker.py` — Check-in assincrono
- `dashboard_worker.py` — Atualiza dashboard (chamado a cada 5s)
- `data_fetch_worker.py` — Busca aniversariantes
- `member_search_worker.py` — Busca membros
- `financial_worker.py` — Carrega dados financeiros
- `database_connection_worker.py` — Conexao inicial ao banco
- `sync_worker.py` — Sincronizacao com Google Sheets (~388 linhas, mais complexo)

---

### 2. Services Layer (`src/services/`)

Camada de logica de negocio. Todos retornam dataclasses tipadas.

| Servico | Responsabilidade | Modo |
|---------|-----------------|------|
| `MemberService` (~786 linhas) | CRUD membros, busca, paginacao, status | SQLAlchemy + legado |
| `PaymentService` (~448 linhas) | Pagamentos, resumo, breakdown | SQLAlchemy + legado |
| `CheckinService` (~586 linhas) | Check-in, validacao, pagamento automatico | SQLAlchemy only |
| `PlanService` (~187 linhas) | Catalogo de planos, cache | SQLAlchemy only |
| `EmailService` (~105 linhas) | Envio de notas por SMTP | Standalone |

**Padrao dual-mode**: MemberService e PaymentService aceitam tanto `db_session` (SQLAlchemy) quanto `db_manager` (legado) para backward compatibility. Preferir sempre SQLAlchemy.

---

### 3. Core Layer (`src/core/`)

Logica de dominio pura, sem dependencia de banco.

| Arquivo | Conteudo |
|---------|----------|
| `models.py` | Classe `Pessoa` — modelo de dominio com propriedades computadas (idade, aniversario) |
| `plan_status.py` | Constantes ATIVO/INATIVO, funcoes is_active(), display_label() |
| `plan_utils.py` | Normalizacao de nomes de plano para pagamento per-checkin |
| `payment_constants.py` | Constantes de metodo/tipo de pagamento |
| `aniversariantes_manager.py` | Gerenciador de aniversarios |
| `member_search_service.py` | Wrapper de busca (DUPLICADO com MemberService.search_by_name) |

---

### 4. Data Layer (`src/data/`)

| Arquivo | Responsabilidade | Status |
|---------|-----------------|--------|
| `models.py` | Modelos ORM: Membro, Frequencia, Pagamento, Plano, Nota | ATIVO |
| `db.py` | Engine SQLAlchemy, session factory, funcao unaccent() | ATIVO |
| `data_provider.py` | Facade que abstrai SQLite vs Google Sheets | ATIVO |
| `database_manager.py` | CRUD legado via SQL direto | **DEPRECATED** |
| `google_sheets_service.py` | Integracao Google Sheets | **DEPRECATED** |
| `maintenance.py` | Manutencao do banco | Minimo |

---

### 5. Reports Layer (`src/reports/`)

| Arquivo | Gera |
|---------|------|
| `finance_report.py` | HTML financeiro via Jinja2 |
| `members_report.py` | HTML membros via Jinja2 |
| `frequency_report.py` | HTML frequencia via Jinja2 |

Templates em `src/templates/reports/` (base + 3 filhos). Usa Chart.js.
Saida salva em `relatorios/` e aberta no navegador.

---

### 6. Web Layer (`src/web/`)

Flask app com 3 rotas:
- `/` — Menu principal
- `/checkin` — Check-in por nome (busca + selecao + confirmacao)
- `/register` — Cadastro de novo membro (estado_plano = PENDENTE)

Rate limiting: 10/min check-in, 5/hour registro.
Templates em `src/web/templates/`.

---

### 7. Config (`src/config.py`)

Planos, precos, regras. **Sendo migrado para tabela Plano no banco.**
Carrega overrides de `plans_config.json` se existir.

---

## Fluxos Principais

### Check-in (desktop)
```
CheckinScreen.busca_membro()
  -> MemberSearchWorker -> MemberService.search_by_name()
  -> CheckinScreen.display_member_for_checkin()
  -> Usuario clica "Confirmar"
  -> MainWindow._on_confirm_checkin_clicked()
  -> CheckinWorker -> CheckinService.perform_checkin()
     -> valida 1/dia
     -> insere Frequencia
     -> se per-checkin: cria Pagamento automatico
     -> se quota: decrementa voucher_credits
  -> MainWindow._on_checkin_worker_completed()
  -> Dashboard atualiza automaticamente (timer 5s)
```

### Cadastro web (celular)
```
Membro preenche form no celular
  -> POST /register -> Flask valida campos obrigatorios
  -> MemberService.create() com estado_plano='PENDENTE'
  -> Dono ve na PendingMembersScreen
  -> Aprova -> muda estado_plano para 'ATIVO'
```

### Geracao de relatorio
```
Sidebar: Relatorios > Financeiro/Membros/Frequencia
  -> ReportPeriodDialog (usuario escolhe periodo)
  -> generate_*_report(start_date, end_date)
  -> Jinja2 renderiza HTML com Chart.js
  -> Salva em relatorios/*.html
  -> Abre no navegador padrao
```

---

## Divida Tecnica Conhecida

1. **MainWindow como God Object** — deveria delegar mais para services
2. **MemberSearchService duplica MemberService** — consolidar
3. **config.py vs tabela Plano** — duplicacao de dados de planos
4. **DatabaseManager deprecated** — ainda referenciado em alguns lugares
5. **HTML gerado como string** em member_info_formatter.py — deveria usar template
6. **manage_plans_dialog.py** — substituido por plans_screen.py, pode ser removido
7. **Logica de status** — atualmente campo unico `estado_plano`, precisa ser separado em status_plano + status_membro (ver BUSINESS_RULES.md)
