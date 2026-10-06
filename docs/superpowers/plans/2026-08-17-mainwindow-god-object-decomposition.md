# MainWindow God Object Decomposition — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Every task runs under `/ponytail:ponytail` — reuse the four existing coordinators, delete over add, no new abstractions.

**Goal:** Finish dismantling the `main_window.py` God Object by deleting its ~250-line delegation-shim layer, relocating the last two embedded flows into existing coordinators, and extracting UI construction — leaving a thin ~400-line window shell.

**Architecture:** The decomposition is ~70% done: `MembersCoordinator`, `CheckinCoordinator`, `ReportsCoordinator`, `SettingsCoordinator` already hold the domain logic. This plan is a mechanical refactor under a characterization-test safety net (Phase 0), not a redesign. Screen signals get wired directly to coordinators; two straggler flows (financeiro, aniversariantes) move into coordinators that already own that domain; UI assembly moves to a `build_ui()` function.

**Tech Stack:** Python 3.13, PyQt6, SQLAlchemy, pytest (`QT_QPA_PLATFORM=offscreen` for headless UI tests).

**Spec:** `docs/superpowers/specs/2026-08-17-mainwindow-god-object-decomposition-design.md`

---

## Complexity → model legend

Each step bullet is tagged `[C:x.x]`. Each task carries a recommended executor derived from its overall complexity:

| Complexity | Executor |
|------------|----------|
| 1.0 – 2.5  | **Haiku** |
| 2.5 – 4.0  | **Sonnet 5, high effort** |
| 5.0        | **Opus 4.8, high effort** |

Run-the-test / commit / grep steps are inherently trivial (`[C:1.0]`, Haiku) even inside a Sonnet task; the task-level executor is what you dispatch the subagent with.

## Baseline command (all phases)

Run the full suite headless before and after every task:

```bash
QT_QPA_PLATFORM=offscreen /c/Users/Usuario/.conda/envs/alcoa/python.exe -m pytest -q
```

Expected baseline: green. If a phase's only change is deletion/move, "green + smoke test passes" is the acceptance bar.

---

## Task 0: Safety net — MainWindow smoke test

**Overall complexity: 3.0/5 → Sonnet 5, high effort.** (Qt-offscreen construction + signal-receiver introspection is fiddly; get it right once and every later phase leans on it.)

**Files:**
- Create: `tests/test_main_window_smoke.py`

- [ ] **Step 1: Write the smoke test** `[C:3.0]`

Construct the real `MainWindow` headless and assert two invariants Phases 1–3 must preserve: the coordinators exist, and the coordinator methods the screen signals should target exist and are callable. `__init__` calls `_auto_connect()` which starts a `DatabaseConnectionWorker` thread — construct, assert, then `window.deleteLater()`; never start the event loop.

`ponytail:` the smoke test asserts construction + handler existence, not each `connect()` at runtime — PyQt makes runtime connection-counting brittle, and emitting signals to check them risks firing real dialogs. Runtime wiring is verified by launching the app once at the end of Task 1 (Task 1, Step 6).

```python
"""Smoke test: MainWindow constrói e mantém coordenadores + handlers.

Rede de segurança para a decomposição do God Object. Não testa comportamento
de negócio (isso vive nos testes de service) — só garante que a janela monta e
que os métodos-alvo dos sinais existem, que é o risco real do refactor.
"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app, monkeypatch):
    # ponytail: o smoke test não precisa conectar ao banco — só verifica
    # montagem + coordenadores. Neutralizamos _auto_connect para não iniciar
    # a QThread de migração (que vazaria e derrubaria a suíte inteira).
    monkeypatch.setattr(MainWindow, "_auto_connect", lambda self: None)
    w = MainWindow()
    yield w
    w.deleteLater()


def test_coordinators_instantiated(window):
    assert window.members_coordinator is not None
    assert window.checkin_coordinator is not None
    assert window.reports_coordinator is not None
    assert window.settings_coordinator is not None


@pytest.mark.parametrize("coordinator, method", [
    ("members_coordinator", "on_member_search_by_name"),
    ("members_coordinator", "on_edit_member_clicked"),
    ("members_coordinator", "on_delete_member_clicked"),
    ("members_coordinator", "on_list_delete_member_clicked"),
    ("checkin_coordinator", "on_confirm_checkin_clicked"),
    ("checkin_coordinator", "on_checkin_search_by_name"),
])
def test_coordinator_handlers_exist(window, coordinator, method):
    assert callable(getattr(getattr(window, coordinator), method))
```

After Tasks 2–3, extend the parametrize list with the moved handlers (`reports_coordinator.load_financial_data`, `members_coordinator.on_aniversariantes_search_clicked`) so the guard tracks the relocations.

- [ ] **Step 2: Run the smoke test — expect PASS** `[C:1.0]`

