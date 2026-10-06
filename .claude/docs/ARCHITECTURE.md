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
        src/ui/main_window.py (orquestrador central, ~500 linhas, shell fino)
        src/ui/main_window_ui.py (build_ui — construção da UI extraída)
        src/ui/screens/ (10 telas)
        src/ui/dialogs/ (12 dialogos)
        src/ui/components/ (sidebar, member_info_formatter)
        src/ui/workers/ (7 workers assincronos)
        src/ui/styles.py (tema visual)
```

---

## Camadas

### 1. UI Layer (`src/ui/`)

#### Main Window (`main_window.py`)
- Orquestra navegacao, sinais, workers, dialogos
- ~500 linhas (refatorado de ~965)
- **Resolvido (2026-08-17)**: era um God Object; a logica foi movida para os 4 coordinators e a construção de UI para main_window_ui.py. Hoje só orquestra navegação, conexão, migrações e o timer do dashboard.
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
| `MemberService` (~700 linhas) | CRUD membros, busca, paginacao, status | SQLAlchemy only |
| `PaymentService` (~360 linhas) | Pagamentos, resumo, breakdown | SQLAlchemy only |
| `CheckinService` (~586 linhas) | Check-in, validacao, pagamento automatico | SQLAlchemy only |
| `PlanService` (~187 linhas) | Catalogo de planos, cache | SQLAlchemy only |
| `EmailService` (~105 linhas) | Envio de notas por SMTP | Standalone |

Todos os services agora exigem `db_session` (SQLAlchemy) no construtor. O antigo modo dual (`db_session` OU `db_manager` legado) foi removido em 2026-08-15 — ver "Limpeza ponytail-audit" abaixo.

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

---

### 4. Data Layer (`src/data/`)

| Arquivo | Responsabilidade | Status |
|---------|-----------------|--------|
| `models.py` | Modelos ORM: Membro, Frequencia, Pagamento, Plano, Nota | ATIVO |
| `db.py` | Engine SQLAlchemy, session factory, funcao unaccent() | ATIVO |
| `data_provider.py` | Facade que abstrai SQLite vs Google Sheets | ATIVO |
| `maintenance.py` | Manutencao do banco (indices, ANALYZE/PRAGMA optimize, create_tables legado usado pelo sync) | ATIVO |
| `legacy_sync_gateway.py` | Adaptador legado para sincronizacao Google Sheets + infra local | ATIVO |
| `google_sheets_service.py` | Integracao Google Sheets | **DEPRECATED** (mas ainda usado pelo Sync, ver `sync_dialog.py`) |

`database_manager.py` (CRUD legado via SQL direto) foi removido em 2026-08-15 — ver "Limpeza ponytail-audit" abaixo. Todo acesso a dados agora passa por `data_provider.py` / services (SQLAlchemy) ou `maintenance.py` (operacoes de manutencao pontuais via conexao sqlite3 propria).

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

1. ~~**MainWindow como God Object**~~ — **RESOLVIDO em 2026-08-17** (ver bloco abaixo).
2. **config.py vs tabela Plano** — config.py e `plans_config.json` continuam em uso, mas apenas como fonte de "valores padrao" para o botao Restaurar Padroes em `plans_screen.py`; a tabela `Plano` (via `PlanService`) e a unica fonte viva de precos. Nao e duplicacao de escrita, so vale desconfiar se algo voltar a ler `config.PLANOS_PRECOS` fora desse fluxo.
3. **HTML gerado como string** em member_info_formatter.py — deveria usar template
4. **Logica de status** — atualmente campo unico `estado_plano`, precisa ser separado em status_plano + status_membro (ver BUSINESS_RULES.md)

### Resolvido em 2026-08-15 — Limpeza ponytail-audit

Um audit de over-engineering (`/ponytail:ponytail-audit`) + plano de implementacao removeu 5 achados confirmados (ver `docs/superpowers/plans/2026-08-15-ponytail-audit-cleanup.md` e o spec correspondente para o historico completo, incluindo duas correcoes descobertas durante a implementacao):

- `database_manager.py` (1884 linhas, CRUD legado) — **deletado**. Os 3 chamadores reais (`settings_coordinator.py`, `pending_members_screen.py`, e `legacy_sync_gateway.py` — este ultimo so descoberto durante a implementacao, nao pelo audit original) foram migrados para `MemberService`/`src/data/maintenance.py` antes da remocao.
- `manage_plans_dialog.py` (747 linhas) — **deletado**. Nunca era instanciado (o metodo `_show_manage_plans_dialog` em `main_window.py`, apesar do nome, sempre navegava para `plans_screen.py`).
- `db_manager=` (fallback legado no construtor) — **removido** de `MemberService` e `PaymentService`. Ambos agora exigem `db_session` (SQLAlchemy).
- `member_search_service.py` — **deletado** (wrapper delegate puro para `DataProvider`). Os 8 chamadores reais (em `checkin_coordinator.py`/`members_coordinator.py`, nao em `main_window.py` como o audit original assumiu) agora usam `self.window.manager.data_provider.get_member_by_id(...)` diretamente.
- Helpers `_get_reports_dir`/`_get_template_env` duplicados nos 3 geradores de relatorio — **extraidos** para `src/reports/_common.py`.
- 17 scripts standalone e 2 docs orfaos que so importavam o `DatabaseManager` deletado — **deletados** em 2026-08-17 (ver `docs/superpowers/plans/2026-08-17-post-audit-dead-file-cleanup.md`), incluindo `docs/MANAGE_PLANS_DIALOG.md` e `docs/MIGRATION_GUIDE.md`.

Achados descartados durante o brainstorming (nao eram over-engineering de verdade): a sync com Google Sheets (`sync_dialog.py`/`sync_worker.py`/`legacy_sync_gateway.py`) e uma feature viva, nao codigo morto; e `config.py`/`plans_config.json` nao sao um terceiro armazenamento concorrente, so a fonte de "valores padrao" (ver item 2 acima).

### Resolvido em 2026-08-17 — Decomposicao do God Object (MainWindow)

`main_window.py` foi de ~965 para ~499 linhas seguindo o plano em `docs/superpowers/plans/2026-08-17-mainwindow-god-object-decomposition.md` (spec correspondente em `docs/superpowers/specs/`):

- **~47 shims de delegacao deletados** — os sinais das telas/sidebar agora conectam direto aos 4 coordinators (nada de metodos de repasse de 1 linha na janela).
- **Fluxo financeiro** movido para `ReportsCoordinator`; **fluxo de aniversariantes** movido para `MembersCoordinator`.
- **Construcao da UI** (`_setup_ui`) extraida para `src/ui/main_window_ui.py` como `build_ui(window)`; `_setup_ui` virou um delegate de 3 linhas.
- **Rede de seguranca**: `tests/test_main_window_smoke.py` (constroi a MainWindow headless, verifica coordinators + handlers). Suite: 106 passed.
- Nao foi criada nenhuma abstracao nova — tudo caiu nos 4 coordinators que ja existiam. O acoplamento coordinator<->window (coordinators acessam `window.screen.widget`) foi deixado como esta, deliberadamente (fora de escopo).
