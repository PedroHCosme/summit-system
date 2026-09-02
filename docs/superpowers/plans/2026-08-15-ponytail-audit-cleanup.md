# Ponytail Audit Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove five confirmed over-engineering findings from the Summit System audit — a dead legacy DB-access class, a fully unwired duplicate UI, dead constructor flexibility on two services, a delegate-only wrapper class, and duplicated report boilerplate — without changing any user-visible behavior.

**Architecture:** No new abstractions. Each phase either deletes dead code after confirming zero live callers, or swaps a caller from a legacy path to its already-existing service-layer equivalent. Phases are ordered so each one only depends on the previous being merged.

**Tech Stack:** Python, PyQt6, SQLAlchemy, SQLite, Flask, Jinja2. Windows dev machine (PowerShell primary, git-bash available).

**Correction (found when setting up the implementation worktree, not present when the spec was written):** the codebase has a real automated test suite — `tests/` (97 tests, collected via `pytest.ini`'s `testpaths = tests`) plus `test_reports_jinja.py` at the repo root (not `src/test_reports_jinja.py` — that path was wrong). None of it imports or couples to any of the five things this plan deletes (`DatabaseManager`, `ManagePlansDialog`, the `db_manager=` params, `MemberSearchService`, or the per-file report helpers) — confirmed by grep. Two files import `DatabaseManager` (`test_duplicate_payment.py` and `tests/validate_improvements.py`) but neither matches pytest's `test_*.py` discovery pattern from the repo root config, aren't collected by `pytest` today, and are already stale/broken scripts unrelated to this plan (`test_duplicate_payment.py` fails at collection today, before any of this plan's changes, on a missing table) — leave both alone, same as `migrate_data.py` in the "out of scope" list.

**Baseline (verified in the worktree before Phase 1 starts):**
```bash
python -m pytest test_reports_jinja.py tests/ -q
```
Expected: `97 passed` in ~2.5s. Every phase below adds "run this full suite" as a fast automated gate *in addition to* its manual smoke test — this is real TDD safety net, not just the grep-based dead-reference checks the plan already specifies. Run it before starting each task (confirm the baseline still holds) and after each task's changes (confirm nothing broke) — not just at the one Phase 5 checkpoint that originally cited it.

Relevant pre-existing coverage per phase (run the full suite regardless, but these are where a regression would surface first): Phase 1 → `tests/test_member_management.py` (`MemberService` CRUD); Phase 3 → `tests/test_member_management.py`, `tests/test_financial.py` (`PaymentService`), `tests/test_plan_status.py`; Phase 4 → `tests/test_member_search.py`; Phase 5 → `test_reports_jinja.py`, `tests/test_reports_overhaul.py`.

**Spec:** `docs/superpowers/specs/2026-08-15-ponytail-audit-cleanup-design.md`

