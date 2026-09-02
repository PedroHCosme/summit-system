# Ponytail Audit Cleanup — Design

## Context

A repo-wide over-engineering audit (`/ponytail:ponytail-audit`) surfaced seven
candidate findings. Two did not survive verification and are dropped; one was
reframed after deeper investigation. What remains is five concrete cleanups,
phased in dependency order, each independently shippable and manually
smoke-tested before merge.

Summit System is a live, single-developer app (PyQt6 desktop + Flask web,
SQLite, ~15-30 checkins/day). Verification for this work is manual (run the
app, exercise the affected screen) plus automated: the implementation
worktree revealed a real 97-test pytest suite (`tests/` + root-level
`test_reports_jinja.py`, not `src/test_reports_jinja.py` as first assumed
here) that this design doc didn't know about when written. See the
implementation plan's header for the corrected testing story — the full
suite was run as a gate before and after every task, not just manual
smoke tests.

## Findings dropped or corrected during verification

- **Google Sheets dead code (dropped as a deletion target, but see
  correction).** The audit's static grep on `data_provider.py` missed that
  `settings_coordinator.show_sync_dialog()` wires a live `SyncDialog` →
  `sync_worker.py` → `legacy_sync_gateway.py` → `google_sheets_service.py`
  path, reachable from Settings. This is a real, used feature, and its
  behavior was never changed by this plan. **Correction found during
  implementation:** `legacy_sync_gateway.py` itself turned out to depend on
  `DatabaseManager` (via `connect_database()`/`ensure_database_schema()`/
  `optimize_database()`, all invoked by `SyncImportService.execute()`) — a
  third live caller finding 1 missed. It was migrated onto
  `src/data/maintenance.py` (a new `create_tables()` function alongside
  `optimize_and_reindex()`) as an unplanned Task 1.3b before
  `database_manager.py` could be deleted. The Sync *feature* is still
  untouched behaviorally; only its incidental dependency on the deleted
  class was removed. See the implementation plan for the full task.
- **"Triple-redundant plan config" (corrected, no action needed).** Reading
  `manage_plans_dialog.py` and `plans_screen.py` in full showed both already
  write live edits through `PlanService` to the `Plano` DB table — the sole
  live store. `config.py`'s `PLANOS_PRECOS` etc. and `plans_config.json` are
  only read by both UIs' "Restaurar Padrões" (restore factory defaults)
  button — a distinct, legitimate concept (default catalog vs. live catalog),
  not a competing live store. No cleanup required beyond what deleting the
  dialog (finding 2 below) already removes.
- **`database_manager.py` (corrected from "delete" to "retire in two
  parts").** The class has two unrelated tenants: CRUD duplicated by
  `MemberService`, and `optimize_and_reindex()` — real DB-maintenance logic
  (VACUUM/ANALYZE/reindex) with no service-layer equivalent. Full deletion
  requires relocating that one method first (see finding 1).

## Findings in scope, phased in dependency order

### 1. Retire `database_manager.py` (~1884 lines)

- `pending_members_screen.py` currently calls `DatabaseManager` directly for
  `get_members_paginated(filter_status="PENDENTE")`, `update_member(id,
  plano=, estado_plano=)`, `delete_member(id)`. Verified 1:1 equivalents
  exist on `MemberService`: `get_paginated(filter_status=...)`, `update()`,
  `delete()`. Swap the screen to construct `MemberService(db_session=...)`
  instead of `DatabaseManager()`.
- `settings_coordinator.optimize_database()` calls
  `DatabaseManager().optimize_and_reindex()`. Move that method's logic into
  `src/data/maintenance.py` (currently empty — the evident intended home per
  `ARCHITECTURE.md`) as a plain function taking a session/connection. Update
  the coordinator's import and call site.
- **Correction found during implementation:** a third live caller,
  `legacy_sync_gateway.py` (used by the Sync feature), also depended on
  `DatabaseManager` and needed migrating the same way — see "Findings
  dropped or corrected during verification" above for the full story.
- Once all three callers are migrated, delete `src/data/database_manager.py`
  entirely.
- Out of scope: `migrate_data.py` and other one-off scripts (including
  `scripts/*.py`, `debug_*.py`, `verify_*.py`, `test_duplicate_payment.py`,
  `tests/validate_improvements.py` at the repo root) that may still import
  `DatabaseManager` for offline data migration or manual debugging — these
  aren't part of the running app or the collected pytest suite, and aren't
  touched. They will fail with `ModuleNotFoundError` if run by hand after
  this plan — see `.claude/docs/ARCHITECTURE.md`'s tech-debt list for the
  full enumeration.

**Smoke test:** approve and reject a pending member; run Settings → Otimizar
Banco de Dados and confirm the success dialog and stats still populate.

### 2. Delete `manage_plans_dialog.py` (~760 lines incl. wiring)

- `plans_screen.py` is a verified superset: both edit preço, valor por
  check-in, and requer-vencimento and both save through
  `plan_service.upsert_plans()` / `.commit()`. `plans_screen.py` additionally
  handles `is_quota`/`quota_amount` and soft-deactivation, which the dialog
  cannot do at all.
- Remove the dialog's 3 wiring points in `main_window.py` (menu/sidebar
  action connected to `_show_manage_plans_dialog`, and the method itself),
  and delete the file.

