# Resumo Semanal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Um relatorio HTML de tela unica, o Resumo Semanal, que mostra ao dono da Summit quanto do movimento e Gym/Totalpass, quanto isso rende, onde lota, quem converter e quem cobrar.

**Architecture:** O check-in passa a gravar o proprio plano (`frequencia.plano`, ADR 0001), com migracao Alembic e backfill. Um modulo Python puro (`src/reports/weekly_summary.py`) le todo o historico e monta 12 Semanas como dicts. Um template Jinja (Chart.js via CDN, como os relatorios atuais) embute esses dados como JSON e navega entre as Semanas com JS. Um script gera um banco simulado para testar tudo.

**Tech Stack:** Python 3, SQLAlchemy 2, Alembic, Jinja2, Chart.js (CDN), PyQt6, pytest.

**Leia antes:** `CONTEXT.md` (glossario), `docs/adr/0001-tipo-do-checkin-gravado-no-checkin.md`, `docs/superpowers/specs/2026-09-28-resumo-semanal-design.md`.

**Comandos (Git Bash):**
- Python: `/c/Users/Usuario/.conda/envs/alcoa/python.exe` (abaixo, `PY`)
- Testes: `PY -m pytest <arquivo> -v`, a partir da raiz do repo
- Commit: `git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "..."`. Toda mensagem termina com a linha `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

**Linha de base:** 5 testes em `tests/test_web_checkin.py` ja falham por causa de CSRF, antes deste plano (ha uma tarefa separada para isso). Todo o resto (101) passa. "Suite verde" neste plano significa: nenhuma falha alem dessas 5.

---

## Mapa de arquivos

| Arquivo | Acao | Responsabilidade |
|---|---|---|
| `src/data/db.py` | Modificar | `SUMMIT_DB_PATH` aponta o app (e o Alembic) para outro banco |
| `src/core/plan_utils.py` | Modificar | `categoria_do_plano()` e as constantes de Categoria de Cliente |
| `src/data/models.py` | Modificar | coluna `Frequencia.plano` |
| `alembic_migrations/versions/c4a1e9d7b2f3_tipo_do_checkin.py` | Criar | adiciona a coluna e faz o backfill |
| `src/services/checkin_service.py` | Modificar | grava `plano` em cada check-in novo |
| `src/reports/frequency_report.py` | Modificar | tabela "por plano" agrupada pelo Tipo do Check-in |
| `scripts/seed_demo_db.py` | Criar | gera `demo_database.db` simulado, nunca o banco real |
| `src/reports/weekly_summary.py` | Criar | calcula as 12 Semanas e gera o HTML |
| `src/templates/reports/weekly_summary.html` | Criar | tela do Resumo Semanal |
| `src/ui/components/sidebar.py` | Modificar | botoes "Resumo Semanal" e "Frequencia" |
| `src/ui/main_window.py` | Modificar | liga os botoes e o aviso de segunda |
| `src/ui/coordinators/reports_coordinator.py` | Modificar | abre o Resumo e faz o aviso de segunda |
| `tests/test_db_path.py`, `tests/test_plan_category.py`, `tests/test_migration_tipo_do_checkin.py`, `tests/test_frequency_report_tipo.py`, `tests/test_weekly_summary.py` | Criar | testes |
| `tests/test_checkin.py` | Modificar | teste do `plano` gravado |
| `.claude/docs/DATA_DICTIONARY.md`, `.claude/docs/REPORTS_STATUS.md` | Modificar | documentacao |

---

### Task 0: Branch

- [ ] **Step 1: Criar a branch a partir de `dev`**

```bash
git checkout dev && git checkout -b feat/resumo-semanal
```

- [ ] **Step 2: Commitar os documentos de design** (hoje estao fora do git)

```bash
git add CONTEXT.md docs/adr/0001-tipo-do-checkin-gravado-no-checkin.md docs/superpowers/specs/2026-09-28-resumo-semanal-design.md docs/superpowers/plans/2026-09-28-resumo-semanal.md
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Docs: glossario, ADR 0001, spec e plano do Resumo Semanal

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 1: `SUMMIT_DB_PATH`

Hoje nada em `src/` le variavel de ambiente para escolher o banco (o `SUMMIT_DB_URL` em `test_reports_jinja.py` e ignorado). O `alembic_migrations/env.py` chama `get_database_url()`, entao uma mudanca so aqui cobre o app, os relatorios e as migracoes.

**Excecao conhecida:** Backup e Otimizar (`src/ui/coordinators/settings_coordinator.py`) e a sincronizacao com Sheets (`legacy_sync_gateway.py`) montam o caminho direto com `DB_FILENAME`. Mesmo com o banco simulado ativo, eles continuam agindo no banco real. Nao mexemos neles aqui; o aviso aparece na Task 9.

**Files:**
- Modify: `src/data/db.py:29-42`
- Test: `tests/test_db_path.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
from src.data.db import get_database_url


def test_summit_db_path_aponta_para_outro_banco(monkeypatch, tmp_path):
    destino = tmp_path / "demo_database.db"
    monkeypatch.setenv("SUMMIT_DB_PATH", str(destino))
    assert get_database_url() == f"sqlite:///{destino}"


def test_sem_variavel_usa_banco_padrao(monkeypatch):
    monkeypatch.delenv("SUMMIT_DB_PATH", raising=False)
    assert get_database_url().endswith("gym_database.db")
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PY -m pytest tests/test_db_path.py -v`
Expected: `test_summit_db_path_aponta_para_outro_banco` FAIL (a URL termina em `gym_database.db`).

- [ ] **Step 3: Implementar.** Em `get_database_url`, trocar o corpo do `if db_path is None:`:

```python
    if db_path is None:
        # SUMMIT_DB_PATH aponta o app para outro banco (ex.: demo_database.db)
        db_path = os.environ.get("SUMMIT_DB_PATH") or str(_DEFAULT_DB_PATH)
    return f"sqlite:///{db_path}"
```

(`os` ja esta importado em `db.py`.)

- [ ] **Step 4: Rodar e ver passar**

Run: `PY -m pytest tests/test_db_path.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/data/db.py tests/test_db_path.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Add SUMMIT_DB_PATH para apontar o app para outro banco

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Categoria de Cliente

**Files:**
- Modify: `src/core/plan_utils.py` (acrescentar ao final, e `import unicodedata` no topo)
- Test: `tests/test_plan_category.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
import pytest

from src.core.plan_utils import categoria_do_plano


@pytest.mark.parametrize("plano, categoria", [
    ("Gympass", "Gym/Totalpass"),
    ("Totalpass", "Gym/Totalpass"),
    ("Diária", "Avulso"),
    ("Diária Boulder", "Avulso"),
    ("Pacote 10", "Pacote"),
    ("Voucher", "Pacote"),
    ("Cortesia", "Sem Receita"),
    ("Livre", "Sem Receita"),
    ("Evento", "Sem Receita"),
    ("Airbnb", "Sem Receita"),
    ("Mensal", "Assinante"),
    ("Mens. c/ Treino", "Assinante"),
    ("Trimestral", "Assinante"),
    ("Semestral", "Assinante"),
    ("Anual", "Assinante"),
    ("Escolinha 2x", "Assinante"),
    ("Plano Inventado", "Outros"),
    (None, "Outros"),
    ("", "Outros"),
])
def test_categoria_do_plano(plano, categoria):
    assert categoria_do_plano(plano) == categoria
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PY -m pytest tests/test_plan_category.py -v`
Expected: ERROR `ImportError: cannot import name 'categoria_do_plano'`

- [ ] **Step 3: Implementar.** Adicionar `import unicodedata` junto ao `from typing import Optional` e acrescentar ao final de `src/core/plan_utils.py`:

```python
# Categorias de Cliente (ver CONTEXT.md)
ASSINANTE = "Assinante"
PACOTE = "Pacote"
AVULSO = "Avulso"
GYM_TOTALPASS = "Gym/Totalpass"
SEM_RECEITA = "Sem Receita"
OUTROS = "Outros"
CATEGORIAS = (ASSINANTE, PACOTE, AVULSO, GYM_TOTALPASS, SEM_RECEITA, OUTROS)

# ponytail: classifica por prefixo do nome; vira coluna em `planos` se o dono passar a criar planos novos com frequencia
_PREFIXOS_POR_CATEGORIA = (
    (("gympass", "totalpass"), GYM_TOTALPASS),
    (("diaria",), AVULSO),
    (("pacote", "voucher"), PACOTE),
    (("cortesia", "livre", "evento", "airbnb"), SEM_RECEITA),
    (("mensal", "mens.", "trimestral", "semestral", "anual", "escolinha"), ASSINANTE),
)


def categoria_do_plano(plan_name: Optional[str]) -> str:
    """Categoria de Cliente de um plano, pelo nome (sem acento e sem caixa)."""
    nome = unicodedata.normalize("NFD", plan_name or "")
    nome = "".join(c for c in nome if unicodedata.category(c) != "Mn").strip().lower()
    for prefixos, categoria in _PREFIXOS_POR_CATEGORIA:
        if nome.startswith(prefixos):
            return categoria
    return OUTROS
