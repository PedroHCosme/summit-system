# Post-Audit Dead File Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete two orphaned docs and 20 standalone scripts left dangling after the 2026-08-15 ponytail-audit cleanup — all of them import the now-deleted `DatabaseManager` class (or document a script that does) and are unreachable from the running app or the pytest suite — plus fix the two still-live docs whose content becomes stale once those files are gone.

**Architecture:** Pure deletion, no code changes. Each file gets a fresh re-grep confirmation immediately before deletion (guards against drift since this plan was written), then a `git rm`. No new abstractions, no refactoring.

**Tech Stack:** Python. Windows dev machine (PowerShell primary, git-bash available).

**Verified before this plan was written, then corrected during plan review:** none of the files in scope are imported by any other file in the repo (confirmed via repo-wide grep for each filename/module name — the one apparent hit, `migrate_data` inside `scripts/fix_database_critical.py`, is a false positive from `migrate_database` containing `migrate_data` as a substring, not an actual import). `docs/MANAGE_PLANS_DIALOG.md` has zero references anywhere else in the repo except this plan and its spec.

**Two corrections from plan review (not caught when the spec was written):**
1. `scripts/test_plan_distribution.py` — originally listed in Group A, but it does NOT import `DatabaseManager`. It imports `FinancialGraphsDialog` from `src/ui/dialogs/finance_graphs.py`, a class that still exists and is used live by `main_window.py`. **Removed from scope** — this is a working manual smoke-test script, not dead code.
2. `docs/MIGRATION_GUIDE.md` — a second orphaned doc, missed when the spec was written. It's a full user guide for `scripts/migrate_data.py` (being deleted in Task 2), including a code example that directly imports the deleted `DatabaseManager`. Same situation as `MANAGE_PLANS_DIALOG.md`: a whole doc about something that's about to stop existing. **Added to Task 1's deletion list.**

This also surfaced a **doc-staleness cascade**: two still-live docs (`docs/SYNC_IMPROVEMENTS.md`, `docs/SYNC_UI_GUIDE.md`) document the still-live Sync UI feature but contain sub-sections and command examples specifically about the CLI script being deleted here, and `.claude/docs/ARCHITECTURE.md`'s tech-debt list (written during the prior cleanup) describes these files as "present but broken" — which becomes wrong once they're deleted. Task 3 below fixes this.

**Spec:** `docs/superpowers/specs/2026-08-17-post-audit-dead-file-cleanup-design.md`

---

## Task 1: Delete the orphaned docs and Group A (one-off debug/verification scripts)

**Files to delete (17 total):**
- `docs/MANAGE_PLANS_DIALOG.md`
- `docs/MIGRATION_GUIDE.md`
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

**Not in scope (found during plan review, do not delete):** `scripts/test_plan_distribution.py` — imports `FinancialGraphsDialog`, not `DatabaseManager`; it's a working smoke-test script for a dialog that still exists.

- [ ] **Step 1: Re-confirm each script still imports the deleted `DatabaseManager`**

```bash
grep -l "DatabaseManager" debug_config.py debug_sync.py reproduce_checkin.py \
  verification_voucher.py verify_approval.py verify_profession.py \
  verify_web_expiration.py test_duplicate_payment.py \
  examples/transaction_usage.py tests/validate_improvements.py \
  scripts/validate_critical_fixes.py scripts/verify_update_fields.py \
  scripts/test_payment_system.py scripts/test_financial_integration.py \
  scripts/test_checkin_payment.py
```
Expected: all 15 filenames printed back (each one matches). If any filename is *missing* from the output, STOP — that file no longer references the deleted class and needs separate investigation before deleting (it may have been fixed or repurposed since this plan was written). This is exactly what happened with `scripts/test_plan_distribution.py` during plan review — it's already been removed from this list, but treat any other surprise the same way: stop, don't guess.

- [ ] **Step 2: Confirm both docs have no other references**

```bash
grep -rln "MANAGE_PLANS_DIALOG" . --include=*.md --include=*.py
grep -rln "MIGRATION_GUIDE" . --include=*.md --include=*.py
```
Expected for the first: `docs/superpowers/plans/2026-08-17-post-audit-dead-file-cleanup.md` (this plan) and `docs/superpowers/specs/2026-08-17-post-audit-dead-file-cleanup-design.md` (its spec). Note neither this plan nor the file's own body contains the literal string as a self-match — `docs/MANAGE_PLANS_DIALOG.md` itself won't appear in this list.