**Smoke test:** open Plans screen, edit a plan's price, create a new plan,
deactivate a plan, confirm changes persist after reload.

### 3. Drop the dead `db_manager=` fallback param from `MemberService` /
   `PaymentService` (~100-150 lines of branching)

- All 8 current construction sites already pass `db_session=`; grep
  confirmed zero live callers pass `db_manager=` to these two services even
  before finding 1. Finding 1 removes the last plausible reason anyone would
  reach for it.
- Remove the `db_manager` constructor parameter and the paired
  `if self._session is not None else ...` branches (~29 in
  `member_service.py`, ~11 in `payment_service.py`).
- Note: `CheckinService`'s own `db_manager=` parameter (used internally by
  `DatabaseManager.add_checkin()`, itself a deprecated method with no live
  UI caller) is a separate class and is NOT in scope here — do not touch
  `CheckinService`.

**Smoke test:** run a full check-in flow (time-based plan, per-checkin plan,
quota plan) and a plan renewal; confirm payments/vouchers post correctly.

### 4. Delete `member_search_service.py` (~53 lines)

- `MemberSearchService.search_by_name()` and `.get_member_by_id()` are pure
  delegates to `DataProvider`. The real callers (found during plan review,
  not in `main_window.py` itself as first assumed) are 8 sites across
  `checkin_coordinator.py` and `members_coordinator.py`, all calling
  `self.window.search_service.get_member_by_id(...)`.
- `main_window.py` already owns `self.manager.data_provider` — the same
  `get_provider()` singleton `MemberSearchService` wraps — so repoint all 8
  call sites to `self.window.manager.data_provider.get_member_by_id(...)`
  (a byte-for-byte behavioral equivalent) and delete the file. No new
  attribute needs to be added to `MainWindow`.

**Smoke test:** search for a member by name from the desktop app, confirm
results and selection still work.

### 5. Extract duplicated report helpers (~24 lines net)

- `_get_reports_dir()` and `_get_template_env()` are byte-identical across
  `finance_report.py`, `members_report.py`, `frequency_report.py`. Extract
  to `src/reports/_common.py`, import in all three.

**Smoke test:** generate all three reports (Financeiro, Membros,
Frequência) and confirm they open correctly in the browser with the same
data as before.

## Process

- One branch per phase, in the order above (each phase depends on the
  previous one being merged, except 4 and 5 which are independent and can be
  done in either order relative to 1-3, but are sequenced last since they're
  the smallest/lowest-risk).
- Manual smoke test per phase (see above) before merge, plus the full
  97-test automated suite (`test_reports_jinja.py` + `tests/`) run as a
  gate before and after every task — see the correction in "Context" above.
- Each phase's diff should be reviewed with `/ponytail:ponytail` discipline:
  shortest correct diff, no incidental refactoring beyond what the phase
  requires.

## Out of scope

- Google Sheets sync feature (confirmed live, not touched).
- `plans_config.json` / `config.py` default-catalog mechanism (legitimate,
  not touched).
- `migrate_data.py` and other offline scripts still referencing
  `DatabaseManager` (not part of the running app).
- `CheckinService`'s own `db_manager` parameter (separate class, separate
  concern).
- Any other findings not listed above — this plan covers exactly the five
  items above and nothing else.
