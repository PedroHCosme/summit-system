# MainWindow God Object Decomposition — Design

## Context

`src/ui/main_window.py` is the long-standing "God Object" of the desktop app
(flagged in `.claude/docs/ARCHITECTURE.md` § Dívida Técnica Conhecida, item 1).
It is **already ~70% dismantled**: four coordinators
(`MembersCoordinator`, `CheckinCoordinator`, `ReportsCoordinator`,
`SettingsCoordinator`, in `src/ui/coordinators/`) already hold the real
domain logic. What remains in `main_window.py` (965 lines, not the ~1700 the
docs claim — stale) is mostly leftover glue from a half-finished migration.

This design **finishes that migration**. It does not introduce a new pattern.
Scope decision (confirmed with the owner): *terminar o padrão atual* — no new
architecture, no MVC/MVP rewrite, no fixing the coordinator↔window coupling.
Just finish and clean up what's already there.

## What's actually left in main_window.py

1. **~40 pure delegation shims** (lines ~649–914): methods whose entire body is
   `self.<x>_coordinator.foo()`, wired to screen signals in
   `_connect_screen_signals`. They add zero value — the screen signal can
   connect straight to the coordinator method. **This is the bulk of the bloat.**
2. **Two flows still fully embedded** with real logic, never moved to a
   coordinator:
   - **Financeiro**: `_load_financial_data`, `_on_financial_data_loaded`,
     `_on_financial_data_error`, `_show_plan_distribution_dialog` (~75 lines,
     worker orchestration + result marshalling).
   - **Aniversariantes**: `_on_aniversariantes_search_clicked`,
     `_on_aniversariantes_fetch_completed` (~30 lines, incl. HTML string building).
3. **UI construction** (`_setup_ui`, ~140 lines: custom title bar, floating
   sidebar, stacked widget) + signal wiring (`_connect_sidebar_signals`,
   `_connect_screen_signals`) + genuine window concerns (connection handlers,
   `_run_migrations`, `_update_dashboard` timer, navigation, `resizeEvent`).

Only **two** private window methods are called from inside coordinators and
must stay as the window's API: `_update_dashboard` and `_show_members_list`
(verified by grepping `self.window._` across `src/ui/coordinators/`).

## Constraints / safety net

- **UI has no test coverage.** `tests/` covers the service layer only (checkin,
  member, financial, plans). The refactor is UI-layer-only and mechanical
  (move methods, rewire signals); the only real risk is a mis-wired signal,
  which the service tests will not catch.
- Net for every phase: (a) the collected `pytest` suite stays green (proves no
  import/breakage), and (b) a new headless smoke test (Phase 0) proves
  `MainWindow` constructs and every screen signal has a receiver.
- Scale: 15–30 check-ins/day, local SQLite. **No new abstractions** are
  justified. Everything lands in the four existing coordinators.

## Phases

Each phase is independently committable and revertable, and each is executed
under `/ponytail:ponytail` (laziest solution that works — reuse the existing
coordinators, delete over add).

### Phase 0 — Safety net

Add `tests/test_main_window_smoke.py`. With `QT_QPA_PLATFORM=offscreen`:
- Construct a `QApplication` + `MainWindow`.
- Assert the four coordinators are instantiated.
- Assert every screen signal that the app wires has at least one connected
  receiver (via `QObject.receivers(...)` or by asserting the connect calls
  don't raise). One test, no per-method UI suite (`ponytail:` smoke only —
  add finer UI tests only if a regression proves they're needed).

Exit: new test passes; existing suite still green.

### Phase 1 — Delete the shim layer

- Remove the ~40 forwarding-only methods in `main_window.py` (the ones whose
  body is a single `self.<x>_coordinator.foo(...)` call).
- In `_connect_screen_signals`, connect each screen signal **directly** to the
  coordinator method (e.g.
  `self.member_search_screen.edit_button.clicked.connect(self.members_coordinator.on_edit_member_clicked)`).
- Keep `_update_dashboard` and `_show_members_list` (called by coordinators).
- Handle the two `request_delete_checkin` / `request_edit_checkin` method
  reassignments (lines 416–418) by pointing them at the coordinator directly.

Exit: smoke + service tests green. Expect ~250 fewer lines.

### Phase 2 — Move the two embedded flows into existing coordinators

- **Financeiro** → `ReportsCoordinator` (default; only create a separate
  `FinancialCoordinator` if Reports genuinely becomes awkward — decide at
  implementation, do not pre-commit to a new file). Move the four financial
  methods; rewire `financial_screen.update_button` /
  `plan_chart_button` signals to the coordinator.
- **Aniversariantes** → `MembersCoordinator` (birthdays already live under the
  Members submenu). Move the two methods incl. the HTML-building via
  `self.window.formatter`; rewire `aniversariantes_screen.search_button`.

Exit: `main_window.py` holds no financial or HTML-building logic. Tests green.

### Phase 3 — Extract UI construction

- Move the `_setup_ui` body (title bar + sidebar + stacked widget assembly)
  into `src/ui/main_window_ui.py` as a free function `build_ui(window)` that
  sets the same attributes on `window` it does today. No new class unless the
  function is clearly worse (`ponytail:` prefer a function over a `_UiBuilder`).
- `_connect_sidebar_signals` / `_connect_screen_signals` **stay on the window**
  (they reference coordinators and screen attributes the window owns).
- `MainWindow.__init__` calls `build_ui(self)` where it called `_setup_ui()`.

Exit: `main_window.py` is a thin shell (~400 lines target); tests green.

### Phase 4 — Doc reconciliation

Update `.claude/docs/ARCHITECTURE.md`:
- Fix the stale `~1700 linhas` → actual post-refactor count.
- Move "MainWindow como God Object" from *Dívida Técnica Conhecida* to a
  resolved note, mirroring the existing "Resolvido em 2026-08-15" precedent.
- Note the new `main_window_ui.py` and the relocated financial/aniversariantes
  flows.

## Out of scope (deliberately)

- The coordinator↔window coupling (coordinators reaching into
  `window.screen.input`). Real smell, but fixing it is a much larger diff for a
  15–30/day app. Left as-is per the confirmed scope.
- Any MVC/MVP/MVVM restructuring.
- The `_show_manage_plans_dialog` double-wiring (financial + settings submenus
  both point at it) and its misleading name — note if it falls out of Phase 1,
  don't chase it.