```

- [ ] **Step 4: Rodar e ver passar**

Run: `PY -m pytest tests/test_plan_category.py -v`
Expected: 19 passed

- [ ] **Step 5: Commit**

```bash
git add src/core/plan_utils.py tests/test_plan_category.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Add categoria_do_plano com as Categorias de Cliente

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Coluna `frequencia.plano` + migracao com backfill

Regras (ADR 0001):
1. Se houver pagamento per-checkin (Gympass, Totalpass, Diaria, Diaria Boulder) do mesmo membro no mesmo dia, o tipo do pagamento vira o plano.
2. Senao, vale o plano atual do membro.

**Cuidado 1:** nao usar `op.batch_alter_table` aqui. No SQLite ele recria a tabela e perde o indice por expressao `uq_frequencia_member_day`. `ADD COLUMN` direto funciona no SQLite.

**Cuidado 2:** num banco novo, `init_db()` (`create_all`) ja cria a coluna. A migracao precisa checar se ela existe antes de adicionar.

**Cuidado 3:** o backfill roda uma vez, na primeira abertura do app depois da atualizacao (`run.py` e o worker de conexao ja fazem `alembic upgrade head`). E uma subquery correlacionada sem indice em `pagamentos.member_id`, entao no banco real pode levar alguns segundos. Isso e esperado; avise o dono que a primeira abertura vai demorar um pouco mais.

**Files:**
- Modify: `src/data/models.py:117-148` (classe `Frequencia`)
- Create: `alembic_migrations/versions/c4a1e9d7b2f3_tipo_do_checkin.py`
- Test: `tests/test_migration_tipo_do_checkin.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

from src.data.models import Base

ROOT = Path(__file__).resolve().parent.parent


def _alembic_cfg():
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic_migrations"))
    return cfg


def test_backfill_usa_pagamento_do_dia_e_senao_plano_atual(tmp_path, monkeypatch):
    db = tmp_path / "antigo.db"
    monkeypatch.setenv("SUMMIT_DB_PATH", str(db))
    Base.metadata.create_all(create_engine(f"sqlite:///{db}"))
    con = sqlite3.connect(db)
    con.execute("ALTER TABLE frequencia DROP COLUMN plano")  # esquema de antes do ADR 0001
    con.executescript("""
        INSERT INTO membros (id, nome, plano, voucher_credits) VALUES (1, 'Ana', 'Mensal', 0);
        INSERT INTO frequencia (id, member_id, checkin_datetime) VALUES
            (1, 1, '2026-03-02 19:00:00'),
            (2, 1, '2026-04-06 19:00:00');
        INSERT INTO pagamentos (member_id, data_pagamento, tipo_transacao, valor, metodo_pagamento)
            VALUES (1, '2026-03-02 19:00:00', 'Gympass', 15, 'Check-in');
    """)
    con.commit()
    con.close()

    cfg = _alembic_cfg()
    command.stamp(cfg, "5e3b8f4d2a11")
    command.upgrade(cfg, "head")

    con = sqlite3.connect(db)
    linhas = con.execute("SELECT id, plano FROM frequencia ORDER BY id").fetchall()
    con.close()
    # 1: veio pelo Gympass (tem pagamento no dia); 2: sem pagamento, herda o plano atual
    assert linhas == [(1, "Gympass"), (2, "Mensal")]
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PY -m pytest tests/test_migration_tipo_do_checkin.py -v`
Expected: FAIL. O `DROP COLUMN plano` quebra com `no such column` porque o modelo ainda nao tem a coluna. Isso prova que o teste depende da mudanca.

- [ ] **Step 3: Adicionar a coluna ao modelo.** Em `Frequencia`, logo depois de `checkin_datetime`:

```python
    # Tipo do Check-in: plano do membro no momento do check-in (ADR 0001)
    plano: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
```

E em `Frequencia.to_dict()`, acrescentar `"plano": self.plano,` depois de `"checkin_datetime"`.

- [ ] **Step 4: Criar a migracao** `alembic_migrations/versions/c4a1e9d7b2f3_tipo_do_checkin.py`:

```python
"""Tipo do Check-in gravado no check-in (ADR 0001)

Revision ID: c4a1e9d7b2f3
Revises: 5e3b8f4d2a11
Create Date: 2026-09-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c4a1e9d7b2f3'
down_revision: Union[str, Sequence[str], None] = '5e3b8f4d2a11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ADD COLUMN direto: batch_alter_table recriaria a tabela e perderia uq_frequencia_member_day.
    # Banco novo ja nasce com a coluna (init_db/create_all).
    colunas = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("frequencia")}
    if "plano" not in colunas:
        op.add_column("frequencia", sa.Column("plano", sa.String(100), nullable=True))

    # Backfill: pagamento per-checkin do mesmo membro no mesmo dia; na falta, plano atual do membro.
    op.execute(
        """
        UPDATE frequencia
           SET plano = COALESCE(
               (SELECT p.tipo_transacao
                  FROM pagamentos p
                 WHERE p.member_id = frequencia.member_id
                   AND date(p.data_pagamento) = date(frequencia.checkin_datetime)
                   AND p.tipo_transacao IN ('Gympass', 'Totalpass', 'Diária', 'Diaria', 'Diária Boulder')
                 LIMIT 1),
               (SELECT m.plano FROM membros m WHERE m.id = frequencia.member_id)
           )
         WHERE plano IS NULL
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE frequencia DROP COLUMN plano")
```

- [ ] **Step 5: Rodar e ver passar**

Run: `PY -m pytest tests/test_migration_tipo_do_checkin.py -v`
Expected: 1 passed

- [ ] **Step 6: Rodar a suite inteira**

Run: `PY -m pytest -q`
Expected: so as 5 falhas de linha de base em `test_web_checkin.py`.

- [ ] **Step 7: Commit**

```bash
git add src/data/models.py alembic_migrations/versions/c4a1e9d7b2f3_tipo_do_checkin.py tests/test_migration_tipo_do_checkin.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Add frequencia.plano (Tipo do Check-in) com backfill

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: CheckinService grava o Tipo do Check-in

`Frequencia(...)` so e construido em `src/services/checkin_service.py:313`. Web, desktop e importacao passam todos por ali, via `perform_checkin` → `_perform_checkin_sqlalchemy`.

**Files:**
- Modify: `src/services/checkin_service.py:313-316`
- Test: `tests/test_checkin.py` (novo metodo na classe `TestCheckinFunctionality`)

- [ ] **Step 1: Escrever o teste que falha.** Adicionar dentro de `class TestCheckinFunctionality`:

```python
    def test_checkin_grava_tipo_do_checkin(self, checkin_service, member_service, db_session):
        member_id = member_service.create({"nome": "Tipo User", "plano": "Mensal"}).member_id

        result = checkin_service.perform_checkin(member_id)

        assert db_session.get(Frequencia, result.checkin_id).plano == "Mensal"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PY -m pytest tests/test_checkin.py::TestCheckinFunctionality::test_checkin_grava_tipo_do_checkin -v`
Expected: FAIL `assert None == 'Mensal'`

- [ ] **Step 3: Implementar**

```python
            new_checkin = Frequencia(
                member_id=member_id,
                checkin_datetime=checkin_datetime,
                plano=effective_plan,  # Tipo do Check-in (ADR 0001)
            )
```

- [ ] **Step 4: Rodar e ver passar**

Run: `PY -m pytest tests/test_checkin.py -v`
Expected: todos passam

- [ ] **Step 5: Commit**

```bash
git add src/services/checkin_service.py tests/test_checkin.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Grava o Tipo do Check-in em cada check-in novo

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Relatorio de Frequencia agrupa pelo Tipo do Check-in

**Files:**
- Modify: `src/reports/frequency_report.py:115-122`
- Test: `tests/test_frequency_report_tipo.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
from datetime import datetime, timedelta
from pathlib import Path

from src.data.models import Frequencia, Membro
from src.reports.frequency_report import generate_frequency_report


def test_tabela_por_plano_usa_tipo_do_checkin(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr("src.reports.frequency_report.get_reports_dir", lambda: tmp_path)
    ana = Membro(nome="Ana", plano="Mensal", estado_plano="ATIVO", voucher_credits=0)
    db_session.add(ana)
    db_session.flush()
    # Ana hoje e Mensal, mas este check-in foi pelo Gympass
    db_session.add(Frequencia(member_id=ana.id, checkin_datetime=datetime.now() - timedelta(days=1), plano="Gympass"))
    db_session.commit()

    html = Path(generate_frequency_report(db_session=db_session, days=7)).read_text(encoding="utf-8")

    assert "Gympass" in html
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PY -m pytest tests/test_frequency_report_tipo.py -v`
Expected: FAIL (`"Gympass" in html` e falso; a tabela mostra "Mensal").