```bash
QT_QPA_PLATFORM=offscreen /c/Users/Usuario/.conda/envs/alcoa/python.exe -m pytest tests/test_main_window_smoke.py -v
```
Expected: all tests PASS against the current (pre-refactor) code.

- [ ] **Step 3: Run the full suite — expect green** `[C:1.0]`

```bash
QT_QPA_PLATFORM=offscreen /c/Users/Usuario/.conda/envs/alcoa/python.exe -m pytest -q
```

- [ ] **Step 4: Commit** `[C:1.0]`

```bash
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal add tests/test_main_window_smoke.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Add MainWindow smoke test as decomposition safety net"
```

---

## Task 1: Delete the delegation-shim layer

**Overall complexity: 3.5/5 → Sonnet 5, high effort.** (Mechanical but wide — ~45 methods across 265 lines, plus two monkey-patch reassignments. The risk is volume: one missed rewire silently breaks a button. Grep-before-delete discipline is mandatory.)

**Files:**
- Modify: `src/ui/main_window.py` (delete shims lines ~334–341, ~469–471, ~649–914 selectively; rewire `_connect_screen_signals` ~372–461 and monkey-patches 416–418)

**The two survivors — DO NOT delete:** `_update_dashboard` (609) and `_show_members_list` (485). Coordinators call `self.window._update_dashboard()` and `self.window._show_members_list()`. Also keep genuine nav/window methods: `_show_dashboard`, `_show_members_list_only`, `_show_pending_members_only`, `_show_checkin_screen_only`, `_show_financial_screen_only`, `_show_member_search`, `_show_aniversariantes`, `_show_pending_members`, `_show_checkin_screen`, `_show_financial_screen`, `_show_notes_screen`, `_show_settings_menu`, `_on_home_clicked`, `_on_*_section_clicked` — these hold real `stacked_widget.setCurrentIndex` logic and/or are wired to the sidebar, not shims.

- [ ] **Step 1: Confirm the shim inventory is pure-forward** `[C:2.0]`

For each candidate shim, confirm its body is a single coordinator call and it is referenced only inside `main_window.py`:

```bash
QT_QPA_PLATFORM=offscreen /c/Users/Usuario/.conda/envs/alcoa/python.exe -m pytest -q  # baseline green
```
Use the Grep tool for each name across `src/` — any hit outside `main_window.py` means repoint that caller too (none expected; verified in planning for the callback-looking ones). Shims to delete (all forward to the named coordinator):
- Members: `_on_dashboard_member_clicked`, `_on_member_search_by_name`, `_on_member_search_completed`, `_on_member_result_clicked`, `_load_member_history`, `_load_member_financial_history`, `_on_edit_member_clicked`, `_on_renew_plan_clicked`, `_on_delete_member_clicked`, `_on_member_whatsapp_clicked`, `_on_member_quick_payment_clicked`, `_on_member_history_shortcut_clicked`, `_delete_member`, `_on_member_updated`, `_on_plan_renewed`, `_on_delete_checkin_requested`, `_on_edit_checkin_requested`, `_show_add_member_dialog`, `_load_members_list`, `_on_members_list_refresh`, `_on_members_list_member_selected`, `_load_list_member_history`, `_load_list_member_financial_history`, `_on_list_edit_member_clicked`, `_on_list_renew_plan_clicked`, `_on_list_delete_member_clicked`, `_on_list_member_whatsapp_clicked`, `_on_list_member_quick_payment_clicked`, `_on_list_member_history_shortcut_clicked`, `_on_list_member_updated`, `_on_list_plan_renewed`, `_delete_list_member`
- Checkin: `_on_checkin_search_by_name`, `_on_checkin_search_completed`, `_on_checkin_result_clicked`, `_on_confirm_checkin_clicked`, `_on_checkin_worker_completed`, `_on_checkin_profile_clicked`
- Reports: `_generate_members_report`, `_generate_financial_report`, `_generate_frequency_report`
- Settings: `_show_manage_plans_dialog`, `_show_expiring_plans_dialog`, `_show_sync_dialog`, `_create_database_backup`, `_optimize_database`, `_run_database_migration`

- [ ] **Step 2: Rewire `_connect_screen_signals` and `_connect_sidebar_signals` to coordinators** `[C:3.0]`

Replace every `self._on_foo` / `self._show_foo` target that pointed at a deleted shim with the coordinator method. Examples:

```python
# antes:  self.member_search_screen.edit_button.clicked.connect(self._on_edit_member_clicked)
# depois:
self.member_search_screen.edit_button.clicked.connect(self.members_coordinator.on_edit_member_clicked)

# antes:  self.checkin_screen.confirm_button.clicked.connect(self._on_confirm_checkin_clicked)
# depois:
self.checkin_screen.confirm_button.clicked.connect(self.checkin_coordinator.on_confirm_checkin_clicked)

# sidebar (antes -> depois):
self.sidebar.reports_members_clicked.connect(self.reports_coordinator.generate_members_report)
self.sidebar.settings_backup_clicked.connect(self.settings_coordinator.create_database_backup)
self.sidebar.settings_sync_clicked.connect(self.settings_coordinator.show_sync_dialog)
```

Signals wired to kept methods (`_show_members_list_only`, `_on_home_clicked`, etc.) stay unchanged.

- [ ] **Step 3: Repoint the two monkey-patches (lines 416–418)** `[C:2.5]`

```python
# antes:
# self.member_search_screen.request_delete_checkin = self._on_delete_checkin_requested
# self.member_search_screen.request_edit_checkin = self._on_edit_checkin_requested
# depois:
self.member_search_screen.request_delete_checkin = self.members_coordinator.on_delete_checkin_requested
self.member_search_screen.request_edit_checkin = self.members_coordinator.on_edit_checkin_requested
```

- [ ] **Step 4: Delete all shim method definitions listed in Step 1** `[C:2.5]`

Remove each `def _on_...`/`def _load_...`/`def _generate_...`/`def _show_manage_plans_dialog` etc. body. Leave the `# === section ===` comments only where a kept method still lives under them.

- [ ] **Step 5: Run smoke + full suite — expect green** `[C:1.0]`

```bash
QT_QPA_PLATFORM=offscreen /c/Users/Usuario/.conda/envs/alcoa/python.exe -m pytest -q
```
Expected: green. Then confirm no dangling `self._on_` reference remains — Grep `self\._(on|load|show|generate|delete)_` in `main_window.py` and check each remaining hit is an intentionally-kept method.

- [ ] **Step 6: Manual launch verification** `[C:2.0]`

Because PyQt signal wiring isn't fully exercised by the smoke test, launch the app once and click through: dashboard → member search → edit/delete/renew, check-in confirm, members list actions, financeiro, relatórios, backup, sync. Confirm no `AttributeError` and each button acts. (This is the real regression gate for Task 1.)

```bash
/c/Users/Usuario/.conda/envs/alcoa/python.exe run.py
```

- [ ] **Step 7: Commit** `[C:1.0]`

```bash
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal add src/ui/main_window.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Delete MainWindow delegation shims, wire screen signals to coordinators"
```

---

## Task 2: Move the two embedded flows into existing coordinators

**Overall complexity: 3.5/5 → Sonnet 5, high effort.** (Real code movement + rewiring + one judgment call on where financeiro lands. Preserves behavior, so smoke + manual launch is the gate.)

**Files:**
- Modify: `src/ui/coordinators/reports_coordinator.py` (add financeiro methods)
- Modify: `src/ui/coordinators/members_coordinator.py` (add aniversariantes methods)
- Modify: `src/ui/main_window.py` (delete moved methods, rewire signals)

### 2a — Financeiro → ReportsCoordinator

- [ ] **Step 1: Move the four financial methods** `[C:3.0]`

Cut `_load_financial_data`, `_on_financial_data_loaded`, `_on_financial_data_error`, `_show_plan_distribution_dialog` from `main_window.py` into `ReportsCoordinator` as `load_financial_data`, `on_financial_data_loaded`, `on_financial_data_error`, `show_plan_distribution_dialog`. Replace every `self.` referencing window state with `self.window.` (e.g. `self.window.financial_screen`, `self.window._financial_worker`). Keep the local imports (`FinancialDataWorker`, `datetime`, `FinancialGraphsDialog`) inside the methods, matching the coordinator's existing lazy-import style.

`ponytail:` land these in `ReportsCoordinator` (it already owns finance-report generation); do **not** create a `FinancialCoordinator` — a 4th finance method in an existing 88-line file is cheaper than a new file + wiring.

- [ ] **Step 2: Rewire financial screen signals** `[C:2.0]`

In `_connect_screen_signals`:
```python
self.financial_screen.update_button.clicked.connect(self.reports_coordinator.load_financial_data)
self.financial_screen.plan_chart_button.clicked.connect(self.reports_coordinator.show_plan_distribution_dialog)
```
And `_show_financial_screen_only` / `_show_financial_screen` (kept nav methods) must call `self.reports_coordinator.load_financial_data()` instead of the deleted `self._load_financial_data()`.

- [ ] **Step 3: Run smoke + full suite — expect green** `[C:1.0]`

```bash
QT_QPA_PLATFORM=offscreen /c/Users/Usuario/.conda/envs/alcoa/python.exe -m pytest -q
```

### 2b — Aniversariantes → MembersCoordinator

- [ ] **Step 4: Move the two aniversariantes methods** `[C:2.5]`