Expected for the second: this plan file, plus three already-out-of-scope historical docs that mention `MIGRATION_GUIDE.md` in passing — `docs/CHANGELOG_2025-11-11.md`, `docs/IMPROVEMENTS_SUMMARY.md`, `docs/SYNC_IMPROVEMENTS.md` (all three are dated records, explicitly not touched by this plan — see "Out of scope" below). If anything else *beyond these four* shows up, STOP and report before deleting.

- [ ] **Step 3: Delete all 17 files**

```bash
git rm docs/MANAGE_PLANS_DIALOG.md docs/MIGRATION_GUIDE.md debug_config.py \
  debug_sync.py reproduce_checkin.py verification_voucher.py verify_approval.py \
  verify_profession.py verify_web_expiration.py test_duplicate_payment.py \
  examples/transaction_usage.py tests/validate_improvements.py \
  scripts/validate_critical_fixes.py scripts/verify_update_fields.py \
  scripts/test_payment_system.py scripts/test_financial_integration.py \
  scripts/test_checkin_payment.py
```

- [ ] **Step 4: Run the full test suite**

```bash
python -m pytest test_reports_jinja.py tests/ -q
```
Expected: `97 passed`. None of the deleted files were part of this suite (`tests/validate_improvements.py` doesn't match pytest's `test_*.py` discovery pattern per `pytest.ini`'s `testpaths = tests`), so this run should be identical to before — if the count or any failure differs from `97 passed`, STOP and investigate before committing (something depended on one of these files in a way this plan's verification missed).

- [ ] **Step 5: Commit**

```bash
git commit -m "Delete orphaned docs and one-off debug/verification scripts

docs/MANAGE_PLANS_DIALOG.md and docs/MIGRATION_GUIDE.md document files
already deleted; the 15 scripts import the DatabaseManager class deleted
in the prior ponytail-audit cleanup. None are part of the running app or
the pytest suite."
```

---

## Task 2: Delete Group B (historical data-migration scripts)

**Files to delete (5 total):**
- `src/migrate_data.py`
- `scripts/migrate_data.py`
- `scripts/migrate_historical_payments.py`
- `src/data/migration_tasks/backfill_payments.py`
- `scripts/clear_payments.py`

- [ ] **Step 1: Re-confirm each script still imports the deleted `DatabaseManager`**

```bash
grep -l "DatabaseManager" src/migrate_data.py scripts/migrate_data.py \
  scripts/migrate_historical_payments.py \
  src/data/migration_tasks/backfill_payments.py scripts/clear_payments.py
```
Expected: all 5 filenames printed back. Same stop condition as Task 1 Step 1 if any is missing.

- [ ] **Step 2: Confirm none of the 5 are imported elsewhere**

```bash
grep -rn "migration_tasks.backfill_payments\|from src.migrate_data\|from scripts.migrate_data\|from scripts.migrate_historical_payments\|from scripts.clear_payments" --include=*.py .
```
Expected: no output. If anything shows up, STOP — one of these is a real dependency, not a leaf, and needs separate investigation.

- [ ] **Step 3: Delete all 5 files**

```bash
git rm src/migrate_data.py scripts/migrate_data.py \
  scripts/migrate_historical_payments.py \
  src/data/migration_tasks/backfill_payments.py scripts/clear_payments.py
```

Note: `src/data/migration_tasks/backfill_payments.py` is the only file inside
`src/data/migration_tasks/`. After deleting it, check whether
`src/data/migration_tasks/__init__.py` (an empty file) is now an empty,
purposeless package directory:
```bash
ls src/data/migration_tasks/
```
If `__init__.py` is the only remaining file in that directory, delete it and
the now-empty directory too (`git rm src/data/migration_tasks/__init__.py`) —
an empty package with nothing in it is exactly the kind of leftover this
cleanup is for. If anything else remains in that directory, leave it alone.

- [ ] **Step 4: Run the full test suite**

