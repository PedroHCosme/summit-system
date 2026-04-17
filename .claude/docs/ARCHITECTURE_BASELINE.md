# Architecture Baseline — Phase 0 Audit

Captured: 2026-04-16. Used to track progress as the stabilization plan removes these dependencies.

---

## 1. `DatabaseManager` imports in runtime paths (`src/`)

| File | Line | Note |
|------|------|------|
| `src/services/checkin_service.py` | 20 | Core service — must migrate to repo |
| `src/services/member_service.py` | 22 | Core service — must migrate to repo |
| `src/services/payment_service.py` | 21 | Core service — must migrate to repo |
| `src/ui/main_window.py` | 1411 | Lazy import inside function |
| `src/ui/workers/sync_worker.py` | 8 | Sync/sheets flow — move to LegacySyncGateway |
| `src/ui/screens/pending_members_screen.py` | 8 | UI screen — must migrate |
| `src/data/migration_tasks/backfill_payments.py` | 10 | Migration script — acceptable, low priority |

**Total: 7 files**

---

## 2. `src.config` (business plan constants) imports in runtime paths

### Business constants — must move to `PlanPolicy` / `planos` table

| Constant | Files importing it |
|----------|-------------------|
| `PLANOS_COM_VENCIMENTO` | `src/services/member_service.py:114,747`, `src/ui/dialogs/add_member_dialog.py:12`, `src/ui/dialogs/edit_member_dialog.py:13`, `src/ui/dialogs/manage_plans_dialog.py:12`, `src/ui/screens/members_list_screen.py:13,474`, `src/ui/screens/member_search_screen.py:12`, `src/ui/components/member_info_formatter.py:10`, `src/ui/workers/sync_worker.py:237` |
| `PLANOS_PRECOS` | `src/data/database_manager.py:157`, `src/services/member_service.py:663`, `src/ui/main_window.py:939` |
| `PLANOS_PAGAMENTO_POR_CHECKIN` | `src/data/database_manager.py:677,691`, `src/data/migration_tasks/backfill_payments.py:9` |
| `PLANOS_NAO_RENOVAVEIS` | `src/ui/screens/members_list_screen.py:474`, `src/ui/screens/member_search_screen.py:307` |

### Infrastructure constants — acceptable in `config.py` long-term

| Constant | Files |
|----------|-------|
| `DB_FILENAME` | `src/data/db.py:21`, `src/data/database_manager.py:59`, `src/ui/main_window.py:1331` |
| `CREDENTIALS_PATH` | `src/ui/workers/database_connection_worker.py:7` |
| `TREINO_VALIDADE_DIAS` | `src/web/app.py:18` |

### Dynamic reloading (anti-pattern — must eliminate)

| File | Lines |
|------|-------|
| `src/ui/dialogs/manage_plans_dialog.py` | 641, 643 — `importlib.reload(config)` |
| `src/ui/screens/plans_screen.py` | 576, 578 — `importlib.reload(config)` |

### Full module import (`from src import config`)

| File | Lines |
|------|-------|
| `src/data/data_provider.py` | 9 |
| `src/data/database_manager.py` | 1431 |
| `src/ui/dialogs/add_member_dialog.py` | 42, 296 |
| `src/ui/dialogs/edit_member_dialog.py` | 50, 361, 501 |
| `src/ui/dialogs/manage_plans_dialog.py` | 641 |
| `src/ui/dialogs/renew_plan_dialog.py` | 56 |
| `src/ui/screens/plans_screen.py` | 576 |

---

## 3. Problem summary

- **2 sources of truth for plan rules**: `src/config.py` (module-level globals) + `planos` table in DB. `manage_plans_dialog.py` can mutate `plans_config.json` and then `importlib.reload(config)` to hot-patch running globals — extremely fragile.
- **No UnitOfWork boundary**: Services instantiate `DatabaseManager` directly, making transaction scope implicit.
- **`DatabaseManager` not isolated**: 3 core services import it at module level; desktop/web/reports call it directly.
- **Test collection risk**: Files in `scripts/` (e.g., `test_checkin_payment.py`, `test_plan_distribution.py`) and root-level `test_*.py` files (6 files) would be picked up by default pytest collection and likely fail due to missing runtime dependencies. Fixed by `pytest.ini`.

---

## 4. Files excluded from pytest collection by pytest.ini

Root-level test-like files (not proper tests):
- `test_duplicate_payment.py`
- `test_reports_jinja.py`
- `verify_approval.py`, `verify_escolhinha.py`, `verify_profession.py`, `verify_renewal.py`

Script-level test-like files in `scripts/`:
- `test_checkin_payment.py`, `test_financial_charts.py`, `test_financial_integration.py`
- `test_payment_system.py`, `test_plan_distribution.py`

Non-test files inside `tests/` that would have been collected:
- `tests/validate_improvements.py`
- `tests/verify_search_accent.py`
