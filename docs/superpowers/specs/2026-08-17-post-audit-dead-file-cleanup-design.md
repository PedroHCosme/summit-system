# Post-Audit Dead File Cleanup — Design

## Context

The 2026-08-15 ponytail-audit cleanup (`docs/superpowers/plans/2026-08-15-ponytail-audit-cleanup.md`)
deleted `database_manager.py`, `manage_plans_dialog.py`, and `member_search_service.py`,
after migrating their live callers. Its final review surfaced a second wave of
now-dead artifacts that were out of scope for that plan but are ready to clean
up on their own: one orphaned doc file, and 21 standalone scripts that only
ever imported the now-deleted `DatabaseManager` class.

None of this affects the running app (desktop or web) or the collected pytest
suite (`pytest.ini`: `testpaths = tests`) — every file in scope here is either
documentation or a script a developer runs by hand.

## Scope

### 1. Orphaned documentation (1 file)

- `docs/MANAGE_PLANS_DIALOG.md` — an entire document describing how to use
  `manage_plans_dialog.py`, which no longer exists (deleted in the prior
  audit's Phase 2). No historical/changelog value; it's a usage guide for a
  screen that isn't there anymore. Delete.

### 2. Scripts that import the deleted `DatabaseManager` (21 files)

All of the following currently fail with `ModuleNotFoundError` if run, since
they `import`/`from ... import DatabaseManager` and that module was deleted.
None are part of the running app or the pytest-collected suite.

**Group A — one-off debug/verification scripts** (named after a specific,
already-resolved historical bug; no ongoing operational value):
- `debug_config.py`
- `debug_sync.py`
- `reproduce_checkin.py`
- `verification_voucher.py`
- `verify_approval.py`
- `verify_profession.py`
- `verify_web_expiration.py`
- `test_duplicate_payment.py`
- `examples/transaction_usage.py`
- `tests/validate_improvements.py`
- `scripts/validate_critical_fixes.py`
- `scripts/verify_update_fields.py`
- `scripts/test_payment_system.py`
- `scripts/test_financial_integration.py`
- `scripts/test_checkin_payment.py`
- `scripts/test_plan_distribution.py`

**Group B — one-time historical data migration scripts** (already run once
against production data; nothing pending to migrate today):
- `src/migrate_data.py`
- `scripts/migrate_data.py`
- `scripts/migrate_historical_payments.py`
- `src/data/migration_tasks/backfill_payments.py`
- `scripts/clear_payments.py`

Both groups are deleted outright — the user confirmed no future need to
resurrect the migration logic in Group B; if a similar migration is ever
needed again, it'll be written fresh against the current `MemberService`/
`PaymentService` architecture rather than resurrecting code built against a
deleted legacy class.

## Verification approach

Unlike the prior audit (which touched live, imported code), this cleanup
touches only standalone/doc files, so the verification bar is lower but not
zero:

1. **Per-file confirmation before deletion** — re-grep each file at deletion
   time to confirm it still imports the deleted `DatabaseManager` (guards
   against drift since the list above was built) and that nothing else in
   the repo imports *it* (i.e., these are leaves, not depended upon by any
   other file, script, or test).
2. **Full test suite** (`pytest test_reports_jinja.py tests/ -q`, expect
   97 passed) run after all deletions — confirms nothing collected by pytest
   silently depended on any of these files.
3. **Repo-wide grep** for `docs/MANAGE_PLANS_DIALOG.md`'s filename and for
   each deleted script's filename, to catch any stray reference (a README
   listing, a comment pointing at one of these scripts) — informational only,
   doesn't block deletion, but worth surfacing if found.

No manual smoke test needed — nothing in the running desktop or web app
touches any of these 22 files.

## Out of scope

- `.claude/docs/ARCHITECTURE_BASELINE.md`, `docs/CHANGELOG_2025-11-11.md`,
  `docs/CRITICAL_FIXES.md`, `docs/DATABASE_AUDIT_REPORT.md`,
  `docs/IMPROVEMENTS_SUMMARY.md` — dated historical records that happen to
  mention now-deleted files, not living documentation. Same treatment as
  `ARCHITECTURE_BASELINE.md` got in the prior audit: left alone.
- Rewriting or preserving any of the Group B migration logic — confirmed
  not needed.
- Any further ponytail-style cleanup (the `MainWindow` God Object, etc.) —
  explicitly deferred to a separate, larger brainstorm/plan cycle.