- [ ] **Step 3: Implementar.** Trocar o bloco `# Frequência por Plano` (a query `plan_rows`) por:

```python
        # Frequência por Plano: pelo Tipo do Check-in (plano no momento), não pelo plano atual
        tipo_do_checkin = func.coalesce(Frequencia.plano, Membro.plano)
        plan_rows = db_session.query(
            tipo_do_checkin.label("plano"),
            func.count(Frequencia.id).label("total")
        ).join(Membro, Frequencia.member_id == Membro.id).filter(
            Frequencia.checkin_datetime >= start_date,
            Frequencia.checkin_datetime <= end_date
        ).group_by(tipo_do_checkin).order_by(desc("total")).all()
```

O laco seguinte (`for row in plan_rows: ... row.plano`) continua igual.

- [ ] **Step 4: Rodar e ver passar**

Run: `PY -m pytest tests/test_frequency_report_tipo.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/reports/frequency_report.py tests/test_frequency_report_tipo.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Relatorio de Frequencia agrupa pelo Tipo do Check-in

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Banco simulado (`scripts/seed_demo_db.py`)

O banco reproduz o caminho real:
1. Nasce no esquema antigo, sem `frequencia.plano`, com os check-ins antes de `MIGRACAO` (17/08/2026).
2. Roda a migracao da Task 3.
3. Grava os check-ins depois de `MIGRACAO` ja com `plano`, como o app novo faria.

O `membros.plano` gravado antes da migracao e o plano que o membro tinha em `MIGRACAO`, porque o backfill real roda nesse momento. Depois ele e atualizado para o plano final.

O fundo e aleatorio, com semente 42. Os cenarios plantados sao deterministicos e tem nomes fixos, para os testes da Task 7:
- **Candidatos**: 6 membros Gympass com 3 check-ins por semana (ter/qui/sab).
- **Conversoes**: 3 membros Gympass → Mensal em 13/07, 03/08 e 08/09. As duas primeiras sao antes da migracao e sao recuperadas pelos pagamentos.
- **Perdas**: 2 membros Mensal → Gympass em 31/08 e 22/09, os dois depois da migracao.
- **Vencidos**: 5 membros Mensal, com vencimento em 01/09 e vindo seg/qua/sex.
- **Domingo**: 1 membro Livre com check-in em 27/09.

O `.gitignore` ja tem `*.db`, entao o `demo_database.db` nunca entra no git. O Step 5 confirma isso.

**Files:**
- Create: `scripts/seed_demo_db.py`
- Test: `tests/test_weekly_summary.py` (so os dois primeiros testes nesta task)

- [ ] **Step 1: Escrever os testes que falham** em `tests/test_weekly_summary.py`:

```python
import importlib.util
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _seed():
    spec = importlib.util.spec_from_file_location("seed_demo_db", ROOT / "scripts" / "seed_demo_db.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def demo_db(tmp_path_factory):
    return _seed().gerar(tmp_path_factory.mktemp("demo") / "demo_database.db")


def test_recusa_gravar_no_banco_real(tmp_path):
    with pytest.raises(SystemExit):
        _seed().gerar(tmp_path / "gym_database.db")


def test_banco_simulado_tem_tipo_do_checkin_em_tudo(demo_db):
    con = sqlite3.connect(demo_db)
    total, sem_tipo = con.execute("SELECT count(*), sum(plano IS NULL) FROM frequencia").fetchone()
    con.close()
    assert total > 1500
    assert sem_tipo == 0
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PY -m pytest tests/test_weekly_summary.py -v`
Expected: ERROR `FileNotFoundError` (o script ainda nao existe).

- [ ] **Step 3: Criar `scripts/seed_demo_db.py`**

```python
"""Gera um banco SIMULADO (demo_database.db) para testar o Resumo Semanal.

Nunca grava no banco real. Uso, na raiz do repo:
    python scripts/seed_demo_db.py
    $env:SUMMIT_DB_PATH = "demo_database.db"; python run.py      # PowerShell
"""

from __future__ import annotations

import os
import random
import sqlite3
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402

from src.config import DB_FILENAME  # noqa: E402
from src.core.payment_constants import METODO_CHECKIN, METODO_PIX  # noqa: E402
from src.core.plan_utils import ASSINANTE, GYM_TOTALPASS, categoria_do_plano  # noqa: E402
from src.data.models import Base  # noqa: E402
from src.utils.utils import calculate_new_due_date  # noqa: E402

DEMO_PATH = ROOT / "demo_database.db"
HOJE = date(2026, 9, 28)        # segunda-feira: ultima Semana fechada = 21/09–26/09
INICIO = date(2026, 6, 8)       # 16 Semanas (12 navegaveis + 4 de historico)
FIM = date(2026, 9, 27)         # domingo excepcional com 1 check-in
MIGRACAO = date(2026, 8, 17)    # dia em que o app passou a gravar o Tipo do Check-in

# (nome, preco, valor_por_checkin, requer_vencimento, is_quota, quota_amount)
PLANOS = [
    ("Mensal", 190.0, 0.0, True, False, 0),
    ("Mens. c/ Treino", 280.0, 0.0, True, False, 0),
    ("Trimestral", 500.0, 0.0, True, False, 0),
    ("Semestral", 950.0, 0.0, True, False, 0),
    ("Anual", 1900.0, 0.0, True, False, 0),
    ("Escolinha 2x", 250.0, 0.0, True, False, 0),
    ("Diária", 0.0, 35.0, False, False, 0),
    ("Diária Boulder", 0.0, 35.0, False, False, 0),
    ("Gympass", 0.0, 15.0, False, False, 0),
    ("Totalpass", 0.0, 15.0, False, False, 0),
    ("Voucher", 300.0, 0.0, False, True, 10),
    ("Cortesia", 0.0, 0.0, False, False, 0),
    ("Livre", 0.0, 0.0, False, False, 0),
    ("Evento", 0.0, 0.0, False, False, 0),
]
PRECO = {p[0]: p[1] for p in PLANOS}
VALOR_POR_CHECKIN = {p[0]: p[2] for p in PLANOS if p[2]}

# Fundo aleatorio: (plano, quantidade de membros, visitas por semana)
PERFIS = [
    ("Gympass", 34, 1.4), ("Totalpass", 4, 1.2),
    ("Mensal", 20, 2.0), ("Mens. c/ Treino", 4, 2.5), ("Trimestral", 4, 2.0),
    ("Semestral", 2, 2.0), ("Anual", 3, 2.0), ("Escolinha 2x", 3, 2.0),
    ("Diária", 20, 0.3), ("Diária Boulder", 6, 0.3),
    ("Voucher", 8, 1.0),
    ("Cortesia", 2, 1.0), ("Livre", 3, 1.5), ("Evento", 2, 0.1),
]

# Cenarios plantados (nomes ficticios e fixos, usados nos testes)
CANDIDATOS = [("Alan Duarte", "Masculino"), ("Bela Nunes", "Feminino"), ("Cris Vale", "Feminino"),
              ("Duda Lobo", "Feminino"), ("Enzo Sales", "Masculino"), ("Flor Aguiar", "Feminino")]
CONVERSOES = [("Caio Moreira", "Masculino", date(2026, 7, 13)),
              ("Lia Fontes", "Feminino", date(2026, 8, 3)),
              ("Rui Teixeira", "Masculino", date(2026, 9, 8))]
PERDAS = [("Bia Campos", "Feminino", date(2026, 8, 31)),
          ("Davi Prado", "Masculino", date(2026, 9, 22))]
VENCIDOS = [("Elis Barros", "Feminino"), ("Ivo Leal", "Masculino"), ("Nina Paiva", "Feminino"),
            ("Otto Reis", "Masculino"), ("Tais Mota", "Feminino")]
DOMINGO = ("Gil Sampaio", "Masculino")

FEM = ["Ana", "Beatriz", "Camila", "Daniela", "Eduarda", "Fernanda", "Gabriela", "Helena", "Isabela",
       "Julia", "Larissa", "Mariana", "Natalia", "Paula", "Renata", "Sofia", "Tatiana", "Vitoria"]
MASC = ["Andre", "Bruno", "Carlos", "Diego", "Eduardo", "Felipe", "Gustavo", "Henrique", "Igor",
        "Joao", "Lucas", "Marcelo", "Nicolas", "Otavio", "Pedro", "Rafael", "Thiago", "Vinicius"]
SOBRENOMES = ["Silva", "Santos", "Oliveira", "Souza", "Lima", "Pereira", "Costa", "Rodrigues",
              "Almeida", "Nascimento", "Araujo", "Ribeiro", "Carvalho", "Gomes", "Martins", "Rocha"]

# Calibrado pelo banco real (dez/2025–jan/2026): picos 10h e 18–20h, terca e quinta mais cheias
HORAS_PESO = {8: 3, 9: 5, 10: 12, 11: 4, 12: 2, 16: 5, 17: 8, 18: 22, 19: 23, 20: 10, 21: 2}
HORAS_PESO_GT = {8: 2, 9: 4, 10: 16, 11: 3, 12: 2, 16: 4, 17: 7, 18: 20, 19: 30, 20: 9, 21: 1}
DIA_PESO = [0.9, 1.3, 0.9, 1.2, 0.8, 0.9]  # seg..sab


def _dias_de_treino(inicio: date, fim: date):
    d = inicio
    while d <= fim:
        if d.weekday() < 6:
            yield d
        d += timedelta(days=1)


def _alembic_upgrade(destino: Path) -> None:
    antes = os.environ.get("SUMMIT_DB_PATH")
    os.environ["SUMMIT_DB_PATH"] = str(destino)
    try:
        cfg = Config(str(ROOT / "alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "alembic_migrations"))
        command.stamp(cfg, "5e3b8f4d2a11")
        command.upgrade(cfg, "head")
    finally:
        if antes is None:
            os.environ.pop("SUMMIT_DB_PATH", None)
        else:
            os.environ["SUMMIT_DB_PATH"] = antes


def gerar(destino: Path = DEMO_PATH) -> Path:
    destino = Path(destino)
    if destino.name == DB_FILENAME:
        raise SystemExit(f"Recusado: '{destino}' tem o nome do banco real. O simulado e demo_database.db.")
    destino.unlink(missing_ok=True)
    rng = random.Random(42)

    membros, checkins, pagamentos = [], [], []
    nomes_usados = {n for n, *_ in CANDIDATOS + CONVERSOES + PERDAS + VENCIDOS + [DOMINGO]}

    def novo_membro(nome, genero, nasc, fases):
        mid = len(membros) + 1
        membros.append({"id": mid, "nome": nome, "genero": genero, "nasc": nasc, "fases": fases,
                        "whatsapp": f"(00) 9{mid:04d}-{mid:04d}", "vencimento": None, "creditos": 0})
        return membros[-1]

    def plano_em(m, d):
        return [plano for inicio, plano in m["fases"] if inicio <= d][-1]

    def nasc_aleatorio(ano_min, ano_max):
        return date(rng.randint(ano_min, ano_max), rng.randint(1, 12), rng.randint(1, 28))

    def checkin(m, d):
        plano = plano_em(m, d)
        pesos = HORAS_PESO_GT if categoria_do_plano(plano) == GYM_TOTALPASS else HORAS_PESO
        hora = rng.choices(list(pesos), weights=list(pesos.values()))[0]
        dt = datetime.combine(d, time(hora, rng.randrange(60)))
        checkins.append((m["id"], dt, plano))
        if plano in VALOR_POR_CHECKIN:  # como o app: pagamento automatico por check-in
            pagamentos.append((m["id"], dt, plano, VALOR_POR_CHECKIN[plano], METODO_CHECKIN, None))

    def fixo(m, dias_semana, desde=INICIO, ate=FIM):
        for d in _dias_de_treino(desde, ate):
            if d.weekday() in dias_semana:
                checkin(m, d)

    def renovar(m, plano, desde, ate):
        d = desde
        while d < ate:
            vence = calculate_new_due_date(plano, datetime.combine(d, time(10))).date()
            pagamentos.append((m["id"], datetime.combine(d, time(10)), "Renovação Plano",
                               PRECO[plano], METODO_PIX, vence))
            m["vencimento"], d = vence, vence

    # --- Fundo aleatorio ---
    for plano, quantidade, por_semana in PERFIS:
        categoria = categoria_do_plano(plano)
        anos = (1995, 2006) if categoria == GYM_TOTALPASS else (2012, 2016) if plano.startswith("Escolinha") else (1972, 2006)
        for _ in range(quantidade):
            genero = rng.choice(["Feminino", "Masculino"])
            while True:
                nome = f"{rng.choice(FEM if genero == 'Feminino' else MASC)} {rng.choice(SOBRENOMES)}"
                if nome not in nomes_usados:
                    break
            nomes_usados.add(nome)
            m = novo_membro(nome, genero, nasc_aleatorio(*anos), [(INICIO, plano)])
            if categoria == ASSINANTE:
                if plano == "Anual":  # pagamento grande numa semana so (testa caixa vs competencia)
                    renovar(m, plano, INICIO + timedelta(days=rng.randrange(100)), HOJE)
                else:
                    duracao = (calculate_new_due_date(plano, datetime(2026, 1, 1)) - datetime(2026, 1, 1)).days
                    renovar(m, plano, INICIO - timedelta(days=rng.randrange(duracao)), HOJE)
            total_dias = (FIM - INICIO).days
            for d in _dias_de_treino(INICIO, FIM - timedelta(days=1)):  # domingo 27/09 so o plantado
                rampa = 0.8 + 0.4 * (d - INICIO).days / total_dias if categoria == GYM_TOTALPASS else 1.0
                if rng.random() < por_semana / 6 * DIA_PESO[d.weekday()] * rampa:
                    checkin(m, d)
            if plano == "Voucher":  # compra de 10 creditos a cada 10 visitas
                meus = [c for c in checkins if c[0] == m["id"]]
                for n, (_, dt, _) in enumerate(meus):
                    if n % 10 == 0:
                        pagamentos.append((m["id"], dt, "Compra Voucher", PRECO["Voucher"], METODO_PIX, None))
                m["creditos"] = (-len(meus)) % 10

    # --- Cenarios plantados ---
    for nome, genero in CANDIDATOS:
        fixo(novo_membro(nome, genero, nasc_aleatorio(1995, 2004), [(INICIO, "Gympass")]), {1, 3, 5})
    for nome, genero, quando in CONVERSOES:
        m = novo_membro(nome, genero, nasc_aleatorio(1990, 2002), [(INICIO, "Gympass"), (quando, "Mensal")])
        renovar(m, "Mensal", quando, HOJE)
        fixo(m, {0, 2})
    for nome, genero, quando in PERDAS:
        m = novo_membro(nome, genero, nasc_aleatorio(1985, 2000), [(INICIO, "Mensal"), (quando, "Gympass")])
        renovar(m, "Mensal", INICIO - timedelta(days=10), quando)
        m["vencimento"] = None  # virou Gympass: plano sem vencimento
        fixo(m, {0, 2})
    for nome, genero in VENCIDOS:
        m = novo_membro(nome, genero, nasc_aleatorio(1980, 2000), [(INICIO, "Mensal")])
        renovar(m, "Mensal", date(2026, 5, 1), date(2026, 8, 2))  # ultimo pagamento 01/08, venceu 01/09
        fixo(m, {0, 2, 4})
    m = novo_membro(*DOMINGO, nasc_aleatorio(1980, 1995), [(INICIO, "Livre")])
    fixo(m, {1})
    checkin(m, FIM)

    checkins.sort(key=lambda c: c[1])

    # --- Fase 1: esquema antigo (sem frequencia.plano), dados ate a migracao ---
    Base.metadata.create_all(create_engine(f"sqlite:///{destino}"))
    con = sqlite3.connect(destino)
    con.execute("ALTER TABLE frequencia DROP COLUMN plano")
    con.executemany(
        "INSERT INTO planos (nome, preco, valor_por_checkin, requer_vencimento, ativo, is_quota, quota_amount)"
        " VALUES (?, ?, ?, ?, 1, ?, ?)", PLANOS)
    con.executemany(
        "INSERT INTO membros (id, nome, plano, vencimento_plano, estado_plano, data_nascimento,"
        " data_cadastro, whatsapp, genero, voucher_credits) VALUES (?, ?, ?, ?, 'ATIVO', ?, ?, ?, ?, ?)",
        [(m["id"], m["nome"], plano_em(m, MIGRACAO),
          m["vencimento"].isoformat() if m["vencimento"] else None,
          m["nasc"].isoformat(), INICIO.isoformat(), m["whatsapp"], m["genero"], m["creditos"])
         for m in membros])
    con.executemany(
        "INSERT INTO pagamentos (member_id, data_pagamento, tipo_transacao, descricao, valor,"
        " metodo_pagamento, nova_data_vencimento) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(mid, dt.isoformat(sep=" "), tipo, f"{tipo} (simulado)", valor, metodo,
          vence.isoformat() if vence else None)
         for mid, dt, tipo, valor, metodo, vence in pagamentos])
    con.executemany(
        "INSERT INTO frequencia (member_id, checkin_datetime) VALUES (?, ?)",
        [(mid, dt.isoformat(sep=" ")) for mid, dt, _ in checkins if dt.date() < MIGRACAO])
    con.commit()
    con.close()

    # --- Fase 2: a migracao real (coluna + backfill) ---
    _alembic_upgrade(destino)

    # --- Fase 3: app novo grava o Tipo do Check-in; membros chegam ao plano final ---
    con = sqlite3.connect(destino)
    con.executemany(
        "INSERT INTO frequencia (member_id, checkin_datetime, plano) VALUES (?, ?, ?)",
        [(mid, dt.isoformat(sep=" "), plano) for mid, dt, plano in checkins if dt.date() >= MIGRACAO])
    con.executemany("UPDATE membros SET plano = ? WHERE id = ?", [(plano_em(m, FIM), m["id"]) for m in membros])
    con.commit()
    con.close()
    return destino


if __name__ == "__main__":
    caminho = gerar()
    print(f"Banco simulado criado em {caminho}")
    print('Abrir o app com ele (PowerShell, na raiz): $env:SUMMIT_DB_PATH = "demo_database.db"; python run.py')
```

- [ ] **Step 4: Rodar e ver passar**

Run: `PY -m pytest tests/test_weekly_summary.py -v`
Expected: 2 passed

- [ ] **Step 5: Gerar o banco na raiz e conferir que o git o ignora**

Run: `PY scripts/seed_demo_db.py && git status --short && git check-ignore -v demo_database.db`
Expected: imprime "Banco simulado criado em ...demo_database.db". O `git status` mostra so os arquivos novos da task e **nao** mostra `demo_database.db`; o `check-ignore` aponta a regra `*.db`.

- [ ] **Step 6: Commit**

```bash
git add scripts/seed_demo_db.py tests/test_weekly_summary.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Add banco simulado para testar o Resumo Semanal

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Calculo das Semanas (`montar_semanas`)

Definicoes (spec e CONTEXT.md):
- **Semana**: segunda 00:00 ate domingo 23:59. A ultima fechada e a anterior a semana de hoje.
- **Janela de 4 Semanas**: a Semana e as 3 anteriores. Usada no mapa de calor, nos Candidatos e no Perfil.
- **Conversao / Perda**: check-in da Semana cuja categoria difere da do check-in anterior do mesmo membro, indo de Gym/Totalpass para Assinante ou Pacote (Conversao), ou o contrario (Perda).
- **Valor por Visita de Assinante**: pagamentos com `nova_data_vencimento` (exceto Treino), rateados por dia entre `data_pagamento` e `nova_data_vencimento`. Soma-se a parte que cai na Semana e divide-se pelos check-ins de Assinante.

**Files:**
- Create: `src/reports/weekly_summary.py`
- Test: `tests/test_weekly_summary.py` (acrescentar)

- [ ] **Step 1: Escrever os testes que falham.** Acrescentar a `tests/test_weekly_summary.py`:

```python
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.reports.weekly_summary import montar_semanas, semana_fechada

HOJE = date(2026, 9, 28)


@pytest.fixture(scope="module")
def demo_session(demo_db):
    session = sessionmaker(bind=create_engine(f"sqlite:///{demo_db}"))()
    yield session
    session.close()


@pytest.fixture(scope="module")
def semanas(demo_session):
    return montar_semanas(demo_session, HOJE)


@pytest.mark.parametrize("hoje, segunda", [
    (date(2026, 9, 28), date(2026, 9, 21)),  # segunda: a semana passada fechou
    (date(2026, 9, 27), date(2026, 9, 14)),  # domingo: a semana atual ainda esta aberta
    (date(2026, 9, 26), date(2026, 9, 14)),  # sabado
])
def test_semana_fechada(hoje, segunda):
    assert semana_fechada(hoje) == segunda


def test_doze_semanas_da_mais_recente_para_a_mais_antiga(semanas):
    assert len(semanas) == 12
    assert semanas[0]["rotulo"] == "21/09 – 26/09"
    assert semanas[-1]["rotulo"] == "06/07 – 11/07"


def test_domingo_entra_no_total_mas_nao_no_grafico_por_dia(semanas):
    s = semanas[0]
    assert s["checkins"] == sum(sum(v) for v in s["por_dia"].values()) + 1


def test_conversoes_e_perdas_plantadas(semanas):
    assert sorted(n for s in semanas for n in s["conversoes"]) == ["Caio Moreira", "Lia Fontes", "Rui Teixeira"]
    assert sorted(n for s in semanas for n in s["perdas"]) == ["Bia Campos", "Davi Prado"]
    assert semanas[0]["perdas"] == ["Davi Prado"]


def test_candidatos_a_conversao(semanas):
    candidatos = semanas[0]["candidatos"]
    plantados = {"Alan Duarte", "Bela Nunes", "Cris Vale", "Duda Lobo", "Enzo Sales", "Flor Aguiar"}
    assert plantados <= {c["nome"] for c in candidatos}
    assert all(c["checkins"] >= 8 and c["whatsapp"].startswith("https://wa.me/") for c in candidatos)


def test_vencidos_que_vieram(semanas):
    plantados = {"Elis Barros", "Ivo Leal", "Nina Paiva", "Otto Reis", "Tais Mota"}
    assert plantados <= {v["nome"] for v in semanas[0]["vencidos"]}


def test_valor_por_visita_e_fatia_gym_totalpass(semanas):
    s = semanas[0]
    assert s["valor_visita_gt"] == 15.0
    assert s["valor_visita_assinante"] > 15.0
    assert 25 <= s["pct_gt"] <= 55


def test_comparativos(semanas):
    s = semanas[0]
    assert s["anterior"]["checkins"] == semanas[1]["checkins"]
    assert set(s["media4"]) == {"checkins", "pct_gt", "receita"}


def test_mapa_de_calor_e_perfil(semanas):
    s = semanas[0]
    assert len(s["calor"]) == 6 and all(len(linha) == 16 for linha in s["calor"])
    assert 1 <= len(s["destaques"]) <= 2
    assert sum(s["perfil"]["Gym/Totalpass"]["idade"].values()) > 0
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PY -m pytest tests/test_weekly_summary.py -v`
Expected: ERROR `ModuleNotFoundError: No module named 'src.reports.weekly_summary'`

- [ ] **Step 3: Criar `src/reports/weekly_summary.py`**

```python
"""Resumo Semanal: numeros-chave de uma Semana numa tela so (termos em CONTEXT.md)."""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from src.core.plan_status import PENDENTE
from src.core.plan_utils import ASSINANTE, CATEGORIAS, GYM_TOTALPASS, PACOTE, categoria_do_plano
from src.data.models import Frequencia, Membro, Pagamento
from src.utils.utils import create_whatsapp_link

N_SEMANAS = 12
LIMIAR_CANDIDATO = 8       # check-ins Gym/Totalpass na janela de 4 Semanas
MIN_CHECKINS_CELULA = 5    # celula do mapa de calor so vira destaque com esse volume
HORAS = list(range(7, 23))
DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
DIAS_EXTENSO = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
FAIXAS = [("até 17", 0, 17), ("18–24", 18, 24), ("25–34", 25, 34), ("35–44", 35, 44), ("45+", 45, 200)]
PAGANTES = {ASSINANTE, PACOTE}   # lado "que paga" de uma Conversao ou Perda
KPIS = ("checkins", "pct_gt", "receita")


def semana_fechada(hoje: date) -> date:
    """Segunda-feira da ultima Semana fechada (a Semana vai de segunda a domingo)."""
    return hoje - timedelta(days=hoje.weekday() + 7)


def _carregar(session: Session):
    # ponytail: carrega todo o historico em memoria (~8 mil check-ins/ano); filtrar por janela se passar de 100 mil
    membros = {
        m.id: m
        for m in session.query(Membro).filter(
            or_(Membro.estado_plano.is_(None), Membro.estado_plano != PENDENTE)
        )
    }
    ultima_categoria = {}
    checkins = []  # (member_id, datetime, categoria, categoria do check-in anterior do membro)
    consulta = (
        session.query(Frequencia.member_id, Frequencia.checkin_datetime,
                      func.coalesce(Frequencia.plano, Membro.plano))
        .join(Membro, Frequencia.member_id == Membro.id)
        .order_by(Frequencia.checkin_datetime)
    )
    for mid, dt, plano in consulta:
        if mid not in membros:
            continue
        categoria = categoria_do_plano(plano)
        checkins.append((mid, dt, categoria, ultima_categoria.get(mid)))
        ultima_categoria[mid] = categoria
    pagamentos = session.query(
        Pagamento.data_pagamento, Pagamento.valor, Pagamento.tipo_transacao, Pagamento.nova_data_vencimento
    ).filter(Pagamento.data_pagamento.isnot(None)).all()
    return membros, checkins, pagamentos


def _receita_competencia_assinante(pagamentos, seg: date) -> float:
    fim = seg + timedelta(days=7)
    total = 0.0
    for data_pag, valor, tipo, vence in pagamentos:
        if not vence or "treino" in (tipo or "").lower():
            continue
        inicio = data_pag.date()
        dias = max((vence - inicio).days, 1)
        sobreposicao = (min(vence, fim) - max(inicio, seg)).days
        if sobreposicao > 0:
            total += valor * sobreposicao / dias
    return total


def _mapa_de_calor(janela):
    total, gt = Counter(), Counter()
    for _, dt, categoria, _ in janela:
        if dt.weekday() < 6 and dt.hour in HORAS:  # domingo e madrugada ficam fora do mapa
            total[dt.weekday(), dt.hour] += 1
            gt[dt.weekday(), dt.hour] += categoria == GYM_TOTALPASS
    celulas = [[[total[d, h], gt[d, h]] for h in HORAS] for d in range(6)]
    destaques = sorted(
        (k for k, n in total.items() if n >= MIN_CHECKINS_CELULA),
        key=lambda k: (-gt[k] / total[k], -total[k]),
    )[:2]
    frases = [
        f"{DIAS_EXTENSO[d]} {h}h: {round(100 * gt[d, h] / total[d, h])}% Gym/Totalpass ({gt[d, h]} de {total[d, h]})"
        for d, h in destaques
    ]
    return {"calor": celulas, "destaques": frases}


def _candidatos(membros, janela):
    contagem = Counter(c[0] for c in janela if c[2] == GYM_TOTALPASS)
    ultima_categoria = {c[0]: c[2] for c in janela}  # janela esta em ordem cronologica
    lista = [
        {"nome": membros[mid].nome, "checkins": n,
         "whatsapp": create_whatsapp_link(membros[mid].whatsapp or "")}
        for mid, n in contagem.items()
        if n >= LIMIAR_CANDIDATO and ultima_categoria[mid] == GYM_TOTALPASS
    ]
    return sorted(lista, key=lambda c: (-c["checkins"], c["nome"]))


def _vencidos(membros, da_semana, hoje: date):
    ids = {c[0] for c in da_semana if c[2] == ASSINANTE}
    vencidos = sorted(
        (m for m in (membros[i] for i in ids)
         if categoria_do_plano(m.plano) == ASSINANTE and m.vencimento_plano and m.vencimento_plano < hoje),
        key=lambda m: m.vencimento_plano,
    )
    return [
        {"nome": m.nome, "plano": m.plano, "vencimento": m.vencimento_plano.strftime("%d/%m/%Y"),
         "whatsapp": create_whatsapp_link(m.whatsapp or "")}
        for m in vencidos
    ]


def _faixa(nascimento, referencia: date) -> str:
    if not nascimento:
        return "Sem data"
    idade = referencia.year - nascimento.year - (
        (referencia.month, referencia.day) < (nascimento.month, nascimento.day))
    return next((nome for nome, menor, maior in FAIXAS if menor <= idade <= maior), "Sem data")


def _perfil(membros, janela, seg: date):
    categoria_por_membro = {c[0]: c[2] for c in janela}
    perfil = {}
    for categoria in (GYM_TOTALPASS, ASSINANTE):
        grupo = [membros[i] for i, c in categoria_por_membro.items() if c == categoria]
        perfil[categoria] = {
            "idade": Counter(_faixa(m.data_nascimento, seg) for m in grupo),
            "genero": Counter(m.genero or "Não informado" for m in grupo),
        }
    return perfil


def _nomes(membros, ids):
    return sorted(membros[i].nome for i in ids)


def _semana(seg: date, hoje: date, membros, checkins, pagamentos) -> dict:
    fim = seg + timedelta(days=7)
    inicio_janela = seg - timedelta(days=21)
    da_semana = [c for c in checkins if seg <= c[1].date() < fim]
    janela = [c for c in checkins if inicio_janela <= c[1].date() < fim]

    por_categoria = Counter(c[2] for c in da_semana)
    total, gt, assinantes = len(da_semana), por_categoria[GYM_TOTALPASS], por_categoria[ASSINANTE]
    pag_semana = [p for p in pagamentos if seg <= p[0].date() < fim]
    receita_gt = sum(p[1] for p in pag_semana if p[2] in ("Gympass", "Totalpass"))

    por_dia = {categoria: [0] * 6 for categoria in CATEGORIAS}
    for _, dt, categoria, _ in da_semana:
        if dt.weekday() < 6:  # domingo conta no total, mas nao ganha coluna
            por_dia[categoria][dt.weekday()] += 1

    return {
        "segunda": seg.isoformat(),
        "rotulo": f"{seg:%d/%m} – {seg + timedelta(days=5):%d/%m}",
        "checkins": total,
        "pct_gt": round(100 * gt / total, 1) if total else 0.0,
        "receita": round(sum(p[1] for p in pag_semana), 2),
        "valor_visita_gt": round(receita_gt / gt, 2) if gt else 0.0,
        "valor_visita_assinante": (
            round(_receita_competencia_assinante(pagamentos, seg) / assinantes, 2) if assinantes else 0.0),
        "por_dia": {categoria: v for categoria, v in por_dia.items() if any(v)},
        **_mapa_de_calor(janela),
        "conversoes": _nomes(membros, {c[0] for c in da_semana if c[3] == GYM_TOTALPASS and c[2] in PAGANTES}),
        "perdas": _nomes(membros, {c[0] for c in da_semana if c[3] in PAGANTES and c[2] == GYM_TOTALPASS}),
        "candidatos": _candidatos(membros, janela),
        "vencidos": _vencidos(membros, da_semana, hoje),
        "perfil": _perfil(membros, janela, seg),
    }


def montar_semanas(session: Session, hoje: date) -> list:
    """As 12 ultimas Semanas fechadas, da mais recente [0] para a mais antiga."""
    membros, checkins, pagamentos = _carregar(session)
    ultima = semana_fechada(hoje)
    # +4 Semanas so para os comparativos da Semana mais antiga
    semanas = [_semana(ultima - timedelta(weeks=i), hoje, membros, checkins, pagamentos)
               for i in range(N_SEMANAS + 4)]
    for i, s in enumerate(semanas[:N_SEMANAS]):
        s["anterior"] = {k: semanas[i + 1][k] for k in KPIS}
        s["media4"] = {k: round(sum(semanas[i + j][k] for j in range(1, 5)) / 4, 1) for k in KPIS}
    return semanas[:N_SEMANAS]
```

- [ ] **Step 4: Rodar e ver passar**

Run: `PY -m pytest tests/test_weekly_summary.py -v`
Expected: todos passam. Se `test_valor_por_visita_e_fatia_gym_totalpass` falhar so no intervalo de `pct_gt`, imprima `semanas[0]["pct_gt"]` e ajuste as visitas/semana de Gympass em `PERFIS` do seed. **Nao** alargue o intervalo do teste.

- [ ] **Step 5: Commit**

```bash
git add src/reports/weekly_summary.py tests/test_weekly_summary.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Add calculo das 12 Semanas do Resumo Semanal

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Template e geracao do HTML

**Seguranca:** nomes de membro vem do cadastro web publico. O JS so escreve dados com `textContent` (nunca `innerHTML`). O JSON embutido troca `</` por `<\/`, para um nome nao conseguir fechar a tag `<script>`.

**Files:**
- Modify: `src/reports/weekly_summary.py` (acrescentar `generate_weekly_summary`)
- Create: `src/templates/reports/weekly_summary.html`
- Test: `tests/test_weekly_summary.py` (acrescentar)

- [ ] **Step 1: Escrever o teste que falha**

```python
from src.data.models import Membro
from src.reports.weekly_summary import generate_weekly_summary


def test_gera_html_com_as_semanas_embutidas(demo_session, tmp_path, monkeypatch):
    monkeypatch.setattr("src.reports.weekly_summary.get_reports_dir", lambda: tmp_path)
    html = Path(generate_weekly_summary(db_session=demo_session, hoje=HOJE)).read_text(encoding="utf-8")
    assert "<title>Resumo Semanal" in html
    assert '"rotulo": "21/09 – 26/09"' in html


def test_nome_malicioso_nao_fecha_o_script(demo_session, tmp_path, monkeypatch):
    monkeypatch.setattr("src.reports.weekly_summary.get_reports_dir", lambda: tmp_path)
    membro = demo_session.query(Membro).filter_by(nome="Davi Prado").one()
    membro.nome = "</script><b>x"
    demo_session.flush()
    try:
        html = Path(generate_weekly_summary(db_session=demo_session, hoje=HOJE)).read_text(encoding="utf-8")
    finally:
        demo_session.rollback()
    assert "</script><b>x" not in html
    assert "<\\/script><b>x" in html
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PY -m pytest tests/test_weekly_summary.py -k "html or malicioso" -v`
Expected: ERROR `ImportError: cannot import name 'generate_weekly_summary'`

- [ ] **Step 3: Acrescentar a `src/reports/weekly_summary.py`.** Os imports vao no topo, junto aos existentes:

```python
import json
from datetime import datetime
from typing import Optional

from src.data.db import create_session
from src.reports._common import get_reports_dir, get_template_env
```

E a funcao, ao final:

```python
def generate_weekly_summary(db_session: Optional[Session] = None, hoje: Optional[date] = None) -> str:
    """Gera o HTML do Resumo Semanal e devolve o caminho do arquivo."""
    hoje = hoje or date.today()
    session = db_session or create_session()
    try:
        semanas = montar_semanas(session, hoje)
    finally:
        if db_session is None:
            session.close()
    dados = {"semanas": semanas, "dias": DIAS, "horas": HORAS,
             "faixas": [f[0] for f in FAIXAS] + ["Sem data"]}
    agora = datetime.now()
    html = get_template_env().get_template("weekly_summary.html").render(
        title="Resumo Semanal",
        subtitle="Gym/Totalpass, lotação e ações da semana",
        generate_date=agora.strftime("%d/%m/%Y às %H:%M"),
        current_year=agora.year,
        # "</" escapado: nomes vem do cadastro web e nao podem fechar o <script>
        dados_json=json.dumps(dados, ensure_ascii=False).replace("</", "<\\/"),
    )
    caminho = get_reports_dir() / f"resumo_semanal_{agora:%Y%m%d_%H%M%S}.html"
    caminho.write_text(html, encoding="utf-8")
    return str(caminho)
```

- [ ] **Step 4: Criar `src/templates/reports/weekly_summary.html`**

```html
{% extends "base_report.html" %}

{% block extra_css %}
        .nav-semana { display: flex; align-items: center; justify-content: center; gap: 16px; margin-bottom: 24px; }
        .nav-semana button { font-size: 1.4em; padding: 4px 18px; border: none; border-radius: 8px;
                             background: var(--primary); color: white; cursor: pointer; }
        .nav-semana button:disabled { background: #ccc; cursor: default; }
        .nav-semana h2 { margin: 0; min-width: 280px; text-align: center; }
        .duas-colunas { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 24px; }
        .calor { border-collapse: collapse; font-size: 0.8em; }
        .calor th, .calor td { padding: 4px 6px; text-align: center; border: 1px solid #eee; min-width: 32px; }
        .lista { list-style: none; padding: 0; }
        .lista li { padding: 6px 0; border-bottom: 1px solid #eee; }
        .lista a { margin-left: 8px; }
        .vazio { color: var(--text-muted); font-style: italic; }
        .legenda { color: var(--text-muted); font-size: 0.85em; margin: 8px 0; }
{% endblock %}

{% block content %}
<div class="nav-semana">
    <button id="btn-antiga" title="Semana anterior">←</button>
    <h2 id="rotulo"></h2>
    <button id="btn-nova" title="Semana seguinte">→</button>
</div>

<div class="stats-grid">
    <div class="stat-card blue">
        <div class="label">Check-ins</div>
        <div class="value" id="k-checkins"></div>
        <div class="label" id="d-checkins"></div>
    </div>
    <div class="stat-card orange">
        <div class="label">% Gym/Totalpass</div>
        <div class="value" id="k-pct"></div>
        <div class="label" id="d-pct"></div>
    </div>
    <div class="stat-card green">
        <div class="label">Receita da Semana</div>
        <div class="value" id="k-receita"></div>
        <div class="label" id="d-receita"></div>
    </div>
    <div class="stat-card purple">
        <div class="label">Valor por Visita</div>
        <div class="value" id="k-visita"></div>
        <div class="label">Assinante vs Gym/Totalpass</div>
    </div>
</div>

<div class="section">
    <h2>Check-ins por dia</h2>
    <div class="chart-container"><canvas id="grafico-dias"></canvas></div>
</div>

<div class="section">
    <h2>Lotação (últimas 4 semanas)</h2>
    <ul class="lista" id="destaques"></ul>
    <p class="legenda">Número = check-ins no horário. Quanto mais vermelho, maior a fatia Gym/Totalpass.</p>
    <div style="overflow-x: auto;"><table class="calor" id="calor"></table></div>
</div>

<div class="duas-colunas">
    <div class="section"><h2>Conversões</h2><ul class="lista" id="conversoes"></ul></div>
    <div class="section"><h2>Perdas para Gym/Totalpass</h2><ul class="lista" id="perdas"></ul></div>
</div>

<div class="duas-colunas">
    <div class="section"><h2>Candidatos a Conversão</h2><ul class="lista" id="candidatos"></ul></div>
    <div class="section"><h2>Vieram e estão com plano vencido</h2><ul class="lista" id="vencidos"></ul></div>
</div>

<div class="duas-colunas">
    <div class="section"><h2>Perfil por idade (%)</h2><div class="chart-container"><canvas id="grafico-idade"></canvas></div></div>
    <div class="section"><h2>Perfil por gênero (%)</h2><div class="chart-container"><canvas id="grafico-genero"></canvas></div></div>
</div>
{% endblock %}

{% block scripts %}
<script>
const DADOS = {{ dados_json }};
const S = DADOS.semanas;  // S[0] = Semana mais recente
const CORES = {"Assinante": "#6c5ce7", "Pacote": "#00b894", "Avulso": "#fdcb6e",
               "Gym/Totalpass": "#d63031", "Sem Receita": "#b2bec3", "Outros": "#636e72"};
const reais = v => v.toLocaleString("pt-BR", {style: "currency", currency: "BRL"});
const graficos = {};
let atual = 0;

function texto(id, valor) { document.getElementById(id).textContent = valor; }

function variacao(valor, referencia, sufixo) {
    if (!referencia) return "sem comparação";
    const pct = Math.round(100 * (valor - referencia) / referencia);
    return (pct >= 0 ? "▲ " : "▼ ") + Math.abs(pct) + "% " + sufixo;
}

// Dados vem do cadastro: só textContent, nunca innerHTML
function lista(id, itens, montar) {
    const ul = document.getElementById(id);
    ul.replaceChildren();
    if (!itens.length) {
        const li = document.createElement("li");
        li.className = "vazio";
        li.textContent = "Ninguém nesta semana";
        ul.append(li);
        return;
    }
    for (const item of itens) {
        const li = document.createElement("li");
        montar(li, item);
        ul.append(li);
    }
}

function comWhatsApp(li, frase, link) {
    li.append(frase);
    if (!link) return;
    const a = document.createElement("a");
    a.href = link;
    a.target = "_blank";
    a.textContent = "WhatsApp";
    li.append(a);
}

function grafico(id, config) {
    if (graficos[id]) graficos[id].destroy();
    graficos[id] = new Chart(document.getElementById(id), config);
}

function perfil(s, chave, rotulos, id) {
    const datasets = ["Gym/Totalpass", "Assinante"].map(cat => {
        const contagem = s.perfil[cat][chave];
        const total = Object.values(contagem).reduce((a, b) => a + b, 0) || 1;
        return {label: cat, backgroundColor: CORES[cat],
                data: rotulos.map(r => Math.round(100 * (contagem[r] || 0) / total))};
    });
    grafico(id, {type: "bar", data: {labels: rotulos, datasets},
                 options: {responsive: true, maintainAspectRatio: false}});
}

function mostrar(i) {
    atual = i;
    const s = S[i];
    texto("rotulo", "Semana " + s.rotulo);
    document.getElementById("btn-antiga").disabled = i === S.length - 1;
    document.getElementById("btn-nova").disabled = i === 0;

    texto("k-checkins", s.checkins);
    texto("d-checkins", variacao(s.checkins, s.anterior.checkins, "vs anterior") + " · média 4 sem.: " + s.media4.checkins);
    texto("k-pct", s.pct_gt + "%");
    texto("d-pct", "anterior: " + s.anterior.pct_gt + "% · média 4 sem.: " + s.media4.pct_gt + "%");
    texto("k-receita", reais(s.receita));
    texto("d-receita", variacao(s.receita, s.anterior.receita, "vs anterior"));
    texto("k-visita", reais(s.valor_visita_assinante) + " vs " + reais(s.valor_visita_gt));

    grafico("grafico-dias", {type: "bar",
        data: {labels: DADOS.dias, datasets: Object.entries(s.por_dia).map(([cat, valores]) =>
            ({label: cat, data: valores, backgroundColor: CORES[cat]}))},
        options: {responsive: true, maintainAspectRatio: false,
                  scales: {x: {stacked: true}, y: {stacked: true, beginAtZero: true}}}});

    lista("destaques", s.destaques, (li, frase) => { li.textContent = "⚠️ " + frase; });
    const tabela = document.getElementById("calor");
    tabela.replaceChildren();
    const cabecalho = tabela.insertRow();
    cabecalho.append(document.createElement("th"));
    for (const h of DADOS.horas) {
        const th = document.createElement("th");
        th.textContent = h + "h";
        cabecalho.append(th);
    }
    s.calor.forEach((linha, d) => {
        const tr = tabela.insertRow();
        const th = document.createElement("th");
        th.textContent = DADOS.dias[d];
        tr.append(th);
        for (const [total, gt] of linha) {
            const td = tr.insertCell();
            if (!total) continue;
            td.textContent = total;
            td.title = gt + " de " + total + " Gym/Totalpass";
            td.style.background = "rgba(214, 48, 49, " + (0.1 + 0.8 * gt / total).toFixed(2) + ")";
        }
    });

    lista("conversoes", s.conversoes, (li, nome) => { li.textContent = "✅ " + nome; });
    lista("perdas", s.perdas, (li, nome) => { li.textContent = "❌ " + nome; });
    lista("candidatos", s.candidatos, (li, c) =>
        comWhatsApp(li, c.nome + " — " + c.checkins + " check-ins em 4 semanas", c.whatsapp));
    lista("vencidos", s.vencidos, (li, v) =>
        comWhatsApp(li, v.nome + " — " + v.plano + ", venceu em " + v.vencimento, v.whatsapp));

    perfil(s, "idade", DADOS.faixas, "grafico-idade");
    const generos = [...new Set(["Gym/Totalpass", "Assinante"].flatMap(c => Object.keys(s.perfil[c].genero)))].sort();
    perfil(s, "genero", generos, "grafico-genero");
}

document.getElementById("btn-antiga").onclick = () => mostrar(atual + 1);
document.getElementById("btn-nova").onclick = () => mostrar(atual - 1);
mostrar(0);
</script>
{% endblock %}
```

- [ ] **Step 5: Rodar e ver passar**

Run: `PY -m pytest tests/test_weekly_summary.py -v`
Expected: todos passam

- [ ] **Step 6: Conferir visualmente**

Run: `PY -c "import os; os.environ['SUMMIT_DB_PATH']='demo_database.db'; from datetime import date; from src.reports.weekly_summary import generate_weekly_summary; print(generate_weekly_summary(hoje=date(2026, 9, 28)))"`

Abra o caminho impresso no navegador (a ferramenta de browser pane aceita `file:///...`) e confira:
- cabecalho "Semana 21/09 – 26/09", com a seta → desativada
- 4 cards preenchidos
- barras empilhadas
- mapa de calor com 2 frases de destaque
- Davi Prado em Perdas
- 6 plantados em Candidatos, com link WhatsApp
- 5 plantados em Vencidos
- 2 graficos de perfil
- clicando ← ate a ultima Semana (06/07 – 11/07), a seta ← desativa; Caio Moreira aparece em Conversoes na Semana 13/07 – 18/07
- nenhum erro no console

Se o `.chart-container` do `base_report.html` nao tiver altura fixa e os graficos colapsarem, adicione `.chart-container { height: 300px; }` no `extra_css`.

- [ ] **Step 7: Commit**

```bash
git add src/reports/weekly_summary.py src/templates/reports/weekly_summary.html tests/test_weekly_summary.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Add template e geracao do Resumo Semanal

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: UI — botoes na sidebar e aviso de segunda

Hoje a sidebar de Relatorios so tem Membros e Financeiro (`src/ui/components/sidebar.py:365-368`). O Relatorio de Frequencia existe no coordinator, mas nao tem botao. O aviso de segunda usa `QSettings`, que e nativo do Qt, para lembrar "ja avisei hoje".

**Files:**
- Modify: `src/ui/components/sidebar.py:52-55` e `:365-368`
- Modify: `src/ui/main_window.py:121-124` e `_on_connection_completed` (`:390-412`)
- Modify: `src/ui/coordinators/reports_coordinator.py`

- [ ] **Step 1: Sinais e botoes na sidebar.** Em `sidebar.py`, junto aos sinais de Relatorios:

```python
    reports_weekly_clicked = pyqtSignal()    # Submenu: Resumo Semanal
    reports_members_clicked = pyqtSignal()  # Submenu: Membros
    reports_financial_clicked = pyqtSignal() # Submenu: Financeiro
    reports_frequency_clicked = pyqtSignal() # Submenu: Frequência
```

E em `_build_reports_menu`:

```python
        nav_items = [
            ("⭐  Resumo Semanal", self.reports_weekly_clicked),
            ("👥  Membros", self.reports_members_clicked),
            ("💰  Financeiro", self.reports_financial_clicked),
            ("📅  Frequência", self.reports_frequency_clicked),
        ]
```

- [ ] **Step 2: Coordinator.** Em `reports_coordinator.py`, adicionar aos imports:

```python
from datetime import date

from PyQt6.QtCore import QSettings
```

E os metodos, logo depois de `generate_frequency_report`:

```python
    def generate_weekly_summary(self):
        if not self.window.is_connected:
            return
        try:
            from src.reports.weekly_summary import generate_weekly_summary

            webbrowser.open(f"file://{generate_weekly_summary()}")
        except Exception as e:
            show_error(self.window, "Não foi possível gerar o resumo semanal. Tente novamente.", detail=e)

    def offer_weekly_summary_on_monday(self):
        """Na primeira conexão de cada segunda-feira, oferece abrir o Resumo Semanal."""
        hoje = date.today()
        if hoje.weekday() != 0:
            return
        settings = QSettings("Summit", "SummitSystem")
        if settings.value("resumo_semanal/ultimo_aviso") == hoje.isoformat():
            return
        settings.setValue("resumo_semanal/ultimo_aviso", hoje.isoformat())
        resposta = QMessageBox.question(
            self.window,
            "Resumo da semana",
            "O resumo da semana passada está pronto. Quer abrir agora?",
        )
        if resposta == QMessageBox.StandardButton.Yes:
            self.generate_weekly_summary()
```

- [ ] **Step 3: Ligar na janela.** Em `main_window.py`, no bloco `# === Submenu Relatórios ===`, acrescentar:

```python
        self.sidebar.reports_weekly_clicked.connect(self.reports_coordinator.generate_weekly_summary)
        self.sidebar.reports_frequency_clicked.connect(self.reports_coordinator.generate_frequency_report)
```

E em `_on_connection_completed`, logo depois de `self.dashboard_timer.start(5000)` (ainda dentro do `if success:`):

```python
            # Segunda-feira: oferece o Resumo Semanal uma vez por dia
            self.reports_coordinator.offer_weekly_summary_on_monday()
```

- [ ] **Step 4: Rodar a suite (inclui `tests/test_main_window_smoke.py`)**

Run: `PY -m pytest -q`
Expected: so as 5 falhas de linha de base em `test_web_checkin.py`.

- [ ] **Step 5: Conferir no app com o banco simulado** (PowerShell, na raiz):

```
$env:SUMMIT_DB_PATH = "demo_database.db"; C:\Users\Usuario\.conda\envs\alcoa\python.exe run.py
```

**Com o banco simulado, nao use Backup, Otimizar nem Sincronizar**: eles agem no `gym_database.db` real (ver Task 1). As datas do simulado sao fixas (ultima Semana fechada 21/09–26/09/2026). Se o teste acontecer numa semana posterior, as Semanas mais recentes aparecem vazias, o que e esperado. Use ← para chegar em 21/09.

Confira:
- Relatorios → "Resumo Semanal" abre o navegador na ultima Semana fechada.
- "Frequencia" abre o dialogo de periodo e depois o relatorio. A tabela "por plano" mostra Gympass separado.
- Se hoje for segunda, o aviso aparece so na primeira abertura do dia. Para testar em outro dia, troque temporariamente `hoje.weekday() != 0` pelo dia de hoje e **desfaca antes do commit**.

- [ ] **Step 6: Commit**

```bash
git add src/ui/components/sidebar.py src/ui/main_window.py src/ui/coordinators/reports_coordinator.py
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Add Resumo Semanal e Frequencia na sidebar e aviso de segunda

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Documentacao

**Files:**
- Modify: `.claude/docs/DATA_DICTIONARY.md` (tabela `frequencia`)
- Modify: `.claude/docs/REPORTS_STATUS.md`

- [ ] **Step 1:** Em `DATA_DICTIONARY.md`, na tabela `frequencia`, acrescentar depois de `checkin_datetime`:

```
| plano | VARCHAR(100) | Sim | Tipo do Check-in: plano do membro no momento do check-in (ADR 0001). Backfill: pagamento per-checkin do dia, senao plano atual |
```

- [ ] **Step 2:** Em `REPORTS_STATUS.md`:
  - trocar "Tres relatorios HTML" por "Quatro relatorios HTML"
  - antes de `### Relatorio Financeiro`, acrescentar:

```
### Resumo Semanal (`src/reports/weekly_summary.py`) — relatorio principal

**Template**: `src/templates/reports/weekly_summary.html`. Spec: `docs/superpowers/specs/2026-09-28-resumo-semanal-design.md`.

- Tela unica, 12 Semanas (seg–sab) navegaveis, dados embutidos como JSON
- Check-ins, % Gym/Totalpass, Receita da Semana (caixa), Valor por Visita (competencia)
- Mapa de calor 4 semanas, Conversoes / Perdas, Candidatos a Conversao, vencidos que vieram, perfil
- Testado contra banco simulado: `python scripts/seed_demo_db.py` → `demo_database.db` (fora do git)
- Limite: Perdas para Gym/Totalpass anteriores a migracao do Tipo do Check-in ficam invisiveis (ADR 0001)
```

- [ ] **Step 3: Commit**

```bash
git add .claude/docs/DATA_DICTIONARY.md .claude/docs/REPORTS_STATUS.md
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Docs: Resumo Semanal e frequencia.plano

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