Cut `_on_aniversariantes_search_clicked` and `_on_aniversariantes_fetch_completed` into `MembersCoordinator` as `on_aniversariantes_search_clicked` / `on_aniversariantes_fetch_completed`, repointing `self.` → `self.window.` (`self.window.aniversariantes_screen`, `self.window.formatter`, `self.window.manager`, `self.window.worker`).

- [ ] **Step 5: Rewire aniversariantes signal** `[C:1.5]`

```python
self.aniversariantes_screen.search_button.clicked.connect(
    self.members_coordinator.on_aniversariantes_search_clicked
)
```

- [ ] **Step 6: Run smoke + full suite — expect green** `[C:1.0]`

```bash
QT_QPA_PLATFORM=offscreen /c/Users/Usuario/.conda/envs/alcoa/python.exe -m pytest -q
```

- [ ] **Step 7: Manual launch — verify financeiro + aniversariantes** `[C:2.0]`

Launch, open Financeiro (period load + plan-distribution chart) and Aniversariantes (search a month, confirm list renders). Confirm no errors.

- [ ] **Step 8: Commit** `[C:1.0]`

```bash
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal add src/ui/main_window.py src/ui/coordinators/reports_coordinator.py src/ui/coordinators/members_coordinator.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Move financeiro and aniversariantes flows into coordinators"
```

---

## Task 3: Extract UI construction into build_ui()

**Overall complexity: 3.0/5 → Sonnet 5, high effort.** (Straight code move, but attribute-sensitive: `build_ui` must set the exact same `window.*` attributes `_setup_ui` did, or later methods break. No logic change.)

**Files:**
- Create: `src/ui/main_window_ui.py`
- Modify: `src/ui/main_window.py`

- [ ] **Step 1: Create `build_ui(window)`** `[C:3.0]`

Move the body of `_setup_ui` (lines ~89–230: title bar, floating sidebar, stacked widget, screen instantiation, stack indices) into a module-level `def build_ui(window):` in `main_window_ui.py`. Every `self.X = ...` becomes `window.X = ...`. Keep `window._connect_sidebar_signals()` and `window._connect_screen_signals()` calls at the end (those methods stay on the window). Import screens/components/`Sidebar`/`STYLESHEET` in the new module.

`ponytail:` a free function, not a `_UiBuilder` class — there's no state to hold; a function that mutates `window` is the smaller diff.

- [ ] **Step 2: Replace `_setup_ui` with a one-line delegate** `[C:1.5]`

```python
def _setup_ui(self):
    from src.ui.main_window_ui import build_ui
    build_ui(self)
```
(Or call `build_ui(self)` directly from `__init__` and delete `_setup_ui` — either; prefer deleting the wrapper if nothing else references `_setup_ui`. Grep first.)

- [ ] **Step 3: Run smoke + full suite — expect green** `[C:1.0]`

```bash
QT_QPA_PLATFORM=offscreen /c/Users/Usuario/.conda/envs/alcoa/python.exe -m pytest -q
```

- [ ] **Step 4: Manual launch — verify UI renders identically** `[C:2.0]`

Launch; confirm title bar buttons (min/max/close), sidebar float + resize, all screens present and navigable. Compare against pre-change behavior.

- [ ] **Step 5: Commit** `[C:1.0]`

```bash
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal add src/ui/main_window.py src/ui/main_window_ui.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Extract MainWindow UI construction into build_ui()"
```

---

## Task 4: Documentation reconciliation

**Overall complexity: 1.5/5 → Haiku.** (Pure prose edits mirroring an existing precedent in the same file.)

**Files:**
- Modify: `.claude/docs/ARCHITECTURE.md`

- [ ] **Step 1: Fix stale facts and resolve the God Object note** `[C:1.5]`

- Update line ~13 `~1700 linhas` → actual post-refactor count (run `wc -l src/ui/main_window.py`).
- Move "MainWindow como God Object" (Dívida Técnica item 1) into a new "Resolvido em 2026-08-17" subsection, mirroring the existing "Resolvido em 2026-08-15 — Limpeza ponytail-audit" block: note shims deleted, financeiro/aniversariantes moved to coordinators, `main_window_ui.py` added.
- Add `main_window_ui.py` to the UI Layer file map.

- [ ] **Step 2: Commit** `[C:1.0]`

```bash
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal add .claude/docs/ARCHITECTURE.md
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Reconcile ARCHITECTURE docs with MainWindow decomposition"
```

---

## Done criteria

- `main_window.py` holds no pure-forward shims, no financeiro/HTML-building logic, no UI-construction body (~400 lines, down from 965).
- Full suite green headless; `test_main_window_smoke.py` passes.
- Manual launch: every button/screen from Tasks 1–3 works.
- `ARCHITECTURE.md` reflects reality; God Object marked resolved.