**Second correction (found during Task 1.4's own verification step, working exactly as designed):** the original usage map for `database_manager.py` missed a third live caller, `src/data/legacy_sync_gateway.py` (used by the live Google Sheets Sync feature — `SyncDialog` → `SyncWorker` → `SyncImportService` → `LegacySyncGateway`), which calls `DatabaseManager.connect()`/`.create_tables()`/`.optimize_and_reindex()`. A new Task 1.3b (inserted below, before Task 1.4) migrates it the same way Tasks 1.2/1.3 migrated the other two callers. This is exactly why Task 1.4's Step 1 grep-and-classify exists as a hard gate rather than trusting the plan's static map — it caught a real gap before any deletion happened.

---

## Phase 1: Retire `src/data/database_manager.py`

`database_manager.py` (1884 lines, docstring-marked `.. deprecated ::`) has two live tenants: CRUD in `pending_members_screen.py` (fully covered by `MemberService`) and `optimize_and_reindex()` in `settings_coordinator.py` (real DB-maintenance logic, no service equivalent — belongs in the empty `src/data/maintenance.py`). Both must move before the file can be deleted.

### Task 1.1: Move `optimize_and_reindex` into `src/data/maintenance.py`

**Files:**
- Modify: `src/data/maintenance.py` (currently empty)
- Read reference: `src/data/database_manager.py:1725-1780` (method being moved), `src/data/database_manager.py:56-70` (path resolution being mirrored)

- [ ] **Step 1: Write the new standalone function**

`src/data/maintenance.py` is currently a zero-byte file. Replace its contents with:

```python
"""Manutenção do banco de dados SQLite (índices, VACUUM, ANALYZE)."""

import os
import sqlite3
from typing import Any, Dict


def optimize_and_reindex(db_path: str) -> Dict[str, Any]:
    """Cria índices principais e executa ANALYZE/PRAGMA optimize no banco em db_path."""
    connection = sqlite3.connect(db_path, check_same_thread=False, timeout=60)
    stats = {
        "indices_processed": 0,
        "vacuum_executed": False,
        "analyze_executed": False,
        "pragma_optimize_executed": False,
    }

    try:
        cursor = connection.cursor()
        index_statements = [
            "CREATE INDEX IF NOT EXISTS idx_membros_nome ON membros(nome)",
            "CREATE INDEX IF NOT EXISTS idx_membros_plano ON membros(plano)",
            "CREATE INDEX IF NOT EXISTS idx_membros_estado_plano ON membros(estado_plano)",
            "CREATE INDEX IF NOT EXISTS idx_membros_vencimento ON membros(vencimento_plano)",
            "CREATE INDEX IF NOT EXISTS idx_frequencia_member_id ON frequencia(member_id)",
            "CREATE INDEX IF NOT EXISTS idx_frequencia_datetime ON frequencia(checkin_datetime)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_frequencia_unique ON frequencia(member_id, DATE(checkin_datetime))",
            "CREATE INDEX IF NOT EXISTS idx_pagamentos_member_id ON pagamentos(member_id)",
            "CREATE INDEX IF NOT EXISTS idx_pagamentos_data ON pagamentos(data_pagamento)",
            "CREATE INDEX IF NOT EXISTS idx_pagamentos_tipo ON pagamentos(tipo_transacao)",
        ]
        for statement in index_statements:
            cursor.execute(statement)
            stats["indices_processed"] += 1
        cursor.close()

        # Garante que ANALYZE rode fora de uma transação ativa
        connection.commit()

        # VACUUM omitido: causa erro "database is locked" se houver outras conexões ativas (ex: UI)
        try:
            connection.execute("ANALYZE")
            stats["analyze_executed"] = True
        except sqlite3.Error as exc:
            print(f"Aviso: ANALYZE falhou: {exc}")

        try:
            connection.execute("PRAGMA optimize")
            stats["pragma_optimize_executed"] = True
        except sqlite3.Error as exc:
            print(f"Aviso: PRAGMA optimize falhou: {exc}")

        connection.commit()
        return stats
    finally:
        connection.close()
```

This is a straight port of `DatabaseManager.optimize_and_reindex()` (`database_manager.py:1725-1780`) with the instance-state connection replaced by a locally-owned one, and `db_path` resolution left to the caller (matching how `settings_coordinator.create_database_backup()` already resolves the DB path itself rather than going through `DatabaseManager`).

- [ ] **Step 2: Verify the module imports cleanly**

Run:
```bash
/c/Users/Usuario/.conda/envs/alcoa/python.exe -c "from src.data.maintenance import optimize_and_reindex; print('ok')"
```
Expected: `ok` (run from the repo root so `src` is importable; if it isn't on `PYTHONPATH`, run via `run.py`'s working directory or `python -m src.data.maintenance` equivalent — whatever the project's existing convention is for ad-hoc import checks).

- [ ] **Step 3: Commit**

```bash
git add src/data/maintenance.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Add optimize_and_reindex to maintenance.py"
```

### Task 1.2: Point `settings_coordinator.optimize_database()` at the new function

**Files:**
- Modify: `src/ui/coordinators/settings_coordinator.py:86-126` (`optimize_database` method)

- [ ] **Step 1: Replace the `DatabaseManager` call**

Current code (`settings_coordinator.py:101-108`):
```python
        try:
            from src.data.database_manager import DatabaseManager

            db = DatabaseManager()
            stats = db.optimize_and_reindex()
            db.close()

            indices_checked = stats.get("indices_processed", 0)
```

Replace with:
```python
        try:
            from src.config import DB_FILENAME
            from src.data.maintenance import optimize_and_reindex

            project_root = Path(__file__).parent.parent.parent.parent
            db_path = os.path.join(project_root, DB_FILENAME)
            stats = optimize_and_reindex(db_path)

            indices_checked = stats.get("indices_processed", 0)
```

This mirrors the exact path-resolution pattern already used a few lines above in `create_database_backup()` (`settings_coordinator.py:60-63`), so no new pattern is introduced. `os` and `Path` are already imported at the top of this file (`settings_coordinator.py:5,10`).

- [ ] **Step 2: Manual smoke test**

Run the app, go to Settings → "Otimizar Banco de Dados", confirm the dialog. Verify the success message still shows indices/ANALYZE/PRAGMA status as before.

- [ ] **Step 3: Commit**

```bash
git add src/ui/coordinators/settings_coordinator.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Route DB optimize through maintenance.py instead of DatabaseManager"
```

### Task 1.3: Migrate `pending_members_screen.py` to `MemberService`

**Files:**
- Modify: `src/ui/screens/pending_members_screen.py` (whole file — small, ~223 lines)

`MemberService` already has verified 1:1 equivalents for the three `DatabaseManager` calls this screen makes:
- `db_manager.get_members_paginated(page=1, page_size=100, filter_status="PENDENTE")` → `MemberService.get_paginated(page=1, page_size=100, filter_status="PENDENTE")` (`member_service.py:232-273`)
- `db_manager.update_member(id, plano=..., estado_plano='ATIVO')` → `MemberService.update(id, plano=..., estado_plano='ATIVO')` (`member_service.py:276-289`)
- `db_manager.delete_member(id)` → `MemberService.delete(id)` (`member_service.py:329-347`)

`MemberService` needs a SQLAlchemy session; the codebase's existing pattern for owning a screen-local session is `create_session()` from `src.data.db` (already used by `frequency_report.py`/`members_report.py`).

- [ ] **Step 1: Swap the import and constructor**

Current (`pending_members_screen.py:8,19-21`):
```python
from src.data.database_manager import DatabaseManager
from src.services.plan_service import PlanService
...
        self.db_manager = DatabaseManager()
        self.db_manager.connect()
        self.plan_service = PlanService()  # Creates its own session
```

Replace with:
```python
from src.data.db import create_session
from src.services.member_service import MemberService
from src.services.plan_service import PlanService
...
        self._session = create_session()
        self.member_service = MemberService(db_session=self._session)
        self.plan_service = PlanService()  # Creates its own session
```

- [ ] **Step 2: Swap `refresh_list()`'s data call**

Current (`pending_members_screen.py:100`):
```python
        result = self.db_manager.get_members_paginated(page=1, page_size=100, filter_status="PENDENTE")
        members = result.get('members', [])
```

Replace with:
```python
        result = self.member_service.get_paginated(page=1, page_size=100, filter_status="PENDENTE")
        members = result.members
```

(`MemberService.get_paginated` returns a `PaginatedResult` dataclass, not a dict — `.members` is the attribute, per `member_service.py:37-43`.)

- [ ] **Step 3: Swap `_on_approve_clicked()`'s update call**

Current (`pending_members_screen.py:173-177`):
```python
            success = self.db_manager.update_member(
                self.current_member_data['id'],
                plano=selected_plan,
                estado_plano='ATIVO'
            )
            
            if success:
```

Replace with:
```python
            result = self.member_service.update(
                self.current_member_data['id'],
                plano=selected_plan,
                estado_plano='ATIVO'
            )

            if result.success:
```

- [ ] **Step 4: Swap `_on_reject_clicked()`'s delete call**

Current (`pending_members_screen.py:215`):
```python
            success = self.db_manager.delete_member(self.current_member_data['id'])
            
            if success:
```

Replace with:
```python
            result = self.member_service.delete(self.current_member_data['id'])

            if result.success:
```

- [ ] **Step 5: Verify no `db_manager` references remain in the file**

```bash
grep -n "db_manager" src/ui/screens/pending_members_screen.py
```
Expected: no output.

- [ ] **Step 6: Manual smoke test**

Run the app. Register a test member via the web `/register` route (or use an existing PENDENTE member if present in a dev DB copy). Open Membros Pendentes: confirm the list loads, approve one member with a plan selected (confirm it flips to ATIVO and disappears from the pending list), reject another with a reason (confirm it's deleted and disappears). Use a copy of the DB, not the production file, per the spec's safety-net notes.

- [ ] **Step 7: Commit**

```bash
git add src/ui/screens/pending_members_screen.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Migrate pending_members_screen.py from DatabaseManager to MemberService"
```

### Task 1.3b: Migrate `legacy_sync_gateway.py` off `DatabaseManager`

**Discovered during implementation** (not in the original plan): `Task 1.4`'s "confirm zero remaining live-app importers" step surfaced a third live caller the original usage map missed. `src/data/legacy_sync_gateway.py`'s `LegacySyncGateway` — used by the live Google Sheets Sync feature (`SyncDialog` → `SyncWorker` → `SyncImportService` → `LegacySyncGateway`, all unconditional module-level imports, no `TYPE_CHECKING` guard) — calls `DatabaseManager.connect()`, `.create_tables()`, and `.optimize_and_reindex()` from `connect_database()`, `ensure_database_schema()`, and `optimize_database()` respectively, all three actually invoked by `SyncImportService.execute()` (`sync_import_service.py:71,75,83`). This must be migrated before `database_manager.py` can be deleted. The Sync feature itself remains untouched/out-of-scope per the spec — only its incidental dependency on the class being deleted is being removed, exactly the same kind of swap as Tasks 1.2/1.3.

**Files:**
- Modify: `src/data/maintenance.py` (add one function)
- Modify: `src/data/legacy_sync_gateway.py` (whole file — small, 64 lines)

Step 1: Add `create_tables` to `maintenance.py`, alongside `optimize_and_reindex`, using the same "open its own connection, do the work, close" pattern — a straight port of `DatabaseManager.create_tables()` (`database_manager.py:334-397`):

```python
def create_tables(db_path: str) -> bool:
    """Cria as tabelas do banco de dados se não existirem."""
    connection = sqlite3.connect(db_path, check_same_thread=False, timeout=60)
    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS membros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                plano TEXT,
                vencimento_plano DATE,
                estado_plano TEXT,
                data_nascimento DATE,
                whatsapp TEXT,
                genero TEXT,
                frequencia TEXT,
                calcado TEXT,
                email TEXT,
                apelido TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS frequencia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                checkin_datetime TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES membros (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER,
                data_pagamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tipo_transacao TEXT NOT NULL,
                descricao TEXT,
                valor REAL NOT NULL,
                metodo_pagamento TEXT,
                nova_data_vencimento DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES membros (id)
            )
        """)

        connection.commit()
        cursor.close()
        return True
    except sqlite3.Error as exc:
        print(f"Erro ao criar tabelas: {exc}")
        return False
    finally:
        connection.close()
```

Note: this is a byte-faithful port including its already-stale schema (missing `voucher_credits`, `treina`, `vencimento_treino`, etc. that the real SQLAlchemy `Membro` model has) — **do not "fix" or modernize the schema here**, that's a separate, out-of-scope concern (the real schema is already managed by SQLAlchemy models/Alembic; this `CREATE TABLE IF NOT EXISTS` call is a no-op safety net against a totally empty DB file and has always been this stale — preserving exact existing behavior is the goal, not improving it).

Step 2: Rewrite `legacy_sync_gateway.py` to resolve its own `db_path` and drop the `DatabaseManager` dependency entirely.

Current:
```python
from src.data.database_manager import DatabaseManager
from src.data.google_sheets_service import GoogleSheetsService


class LegacySyncGateway:
    def __init__(self, credentials_path: str, spreadsheet_id: str) -> None:
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.sheets_service: Optional[GoogleSheetsService] = None
        self.db_manager: Optional[DatabaseManager] = None

    def connect_google_sheets(self) -> bool:
        self.sheets_service = GoogleSheetsService(self.credentials_path)
        return self.sheets_service.authenticate()

    def connect_database(self) -> bool:
        self.db_manager = DatabaseManager()
        return self.db_manager.connect()

    def ensure_database_schema(self) -> bool:
        if not self.db_manager:
            return False
        return self.db_manager.create_tables()

    def optimize_database(self) -> Dict[str, Any]:
        if not self.db_manager:
            raise RuntimeError("DatabaseManager não inicializado")
        return self.db_manager.optimize_and_reindex()

    def read_sheet(self, sheet_name: str, range_name: str = "A:CZ") -> List[list]:
        if not self.sheets_service:
            raise RuntimeError("GoogleSheetsService não inicializado")
        return self.sheets_service.read_spreadsheet(
            self.spreadsheet_id, range_name, sheet_name
        )

    def close(self) -> None:
        if self.db_manager:
            self.db_manager.close()
            self.db_manager = None
```

Replace with:
```python
import os
import sqlite3
from pathlib import Path

from src.data.google_sheets_service import GoogleSheetsService
from src.data.maintenance import create_tables, optimize_and_reindex


class LegacySyncGateway:
    def __init__(self, credentials_path: str, spreadsheet_id: str) -> None:
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.sheets_service: Optional[GoogleSheetsService] = None
        self._db_path: Optional[str] = None

    def connect_google_sheets(self) -> bool:
        self.sheets_service = GoogleSheetsService(self.credentials_path)
        return self.sheets_service.authenticate()

    def connect_database(self) -> bool:
        from src.config import DB_FILENAME

        project_root = Path(__file__).parent.parent.parent
        db_path = os.path.join(project_root, DB_FILENAME)
        try:
            sqlite3.connect(db_path, check_same_thread=False, timeout=60).close()
        except sqlite3.Error:
            return False
        self._db_path = db_path
        return True

    def ensure_database_schema(self) -> bool:
        if not self._db_path:
            return False
        return create_tables(self._db_path)

    def optimize_database(self) -> Dict[str, Any]:
        if not self._db_path:
            raise RuntimeError("Banco de dados não conectado")
        return optimize_and_reindex(self._db_path)

    def read_sheet(self, sheet_name: str, range_name: str = "A:CZ") -> List[list]:
        if not self.sheets_service:
            raise RuntimeError("GoogleSheetsService não inicializado")
        return self.sheets_service.read_spreadsheet(
            self.spreadsheet_id, range_name, sheet_name
        )

    def close(self) -> None:
        self._db_path = None
```

Keep the existing `from __future__ import annotations` and `from typing import Any, Dict, List, Optional` lines at the top of the file (only the `DatabaseManager` import line and the body of the four affected methods change — `read_sheet` and the module docstring are untouched). `connect_database()`'s new body preserves the original's success/failure semantics: it actually attempts a real connection and returns `False` on failure, same as `DatabaseManager.connect()` did, just without holding the connection open afterward (each `maintenance.py` call opens and closes its own connection anyway, so there is nothing to keep open between steps — this is a behaviorally-equivalent simplification of an already connection-per-call-op design, not a new design).

Step 3: Verify no `DatabaseManager` references remain.
```bash
grep -n "DatabaseManager" src/data/legacy_sync_gateway.py
```
Expected: no output.

Step 4: Manual smoke test — a live Google Sheets sync isn't runnable in an automated check (needs real credentials); confirm instead via the automated substitute in the task dispatch (import-collect check + full suite), and note that the actual Sync button should be manually exercised once by the user before this branch is considered fully verified end-to-end, same as any other manual-only smoke test in this plan.

Step 5: Commit.
```bash
git add src/data/maintenance.py src/data/legacy_sync_gateway.py
git commit -m "Migrate legacy_sync_gateway.py off DatabaseManager"
```

---

### Task 1.4: Delete `database_manager.py`

**Files:**
- Delete: `src/data/database_manager.py`

- [ ] **Step 1: Confirm zero remaining live-app importers**

```bash
grep -rn "database_manager\|DatabaseManager" src/ --include=*.py | grep -v "src/data/database_manager.py"
```

Expected: only references in one-off/offline scripts outside the running app (`src/migrate_data.py`, `src/data/migration_tasks/backfill_payments.py`, `test_duplicate_payment.py`, `tests/validate_improvements.py` — none of the last two are collected by pytest per `pytest.ini`'s `testpaths = tests` and `test_*.py` pattern), plus a stray `database_manager` *parameter name* in `src/ui/dialogs/expiring_plans_dialog.py` that doesn't actually import the class — none in `src/ui/` importing the real class, `src/services/` (beyond the `TYPE_CHECKING`-only import handled in Phase 3), `src/data/data_provider.py`, `src/data/legacy_sync_gateway.py` (migrated in Task 1.3b — confirm this file no longer appears in the grep output at all, not even as an expected hit), or `src/web/`. If anything unexpected shows up in a live-app path, stop and investigate before deleting — it means this plan's usage map missed a caller (this is exactly how Task 1.3b's need was originally discovered).

- [ ] **Step 2: Delete the file**

```bash
git rm src/data/database_manager.py
```

- [ ] **Step 3: Confirm the app still boots**

Run the app's normal launch command (per the project's `run.py`) and confirm no `ImportError` on startup, then exercise Membros Pendentes and Settings → Otimizar Banco de Dados once more as a final regression check for this phase.

- [ ] **Step 4: Commit**

```bash
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Delete deprecated database_manager.py, fully replaced by services layer"
```

---

## Phase 2: Delete `manage_plans_dialog.py`

Contrary to the original audit's assumption that this dialog was reachable from 3 sidebar/menu actions, tracing `_show_manage_plans_dialog` (`main_window.py:824-826`) shows it calls `self.settings_coordinator.show_manage_plans()`, which navigates to `PlansScreen` (`settings_coordinator.py:23-27`) — **not** `ManagePlansDialog`. A repo-wide search for `ManagePlansDialog(` found only its own class definition (`manage_plans_dialog.py:16`) — it is never instantiated anywhere. This phase is a pure dead-file deletion; no UI wiring changes are needed (the misleadingly-named method stays as-is, since it's out of scope to rename working code not part of this cleanup).

**Files:**
- Delete: `src/ui/dialogs/manage_plans_dialog.py`
- Modify: `src/ui/dialogs/__init__.py:7,17`
- Modify: `src/ui/main_window.py:41`

- [ ] **Step 1: Confirm it's truly never instantiated**

```bash
grep -rn "ManagePlansDialog(" src/
```
Expected: only `src/ui/dialogs/manage_plans_dialog.py:16` (the class definition line itself). If any other call site shows up, stop — the file is not dead and this task needs re-scoping.

- [ ] **Step 2: Remove the export from `src/ui/dialogs/__init__.py`**

Current:
```python
from .manage_plans_dialog import ManagePlansDialog
```
and in `__all__`:
```python
    'ManagePlansDialog',
```
Delete both lines.

- [ ] **Step 3: Remove the now-unused import in `main_window.py`**

Current (`main_window.py:41`):
```python
from src.ui.dialogs import AddMemberDialog, SyncDialog, ManagePlansDialog, ExpiringPlansDialog
```
Replace with:
```python
from src.ui.dialogs import AddMemberDialog, SyncDialog, ExpiringPlansDialog
```

- [ ] **Step 4: Delete the file**

```bash
git rm src/ui/dialogs/manage_plans_dialog.py
```

- [ ] **Step 5: Verify no remaining references**

```bash
grep -rn "manage_plans_dialog\|ManagePlansDialog" src/
```
Expected: no output.

- [ ] **Step 6: Manual smoke test**

Run the app, open Plans (via sidebar "Financeiro → Planos" or "Configurações → Planos" or the ⚙️ menu's "Gerenciar Planos" action — all three routes) and confirm `PlansScreen` opens exactly as before (this file didn't change behavior in any of these paths, since none of them ever reached the deleted dialog).

- [ ] **Step 7: Commit**

```bash
git add src/ui/dialogs/__init__.py src/ui/main_window.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Delete unreachable manage_plans_dialog.py, superseded by plans_screen.py"
```

---

## Phase 3: Drop the dead `db_manager=` fallback from `MemberService`/`PaymentService`

Every live construction site already passes `db_session=` (verified by the original audit's grep, and unaffected by Phase 1's migration since that also constructs with `db_session=`). This phase removes the parameter and every `if self._session is not None: ... else: ...` branch that exists only to support it. Step 4 of each task below re-verifies the current call-site list at implementation time rather than relying on a hardcoded count, since it will have shifted after Phase 1.

**Files:**
- Modify: `src/services/member_service.py`
- Modify: `src/services/payment_service.py`

### Task 3.1: `member_service.py`

- [ ] **Step 1: Simplify the constructor**

Current (`member_service.py:60-81`):
```python
    def __init__(
        self, 
        db_session: Optional[Session] = None,
        db_manager: Optional["DatabaseManager"] = None
    ):
        """
        Inicializa o serviço de membros.
        
        Args:
            db_session: Sessão SQLAlchemy para acesso aos dados (preferencial)
            db_manager: Instância do DatabaseManager legado (compatibilidade)
        
        Raises:
            ValueError: Se nenhum dos parâmetros for fornecido
        """
        self._session = db_session
        self._db_manager = db_manager
        
        if db_session is None and db_manager is None:
            raise ValueError(
                "MemberService requer db_session (SQLAlchemy) ou db_manager (legado)"
            )
```

Replace with:
```python
    def __init__(self, db_session: Session):
        """
        Inicializa o serviço de membros.
        
        Args:
            db_session: Sessão SQLAlchemy para acesso aos dados
        """
        self._session = db_session
```

Also remove the now-unused `TYPE_CHECKING` import block (`member_service.py:23-24`):
```python
if TYPE_CHECKING:
    from src.data.database_manager import DatabaseManager
```
and drop `TYPE_CHECKING` from the `typing` import on line 11 if nothing else in the file uses it (`grep -n "TYPE_CHECKING" src/services/member_service.py` after the edit should show only the import line if still needed elsewhere, or nothing).

- [ ] **Step 2: Collapse each `if self._session is not None: / else:` branch**

For each site below, delete the `else` clause (and its `self._db_manager...` body) and un-indent the `if` body so it always runs. Two worked examples, then the full list to repeat the same transformation on:

`create()` (`member_service.py:124-127`) — before:
```python
        if self._session is not None:
            return self._create_sqlalchemy(member_data)
        else:
            return self._create_legacy(member_data)
```
after:
```python
        return self._create_sqlalchemy(member_data)
```
Also delete the now-dead `_create_legacy` method entirely (`member_service.py:467-479`).

`get_by_id()` (`member_service.py:139-142`) — before:
```python
        if self._session is not None:
            return self._session.query(Membro).filter(Membro.id == member_id).first()
        else:
            return self._db_manager.get_member_by_id(member_id)
```
after:
```python
        return self._session.query(Membro).filter(Membro.id == member_id).first()
```

Repeat the same "keep the `if` body, delete the `else` body, un-indent" transformation at each of these remaining sites (line numbers are pre-edit — re-grep after each edit if line numbers drift):

| Method | Lines | `else` body being deleted |
|---|---|---|
| `search_by_name` | `member_service.py:175-178` | `return self._db_manager.find_members_by_name(name_query)` |
| `get_all` | `member_service.py:195-198` | `return self._db_manager.get_all_members()` |
| `get_recent_members` | `member_service.py:214-230` | fallback block computing `all_members = self._db_manager.get_all_members()`, defining `sort_key`, and `return sorted(all_members, key=sort_key, reverse=True)[:limit]` — delete the `else`-less fallback entirely, keep only the `if self._session is not None:` body's `return [...]` (un-indented), since a session is now always present |
| `get_paginated` | `member_service.py:257-273` | the `else:` block calling `self._db_manager.get_members_paginated(...)` and wrapping it in `PaginatedResult` |
| `update` | `member_service.py:287-289` | `raise NotImplementedError(...)` — replace the whole 3-line if/raise with just `return self._update_sqlalchemy(member_id, **kwargs)` |
| `update_from_dict` | `member_service.py:315-327` | `else:` block calling `self._db_manager.update_member_from_dict(...)` |
| `delete` | `member_service.py:339-347` | `else:` block calling `self._db_manager.delete_member(member_id)` |
| `get_birthdays` | `member_service.py:363-366` | `return self._db_manager.get_members_by_birthday_month(month)` |
| `update_expired_plans` | `member_service.py:375-378` | `return self._db_manager.update_expired_plans()` |
| `count_by_status` | `member_service.py:387-396` | fallback block iterating `self._db_manager.get_all_members()` |
| `count_by_plan` | `member_service.py:405-414` | fallback block iterating `self._db_manager.get_all_members()` |
| `_get_plan_by_name` | `member_service.py:514` | condition is `if not plan_name or self._session is None: return None` — simplify to `if not plan_name: return None` (session is always present now) |
| `get_all_excluding_pending` | `member_service.py:976-979` | `if self._session is not None:` guards the real query; the fallback below it (`all_members = self._db_manager.get_all_members()` + list comprehension) is now unreachable — delete the fallback, keep only the `return self._session.query(...)` line, un-indented |

- [ ] **Step 3: Verify no `_db_manager` or `_create_legacy` references remain**

```bash
grep -n "_db_manager\|_create_legacy\|DatabaseManager" src/services/member_service.py
```
Expected: no output.

- [ ] **Step 4: Verify every existing construction site still works**

```bash
grep -rn "MemberService(" src/
```
Confirm every call site passes `db_session=...` positionally or by keyword (per the original audit, all 8 do). No call site needs to change.

- [ ] **Step 5: Manual smoke test**

Run the app: search for a member, view a member's detail (uses `get_by_id`), check the dashboard birthday widget, view the members list with a status filter (uses `get_paginated`), edit and delete a test member. Confirm all behave as before.

- [ ] **Step 6: Commit**

```bash
git add src/services/member_service.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Remove dead db_manager fallback from MemberService"
```

### Task 3.2: `payment_service.py`

- [ ] **Step 1: Simplify the constructor**

Current (`payment_service.py:63-84`):
```python
    def __init__(
        self, 
        db_session: Optional[Session] = None,
        db_manager: Optional["DatabaseManager"] = None
    ):
        """
        Inicializa o serviço de pagamentos.
        
        Args:
            db_session: Sessão SQLAlchemy para acesso aos dados (preferencial)
            db_manager: Instância do DatabaseManager legado (compatibilidade)
        
        Raises:
            ValueError: Se nenhum dos parâmetros for fornecido
        """
        self._session = db_session
        self._db_manager = db_manager
        
        if db_session is None and db_manager is None:
            raise ValueError(
                "PaymentService requer db_session (SQLAlchemy) ou db_manager (legado)"
            )
```

Replace with:
```python
    def __init__(self, db_session: Session):
        """
        Inicializa o serviço de pagamentos.
        
        Args:
            db_session: Sessão SQLAlchemy para acesso aos dados
        """
        self._session = db_session
```

Also remove the now-unused `TYPE_CHECKING` import block (`payment_service.py:21-22`), same as Task 3.1 Step 1.

- [ ] **Step 2: Collapse each `if self._session is not None: / else:` branch**

`create_payment()` (`payment_service.py:123-147`) — before:
```python
        if self._session is not None:
            return self._create_payment_sqlalchemy(
                member_id, valor, tipo_transacao, descricao,
                metodo_pagamento, nova_data_vencimento, data_pagamento
            )
        else:
            payment_id = self._db_manager.add_payment(
                member_id=member_id,
                valor=valor,
                tipo_transacao=tipo_transacao,
                descricao=descricao,
                metodo_pagamento=metodo_pagamento,
                nova_data_vencimento=nova_data_vencimento,
                data_pagamento=data_pagamento
            )
            if payment_id:
                return PaymentResult(
                    success=True,
                    payment_id=payment_id,
                    message="Pagamento registrado com sucesso."
                )
            return PaymentResult(
                success=False,
                message="Erro ao registrar pagamento."
            )
```
after:
```python
        return self._create_payment_sqlalchemy(
            member_id, valor, tipo_transacao, descricao,
            metodo_pagamento, nova_data_vencimento, data_pagamento
        )
```

`register_plan_payment()`'s price lookup (`payment_service.py:174-179`) — before:
```python
        if self._session is not None:
            from src.services.plan_service import PlanService
            valor = PlanService(db_session=self._session).get_plan_price(plan_name)
        else:
            from src.config import PLANOS_PRECOS
            valor = PLANOS_PRECOS.get(plan_name, 0.0)
```
after:
```python
        from src.services.plan_service import PlanService
        valor = PlanService(db_session=self._session).get_plan_price(plan_name)
```

Repeat the same transformation at each remaining site:

| Method | Lines | `else` body being deleted |
|---|---|---|
| `get_summary` | `payment_service.py:218-226` | `else:` block calling `self._db_manager.get_financial_summary(...)` and wrapping in `FinancialSummary` |
| `get_breakdown` | `payment_service.py:243-254` | `else:` block calling `self._db_manager.get_revenue_breakdown(...)` and wrapping in `RevenueBreakdown` list |
| `get_transactions` | `payment_service.py:273-276` | `return self._db_manager.get_transactions_in_range(start_date, end_date, limit)` |
| `get_member_history` | `payment_service.py:288-291` | `return self._db_manager.get_member_payment_history(member_id)` |

- [ ] **Step 3: Verify no `_db_manager` references remain**

```bash
grep -n "_db_manager\|DatabaseManager" src/services/payment_service.py
```
Expected: no output.

- [ ] **Step 4: Verify every existing construction site still works**

```bash
grep -rn "PaymentService(" src/
```
Confirm every call site passes `db_session=...`.

- [ ] **Step 5: Manual smoke test**

Run the app: perform a check-in on a per-checkin plan (Diária/Gympass/Totalpass — exercises `create_payment`), renew a time-based plan (exercises `register_plan_payment`), open the Financial dashboard (exercises `get_summary`/`get_breakdown`), view a member's payment history. Confirm all behave as before.

- [ ] **Step 6: Commit**

```bash
git add src/services/payment_service.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Remove dead db_manager fallback from PaymentService"
```

---

## Phase 4: Delete `member_search_service.py`

**Files:**
- Delete: `src/core/member_search_service.py`
- Modify: `src/ui/main_window.py:17,60`
- Modify: `src/ui/coordinators/checkin_coordinator.py:33,72`
- Modify: `src/ui/coordinators/members_coordinator.py:216,346,387,541,596,603`

`MemberSearchService.search_by_name()` and `.get_member_by_id()` (`member_search_service.py:16-53`) are pure delegates to `DataProvider` — `self.data_provider = get_provider()`, then e.g. `return self.data_provider.get_member_by_id(member_id)`. **`main_window.py` itself never calls `.search_service.` methods** — it only constructs the instance (`self.search_service = MemberSearchService()` at line 60) and hands `self.window` (the `MainWindow` instance) to its coordinators, which are the real 8 callers, all via `self.window.search_service.get_member_by_id(...)` (none of them call `search_by_name`):
- `checkin_coordinator.py:33,72`
- `members_coordinator.py:216,346,387,541,596,603`

`main_window.py` already owns `self.manager = AniversariantesManager()` (`main_window.py:59`), and `AniversariantesManager.__init__` sets `self.data_provider = get_provider()` (`aniversariantes_manager.py:18`) — the exact same `DataProvider` singleton `MemberSearchService` wraps. So `self.window.manager.data_provider.get_member_by_id(...)` is a byte-for-byte behavioral equivalent to `self.window.search_service.get_member_by_id(...)`, reachable today with zero new attributes on `MainWindow`.

- [ ] **Step 1: Confirm the full call-site map**

```bash
grep -rn "search_service\." src/
```
Expected: exactly the 8 matches listed above (6 in `members_coordinator.py`, 2 in `checkin_coordinator.py`), all calling `.get_member_by_id(...)`. If this turns up anything in `main_window.py` itself or a `search_by_name` call, stop — the map above is stale and the remaining steps need to be re-targeted.

- [ ] **Step 2: Repoint the 8 call sites**

In `checkin_coordinator.py`, replace both occurrences:
```python
member_data = self.window.search_service.get_member_by_id(member_id)
```
with:
```python
member_data = self.window.manager.data_provider.get_member_by_id(member_id)
```

In `members_coordinator.py`, replace all 6 occurrences the same way (the argument differs per call site — keep whatever variable each site already passes, e.g. `member_data["id"]`, `updated_data["id"]`, `renewal_data["id"]` — only the `self.window.search_service` → `self.window.manager.data_provider` prefix changes).

- [ ] **Step 3: Remove the import and instantiation from `main_window.py`**

Current (`main_window.py:17,60`):
```python
from src.core.member_search_service import MemberSearchService
...
        self.search_service = MemberSearchService()
```
Delete both lines.

- [ ] **Step 4: Delete the file**

```bash
git rm src/core/member_search_service.py
```

- [ ] **Step 5: Verify no remaining references**

```bash
grep -rn "member_search_service\|MemberSearchService\|search_service" src/
```
Expected: no output.

- [ ] **Step 6: Manual smoke test**

Run the app and exercise every flow that touched the deleted call sites: search for a member on the member search screen (uses `MemberService.search_by_name_as_dicts` directly already, unaffected — sanity check only); click a check-in search result (`checkin_coordinator.py:33`); complete a check-in and confirm the post-checkin refresh works (`checkin_coordinator.py:72`); select a member from a search result on the member list (`members_coordinator.py:216,541`); edit a member and confirm the detail view refreshes with updated data (`members_coordinator.py:346,596`); renew a plan and confirm the detail view refreshes (`members_coordinator.py:387,603`).

- [ ] **Step 7: Commit**

```bash
git add src/ui/main_window.py src/ui/coordinators/checkin_coordinator.py src/ui/coordinators/members_coordinator.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Delete member_search_service.py, replaced by DataProvider.get_member_by_id"
```

---

## Phase 5: Extract duplicated report helpers

**Files:**
- Create: `src/reports/_common.py`
- Modify: `src/reports/finance_report.py:46-56`
- Modify: `src/reports/members_report.py:24-34`
- Modify: `src/reports/frequency_report.py:19-28`

`_get_reports_dir()` and `_get_template_env()` are byte-identical across all three files.

- [ ] **Step 1: Create the shared module**

```python
"""Helpers compartilhados pelos geradores de relatório."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def get_reports_dir() -> Path:
    project_root = Path(__file__).parent.parent.parent
    reports_dir = project_root / "relatorios"
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def get_template_env() -> Environment:
    project_root = Path(__file__).parent.parent.parent
    templates_dir = project_root / "src" / "templates" / "reports"
    return Environment(loader=FileSystemLoader(str(templates_dir)))
```

(Names are un-prefixed since this module's whole purpose is to be the shared, public home for these two functions — the leading underscore in the original per-file copies only made sense when they were file-private.)

- [ ] **Step 2: Update `finance_report.py`**

Delete lines 46-56 (the two function defs). Add near the top, with the other `src.reports` import:
```python
from src.reports._common import get_reports_dir, get_template_env
```
Then replace every call to `_get_reports_dir()` with `get_reports_dir()` and `_get_template_env()` with `get_template_env()` in this file:
```bash
grep -n "_get_reports_dir()\|_get_template_env()" src/reports/finance_report.py
```
Update each match.

- [ ] **Step 3: Update `members_report.py`** — same transformation: delete lines 24-34, add the import, replace call sites.

- [ ] **Step 4: Update `frequency_report.py`** — same transformation: delete lines 19-28, add the import, replace call sites.

- [ ] **Step 5: Check for now-unused imports**

For each of the three files, check whether `Environment`/`FileSystemLoader` (and `Path`, if applicable) are still used anywhere else in the file:
```bash
grep -n "Environment(\|FileSystemLoader(\|Path(" src/reports/finance_report.py src/reports/members_report.py src/reports/frequency_report.py
```
If a file's only remaining match for `Environment(`/`FileSystemLoader(` is inside `_common.py` itself (i.e. zero matches left in the report file), remove that file's now-unused `from jinja2 import Environment, FileSystemLoader` line. Leave `from pathlib import Path` alone unless the same check shows zero remaining uses.

- [ ] **Step 6: Run the existing report test plus the full suite**

```bash
/c/Users/Usuario/.conda/envs/alcoa/python.exe -m pytest test_reports_jinja.py tests/ -q
```
Expected: `97 passed` (per `REPORTS_STATUS.md`, `test_reports_jinja.py` already validates 3/3 reports with simulated data; `tests/test_reports_overhaul.py` covers related report behavior).

- [ ] **Step 7: Manual smoke test**

Generate all three reports (Financeiro, Membros, Frequência) from the app and confirm they open in the browser with the same layout and data as before.

- [ ] **Step 8: Commit**

```bash
git add src/reports/_common.py src/reports/finance_report.py src/reports/members_report.py src/reports/frequency_report.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Extract duplicated report helpers into src/reports/_common.py"
```

---

## Out of scope (do not touch in this plan)

- Google Sheets sync feature (`sync_worker.py`, `sync_dialog.py`, `legacy_sync_gateway.py`, `google_sheets_service.py`) — confirmed live via `settings_coordinator.show_sync_dialog()`.
- `plans_config.json` / `config.py`'s `PLANOS_*` constants — legitimate factory-defaults source for both plan UIs' "Restaurar Padrões" button, not dead.
- `migrate_data.py`, `test_duplicate_payment.py`, and `tests/validate_improvements.py` — one-off/offline scripts still importing `DatabaseManager`, not part of the running app or the collected pytest suite (`test_duplicate_payment.py` already fails at collection today on an unrelated missing-table error; `tests/validate_improvements.py` doesn't match pytest's discovery pattern).
- `CheckinService`'s own `db_manager` parameter — a different class and a different concern from Phase 3's scope (`MemberService`/`PaymentService` only).