```bash
python -m pytest test_reports_jinja.py tests/ -q
```
Expected: `97 passed`, same as Task 1 Step 4.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Delete historical data-migration scripts

All import the DatabaseManager class deleted in the prior ponytail-audit
cleanup; each already ran once against production data with nothing left
to migrate. If similar migration is needed again, it should be written
fresh against the current MemberService/PaymentService architecture."
```

---

## Task 3: Fix the doc-staleness cascade from Tasks 1 and 2

Deleting `scripts/migrate_data.py` and `database_manager.py`'s former
callers leaves three still-live docs with now-inaccurate content: two
sub-sections in `docs/SYNC_UI_GUIDE.md` (a genuinely current user guide for
the still-live Sync UI feature) instruct a reader to run a script that no
longer exists, and `.claude/docs/ARCHITECTURE.md`'s tech-debt list
(required pre-reading per this repo's `CLAUDE.md`) describes these files as
"present but broken" rather than deleted.

**`docs/SYNC_IMPROVEMENTS.md` is explicitly NOT touched** — despite also
referencing `scripts/migrate_data.py` extensively, it reads as a dated
"what we shipped" announcement doc (🎉 headers, a "Conclusão" section, a
"Próximos Passos Sugeridos" wishlist from the time it was written), the
same genre as `docs/CHANGELOG_2025-11-11.md`/`docs/IMPROVEMENTS_SUMMARY.md`
which are already out of scope. Treat it the same way: a historical record,
not living documentation.

**Files:**
- Modify: `docs/SYNC_UI_GUIDE.md`
- Modify: `.claude/docs/ARCHITECTURE.md`

- [ ] **Step 1: Remove the two script-usage subsections from `SYNC_UI_GUIDE.md`'s "🔄 Sincronização vs. Migração Completa" section**

Current:
```markdown
## 🔄 Sincronização vs. Migração Completa

### Sincronização (via UI)
- ✅ Preserva todos os dados existentes
- ✅ Adiciona apenas novos registros
- ✅ Interface visual com progresso
- ✅ Ideal para uso frequente
- ⚠️ Modo apenas incremental

### Migração Completa (via script)
```bash
python scripts/migrate_data.py
```
- ⚠️ **APAGA** todos os dados existentes
- ✅ Recria o banco do zero
- ✅ Ideal para reset completo
- ❌ Perde dados locais não sincronizados

### Migração Incremental (via script)
```bash
python scripts/migrate_data.py --append
```
- ✅ Mesma funcionalidade da sincronização UI
- ✅ Pode ser agendada (cron/task scheduler)
- ❌ Sem interface visual
- ✅ Ideal para automação
```

Replace with:
```markdown
## 🔄 Sincronização via UI

- ✅ Preserva todos os dados existentes
- ✅ Adiciona apenas novos registros
- ✅ Interface visual com progresso
- ✅ Ideal para uso frequente e para automação futura

> O script de linha de comando (`scripts/migrate_data.py`) que antes
> oferecia um modo alternativo de migração foi removido em 2026-08-17 por
> não ter mais uso — a sincronização via UI é hoje o único caminho
> suportado.
```

- [ ] **Step 2: Fix the troubleshooting step in `SYNC_UI_GUIDE.md`'s "🆘 Suporte" section**

Current:
```markdown
## 🆘 Suporte

Em caso de problemas não cobertos neste guia:

1. **Verifique o log de atividades** no próprio diálogo
2. **Consulte os logs do console** da aplicação
3. **Tente executar o script direto**:
   ```bash
   python scripts/migrate_data.py --append
   ```
4. **Reporte o erro** com o log completo para análise
```

Replace with:
```markdown
## 🆘 Suporte

Em caso de problemas não cobertos neste guia:

1. **Verifique o log de atividades** no próprio diálogo
2. **Consulte os logs do console** da aplicação
3. **Reporte o erro** com o log completo para análise
```

- [ ] **Step 3: Verify no other `scripts/migrate_data.py` references remain in `SYNC_UI_GUIDE.md`**

```bash
grep -n "migrate_data" docs/SYNC_UI_GUIDE.md
```
Expected: no output.

- [ ] **Step 4: Update `.claude/docs/ARCHITECTURE.md`'s tech-debt list**

Current (`.claude/docs/ARCHITECTURE.md`, in the "Divida Tecnica Conhecida" list):
```markdown
5. **Scripts standalone quebrados por remocao do DatabaseManager** — `debug_config.py`, `debug_sync.py`, `examples/transaction_usage.py`, `reproduce_checkin.py`, `verification_voucher.py`, `verify_approval.py`, `verify_profession.py`, `verify_web_expiration.py`, `test_duplicate_payment.py`, `tests/validate_improvements.py`, `scripts/migrate_data.py` (raiz), `src/migrate_data.py`, `src/data/migration_tasks/backfill_payments.py` e mais alguns arquivos em `scripts/` ainda importam `src.data.database_manager.DatabaseManager`, que foi deletado (ver "Limpeza ponytail-audit" abaixo). Nenhum e coletado pelo pytest (`pytest.ini`: `testpaths = tests`) nem importado pelo app rodando — sao scripts de debug/verificacao pontuais que um dev roda manualmente. Se for rodar algum deles, espere um `ModuleNotFoundError` ate serem atualizados (ou deletados, ja que a maioria descreve verificacoes de bugs ja corrigidos).
```

Delete that bullet entirely from the numbered tech-debt list (renumbering
the remaining items isn't necessary — Markdown renders ordered lists by
position regardless of the literal numbers typed, but if you want to keep
the source tidy, renumber the following item from `4` to stay sequential;
either is fine, don't spend time on it).

Then add a new bullet to the "Resolvido em 2026-08-15 — Limpeza
ponytail-audit" section's list (which already documents the 5 deletions
from that cleanup), so the resolution history stays complete:
```markdown
- 17 scripts standalone e 2 docs orfaos que so importavam o `DatabaseManager` deletado — **deletados** em 2026-08-17 (ver `docs/superpowers/plans/2026-08-17-post-audit-dead-file-cleanup.md`), incluindo `docs/MANAGE_PLANS_DIALOG.md` e `docs/MIGRATION_GUIDE.md`.
```

- [ ] **Step 5: Verify no other stray references to the deleted docs remain**

```bash
grep -rln "MIGRATION_GUIDE\|MANAGE_PLANS_DIALOG" . --include=*.md --include=*.py
```
Expected: this plan file, its spec, and three already-out-of-scope historical docs that mention `MIGRATION_GUIDE.md` — `docs/CHANGELOG_2025-11-11.md`, `docs/IMPROVEMENTS_SUMMARY.md`, `docs/SYNC_IMPROVEMENTS.md` (the last one still links to `MIGRATION_GUIDE.md` in its own "📖 Documentação" section — fine to leave as a dead link in a historical record). `docs/SYNC_UI_GUIDE.md` should NOT appear (Steps 1-3 above already removed its only reference). If anything else beyond these five shows up, investigate before committing.

- [ ] **Step 6: Commit**

```bash
git add docs/SYNC_UI_GUIDE.md .claude/docs/ARCHITECTURE.md
git commit -m "Fix doc-staleness cascade from Tasks 1-2's deletions

SYNC_UI_GUIDE.md's two script-usage sections instructed readers to run
scripts/migrate_data.py, which no longer exists. ARCHITECTURE.md's
tech-debt list described the deleted files as present-but-broken rather
than deleted. SYNC_IMPROVEMENTS.md deliberately left untouched — it's a
dated announcement doc, same treatment as CHANGELOG_2025-11-11.md."
```

---

## Out of scope

- `.claude/docs/ARCHITECTURE_BASELINE.md`, `docs/CHANGELOG_2025-11-11.md`,
  `docs/CRITICAL_FIXES.md`, `docs/DATABASE_AUDIT_REPORT.md`,
  `docs/IMPROVEMENTS_SUMMARY.md`, `docs/SYNC_IMPROVEMENTS.md` — dated
  historical records, not touched.
- `scripts/fix_database_critical.py` — contains a function named
  `migrate_database()` (an unrelated false-positive grep match on
  `migrate_data`, verified in this plan's header) — not in scope, not
  touched, and does not import `DatabaseManager` (verify this if in doubt
  before touching anything in `scripts/` beyond the 5 files named above).
- Any further ponytail-style cleanup (the `MainWindow` God Object, etc.) —
  deferred to a separate cycle per the spec.
