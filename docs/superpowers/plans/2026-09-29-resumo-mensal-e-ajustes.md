# Resumo Mensal e ajustes de membro — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corrigir o plano errado ao editar membro e o perfil aberto pelo dashboard, trocar o mapa de calor do Resumo Semanal para so a Semana e criar o Resumo Mensal.

**Architecture:** O motor do Resumo Semanal (`_semana`) vira `_periodo(ini, fim, ...)` e serve a Semana e ao Mes. `monthly_summary.py` monta 12 Meses fechados com o motor e acrescenta 4 blocos so do Mes. Um unico template Jinja (`weekly_summary.html`) e parametrizado por `termos`.

**Tech Stack:** Python 3, SQLAlchemy 2, Jinja2 + Chart.js (HTML embutido), PyQt6, pytest.

Spec: [2026-09-29-resumo-mensal-e-ajustes-design.md](../specs/2026-09-29-resumo-mensal-e-ajustes-design.md). Glossario: [CONTEXT.md](../../../CONTEXT.md).

## Convencoes deste plano

- Branch: `feat/resumo-mensal-e-ajustes` (ja criada; o spec ja esta commitado nela).
- Comandos na raiz do repo, no Git Bash. Nos comandos abaixo, `$PY` significa `/c/Users/Usuario/.conda/envs/alcoa/python.exe`. O Bash tool nao guarda variaveis entre chamadas: escreva o caminho por extenso (ou defina `PY=...` de novo no inicio de cada comando).
- Testes: `rtk test $PY -m pytest <alvo> -q`. Se precisar ver a saida completa: `$PY -m pytest <alvo> -v`.
- Commit (gitconfig pessoal + trailer), sempre neste formato:
  ```bash
  rtk git add <arquivos> && git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "<mensagem>

  Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
  ```
- Comentarios e docstrings em portugues (convencao do projeto).
- Mensagens ao usuario final: linguagem leiga, via `src/ui/messages.py` (nenhuma nova mensagem de erro e necessaria aqui alem do padrao `show_error` ja usado).

## Mapa de arquivos

| Arquivo | Acao | Responsabilidade |
|---|---|---|
| `src/ui/dialogs/edit_member_dialog.py` | modificar | combo mostra o plano real do membro |
| `src/ui/coordinators/members_coordinator.py` | modificar | dashboard carrega os historicos do perfil |
| `src/reports/weekly_summary.py` | modificar | motor `_periodo`, `_comparar`, `_kpis`, `gerar_html`, mapa so da Semana |
| `src/reports/monthly_summary.py` | criar | Meses fechados + 4 blocos extras + `generate_monthly_summary` |
| `src/templates/reports/weekly_summary.html` | modificar | parametrizado por `termos` + blocos so do Mes |
| `src/ui/components/sidebar.py` | modificar | botao "Resumo Mensal" |
| `src/ui/coordinators/reports_coordinator.py` | modificar | `generate_monthly_summary` |
| `src/ui/main_window.py` | modificar | liga o sinal do botao |
| `scripts/seed_demo_db.py` | modificar | `data_cadastro` = data do 1o check-in (demo tem Membros novos) |
| `tests/test_edit_member_dialog.py` | criar | Tarefa 1 |
| `tests/test_dashboard_member_click.py` | criar | Tarefa 2 |
| `tests/test_weekly_summary.py` | modificar | mapa so da Semana, `media` |
| `tests/test_monthly_summary.py` | criar | Resumo Mensal |
| `tests/test_main_window_smoke.py` | modificar | handler novo existe |
| `CONTEXT.md`, `.claude/docs/REPORTS_STATUS.md`, `docs/superpowers/specs/2026-09-29-resumo-mensal-e-ajustes-design.md` | modificar | documentacao |

---

### Task 0: Baseline

**Files:** nenhum.

- [ ] **Step 1: Rodar a suite inteira antes de mexer**

Run: `rtk test $PY -m pytest tests -q`
Expected: anotar quantos passam/falham. Falhas que ja existem aqui nao sao responsabilidade deste plano; se houver, anotar os nomes para comparar no fim (Task 8).

---

### Task 1: Combo do EditMemberDialog mostra o plano real

**Files:**
- Modify: `src/ui/dialogs/edit_member_dialog.py:213-215`
- Create: `tests/test_edit_member_dialog.py`

- [ ] **Step 1: Escrever os testes que falham**

Create `tests/test_edit_member_dialog.py`:

```python
"""EditMemberDialog: o combo de plano nunca troca o plano do membro sem ninguem escolher."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication, QMessageBox

from src.ui.dialogs.edit_member_dialog import EditMemberDialog

BASE = {"id": 1, "nome": "Inácio Mariani", "whatsapp": "(31) 99607-3742", "calcado": "41"}


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def _dialogo(monkeypatch, plano):
    # so os planos ativos entram na lista, como no banco real
    monkeypatch.setattr(EditMemberDialog, "_load_plans_from_db", lambda self: ["Mensal", "Trimestral"])
    return EditMemberDialog({**BASE, "plano": plano})


def test_plano_fora_da_lista_e_mantido(app, monkeypatch):
    dialogo = _dialogo(monkeypatch, "Diária Boulder")
    salvos = []
    dialogo.member_updated.connect(salvos.append)
    assert dialogo.plano_combo.currentText() == "Diária Boulder"
    dialogo._on_save()
    assert salvos and salvos[0]["plano"] == "Diária Boulder"


def test_plano_da_lista_continua_selecionado(app, monkeypatch):
    dialogo = _dialogo(monkeypatch, "Trimestral")
    assert dialogo.plano_combo.currentText() == "Trimestral"
    assert dialogo.plano_combo.count() == 2


def test_membro_sem_plano_abre_em_branco_e_nao_salva(app, monkeypatch):
    avisos = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: avisos.append(args))
    dialogo = _dialogo(monkeypatch, None)
    salvos = []
    dialogo.member_updated.connect(salvos.append)
    assert dialogo.plano_combo.currentText() == ""
    dialogo._on_save()
    assert avisos and not salvos
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `rtk test $PY -m pytest tests/test_edit_member_dialog.py -q`
Expected: `test_plano_fora_da_lista_e_mantido` FALHA (combo mostra "Mensal"). `test_membro_sem_plano_abre_em_branco_e_nao_salva` FALHA, provavelmente com `TypeError` na construcao do dialogo (`findText(None)`). `test_plano_da_lista_continua_selecionado` passa.

- [ ] **Step 3: Implementar**

Em `src/ui/dialogs/edit_member_dialog.py`, substituir:

```python
        plano = self.member_data.get('plano', '')
        if plano in self.plans_cache or self.plano_combo.findText(plano) >= 0:
            self.plano_combo.setCurrentText(plano)
```

por:

```python
        plano = self.member_data.get('plano') or ''
        if plano and self.plano_combo.findText(plano) < 0:
            # plano inativo ou legado: mantem o valor real em vez de cair no primeiro item da lista
            self.plano_combo.addItem(plano)
        if plano:
            self.plano_combo.setCurrentText(plano)
        else:
            # sem plano: em branco, a validacao obriga a escolher antes de salvar
            self.plano_combo.insertItem(0, "")
            self.plano_combo.setCurrentIndex(0)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `rtk test $PY -m pytest tests/test_edit_member_dialog.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
rtk git add src/ui/dialogs/edit_member_dialog.py tests/test_edit_member_dialog.py && git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Fix: editar membro nao troca o plano quando ele esta fora da lista

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Perfil aberto pelo dashboard carrega os historicos

**Files:**
- Modify: `src/ui/coordinators/members_coordinator.py:31-35`
- Create: `tests/test_dashboard_member_click.py`

- [ ] **Step 1: Escrever o teste que falha**

Create `tests/test_dashboard_member_click.py`:

```python
"""Clique num membro do dashboard: perfil abre com Frequencia e Financeiro carregados."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest.mock import MagicMock

from src.ui.coordinators.members_coordinator import MembersCoordinator


def test_clique_no_dashboard_carrega_historicos(monkeypatch):
    monkeypatch.setattr("src.data.data_provider.get_member_by_id", lambda mid: {"id": mid, "nome": "Ana"})
    window = MagicMock()
    window.is_connected = True
    coordenador = MembersCoordinator(window)
    coordenador.load_member_history = MagicMock()
    coordenador.load_member_financial_history = MagicMock()

    coordenador.on_dashboard_member_clicked(7)

    window.member_search_screen.display_member_data.assert_called_once()
    coordenador.load_member_history.assert_called_once_with(7, "Ana")
    coordenador.load_member_financial_history.assert_called_once_with(7, "Ana")
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `rtk test $PY -m pytest tests/test_dashboard_member_click.py -q`
Expected: FAIL (`load_member_history` nunca chamado).

- [ ] **Step 3: Implementar**

Em `src/ui/coordinators/members_coordinator.py`, dentro de `on_dashboard_member_clicked`, substituir:

```python
                self.window.member_search_screen.display_member_data(member)
            else:
```

por:

```python
                self.window.member_search_screen.display_member_data(member)
                self.load_member_history(member_id, member.get("nome", "Membro"))
                self.load_member_financial_history(member_id, member.get("nome", "Membro"))
            else:
```

(Esse `display_member_data(member)` e o da linha 35; nao confundir com o da linha 220.)

- [ ] **Step 4: Rodar e ver passar**

Run: `rtk test $PY -m pytest tests/test_dashboard_member_click.py -q`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
rtk git add src/ui/coordinators/members_coordinator.py tests/test_dashboard_member_click.py && git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Fix: perfil aberto pelo dashboard carrega frequencia e financeiro

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Motor generico `_periodo` + mapa de calor semanal so da Semana

Refatora `weekly_summary.py` para o motor servir a Semana e ao Mes, e troca o mapa de calor semanal (item 3 do spec). O template ganha `termos`. O comportamento do semanal so muda no mapa (janela e limite) e nos nomes de chaves internas (`media4`→`media`, `segunda`→`inicio`, JSON `semanas`→`periodos`).

**Files:**
- Modify: `src/reports/weekly_summary.py` (arquivo inteiro, ver Step 3)
- Modify: `src/templates/reports/weekly_summary.html` (ver Step 5)
- Modify: `tests/test_weekly_summary.py`

- [ ] **Step 1: Ajustar/adicionar testes que falham**

Em `tests/test_weekly_summary.py`:

Trocar em `test_comparativos`:

```python
    assert set(s["media4"]) == {"checkins", "pct_gt", "receita"}
```
por:
```python
    assert set(s["media"]) == {"checkins", "pct_gt", "receita"}
```

Depois de `test_mapa_de_calor_e_perfil`, adicionar:

```python
def test_mapa_de_calor_e_so_da_semana(semanas):
    s = semanas[0]
    celulas = sum(total for linha in s["calor"] for total, _ in linha)
    assert 0 < celulas <= s["checkins"]  # com 4 Semanas no mapa, passaria de 3x o total
```

No fim de `test_gera_html_com_as_semanas_embutidas`, adicionar:

```python
    assert '"mensal": false' in html
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `rtk test $PY -m pytest tests/test_weekly_summary.py -q`
Expected: FAIL em `test_comparativos` (KeyError `media`), `test_mapa_de_calor_e_so_da_semana` e `test_gera_html_com_as_semanas_embutidas`.

- [ ] **Step 3: Reescrever `src/reports/weekly_summary.py`**

Substituir o arquivo inteiro por:

```python
"""Resumo Semanal: numeros-chave de uma Semana numa tela so (termos em CONTEXT.md).

O motor (`_periodo`) tambem serve ao Resumo Mensal (monthly_summary.py).
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from src.core.plan_status import PENDENTE
from src.core.plan_utils import ASSINANTE, CATEGORIAS, GYM_TOTALPASS, PACOTE, categoria_do_plano
from src.data.db import create_session
from src.data.models import Frequencia, Membro, Pagamento
from src.reports._common import get_reports_dir, get_template_env
from src.utils.utils import create_whatsapp_link

N_SEMANAS = 12
N_MEDIA_SEMANAS = 4
LIMIAR_CANDIDATO = 8       # check-ins Gym/Totalpass na janela de 4 Semanas
MIN_CELULA_SEMANA = 3      # celula do mapa so vira destaque com esse volume (uma Semana tem poucos check-ins)
JANELA_DIAS = 28           # Candidatos e Perfil: 4 Semanas terminando no fim do periodo
HORAS = list(range(7, 23))
DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
DIAS_EXTENSO = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
FAIXAS = [("até 17", 0, 17), ("18–24", 18, 24), ("25–34", 25, 34), ("35–44", 35, 44), ("45+", 45, 200)]
PAGANTES = {ASSINANTE, PACOTE}   # lado "que paga" de uma Conversao ou Perda
KPIS = ("checkins", "pct_gt", "receita")
TERMOS = {
    "periodo": "Semana", "prefixo": "Semana ", "receita": "Receita da Semana",
    "por_dia": "Check-ins por dia", "mapa": "Lotação (desta semana)",
    "media": "média 4 sem.", "vazio": "Ninguém nesta semana", "mensal": False,
}


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
        Pagamento.data_pagamento, Pagamento.valor, Pagamento.tipo_transacao,
        Pagamento.nova_data_vencimento, Pagamento.member_id,
    ).filter(Pagamento.data_pagamento.isnot(None)).all()
    return membros, checkins, pagamentos


def _receita_competencia_assinante(pagamentos, ini: date, fim: date) -> float:
    total = 0.0
    for data_pag, valor, tipo, vence, _ in pagamentos:
        if not vence or "treino" in (tipo or "").lower():
            continue
        inicio = data_pag.date()
        dias = max((vence - inicio).days, 1)
        sobreposicao = (min(vence, fim) - max(inicio, ini)).days
        if sobreposicao > 0:
            total += valor * sobreposicao / dias
    return total


def _mapa_de_calor(no_periodo, min_celula: int):
    total, gt = Counter(), Counter()
    for _, dt, categoria, _ in no_periodo:
        if dt.weekday() < 6 and dt.hour in HORAS:  # domingo e madrugada ficam fora do mapa
            total[dt.weekday(), dt.hour] += 1
            gt[dt.weekday(), dt.hour] += categoria == GYM_TOTALPASS
    celulas = [[[total[d, h], gt[d, h]] for h in HORAS] for d in range(6)]
    destaques = sorted(
        (k for k, n in total.items() if n >= min_celula),
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


def _vencidos(membros, no_periodo, hoje: date):
    ids = {c[0] for c in no_periodo if c[2] == ASSINANTE}
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


def _perfil(membros, janela, referencia: date):
    categoria_por_membro = {c[0]: c[2] for c in janela}
    perfil = {}
    for categoria in (GYM_TOTALPASS, ASSINANTE):
        grupo = [membros[i] for i, c in categoria_por_membro.items() if c == categoria]
        perfil[categoria] = {
            "idade": Counter(_faixa(m.data_nascimento, referencia) for m in grupo),
            "genero": Counter(m.genero or "Não informado" for m in grupo),
        }
    return perfil


def _nomes(membros, ids):
    return sorted(membros[i].nome for i in ids)


def _kpis(no_periodo, pag_periodo) -> dict:
    """Check-ins, % Gym/Totalpass e Receita (caixa) de um recorte ja filtrado."""
    gt = sum(c[2] == GYM_TOTALPASS for c in no_periodo)
    return {
        "checkins": len(no_periodo),
        "pct_gt": round(100 * gt / len(no_periodo), 1) if no_periodo else 0.0,
        "receita": round(sum(p[1] for p in pag_periodo), 2),
    }


def _periodo(ini: date, fim: date, rotulo: str, hoje: date, membros, checkins, pagamentos,
             min_celula: int) -> dict:
    """Numeros de [ini, fim): uma Semana ou um Mes."""
    janela = [c for c in checkins if fim - timedelta(days=JANELA_DIAS) <= c[1].date() < fim]
    no_periodo = [c for c in checkins if ini <= c[1].date() < fim]

    por_categoria = Counter(c[2] for c in no_periodo)
    gt, assinantes = por_categoria[GYM_TOTALPASS], por_categoria[ASSINANTE]
    pag_periodo = [p for p in pagamentos if ini <= p[0].date() < fim]
    receita_gt = sum(p[1] for p in pag_periodo if p[2] in ("Gympass", "Totalpass"))

    por_dia = {categoria: [0] * 6 for categoria in CATEGORIAS}
    for _, dt, categoria, _ in no_periodo:
        if dt.weekday() < 6:  # domingo conta no total, mas nao ganha coluna
            por_dia[categoria][dt.weekday()] += 1

    return {
        "inicio": ini.isoformat(),
        "rotulo": rotulo,
        **_kpis(no_periodo, pag_periodo),
        "valor_visita_gt": round(receita_gt / gt, 2) if gt else 0.0,
        "valor_visita_assinante": (
            round(_receita_competencia_assinante(pagamentos, ini, fim) / assinantes, 2) if assinantes else 0.0),
        "por_dia": {categoria: v for categoria, v in por_dia.items() if any(v)},
        **_mapa_de_calor(no_periodo, min_celula),
        "conversoes": _nomes(membros, {c[0] for c in no_periodo if c[3] == GYM_TOTALPASS and c[2] in PAGANTES}),
        "perdas": _nomes(membros, {c[0] for c in no_periodo if c[3] in PAGANTES and c[2] == GYM_TOTALPASS}),
        "candidatos": _candidatos(membros, janela),
        "vencidos": _vencidos(membros, no_periodo, hoje),
        "perfil": _perfil(membros, janela, ini),
    }


def _comparar(periodos: list, n: int, n_media: int) -> list:
    """Anexa `anterior` e `media` (dos n_media periodos anteriores) aos n primeiros; periodos[0] e o mais recente."""
    for i, p in enumerate(periodos[:n]):
        p["anterior"] = {k: periodos[i + 1][k] for k in KPIS}
        p["media"] = {k: round(sum(periodos[i + j][k] for j in range(1, n_media + 1)) / n_media, 1) for k in KPIS}
    return periodos[:n]


def montar_semanas(session: Session, hoje: date) -> list:
    """As 12 ultimas Semanas fechadas, da mais recente [0] para a mais antiga."""
    membros, checkins, pagamentos = _carregar(session)
    ultima = semana_fechada(hoje)
    periodos = []
    # +4 Semanas so para os comparativos da Semana mais antiga
    for i in range(N_SEMANAS + N_MEDIA_SEMANAS):
        seg = ultima - timedelta(weeks=i)
        rotulo = f"{seg:%d/%m} – {seg + timedelta(days=5):%d/%m}"
        periodos.append(_periodo(seg, seg + timedelta(days=7), rotulo, hoje,
                                 membros, checkins, pagamentos, MIN_CELULA_SEMANA))
    return _comparar(periodos, N_SEMANAS, N_MEDIA_SEMANAS)


def gerar_html(periodos: list, *, title: str, subtitle: str, termos: dict, prefixo: str) -> str:
    """Renderiza a tela unica com os periodos embutidos e devolve o caminho do arquivo."""
    dados = {"periodos": periodos, "dias": DIAS, "horas": HORAS,
             "faixas": [f[0] for f in FAIXAS] + ["Sem data"], "termos": termos}
    agora = datetime.now()
    html = get_template_env().get_template("weekly_summary.html").render(
        title=title,
        subtitle=subtitle,
        termos=termos,
        generate_date=agora.strftime("%d/%m/%Y às %H:%M"),
        current_year=agora.year,
        # "</" escapado: nomes vem do cadastro web e nao podem fechar o <script>
        dados_json=json.dumps(dados, ensure_ascii=False).replace("</", "<\\/"),
    )
    caminho = get_reports_dir() / f"{prefixo}_{agora:%Y%m%d_%H%M%S}.html"
    caminho.write_text(html, encoding="utf-8")
    return str(caminho)


def generate_weekly_summary(db_session: Optional[Session] = None, hoje: Optional[date] = None) -> str:
    """Gera o HTML do Resumo Semanal e devolve o caminho do arquivo."""
    hoje = hoje or date.today()
    session = db_session or create_session()
    try:
        semanas = montar_semanas(session, hoje)
    finally:
        if db_session is None:
            session.close()
    return gerar_html(semanas, title="Resumo Semanal", subtitle="Gym/Totalpass, lotação e ações da semana",
                      termos=TERMOS, prefixo="resumo_semanal")
```

- [ ] **Step 4: Rodar os testes do semanal (ainda deve haver falha so no HTML)**

Run: `rtk test $PY -m pytest tests/test_weekly_summary.py -q`
Expected: tudo passa, exceto possivelmente `test_gera_html_*` (template ainda usa `DADOS.semanas`, mas o teste so olha o texto do HTML; se passar, ok). O template quebra no navegador ate o Step 5.

- [ ] **Step 5: Parametrizar `src/templates/reports/weekly_summary.html`**

Aplicar estas 9 trocas exatas:

1. `title="Semana anterior"` → `title="{{ termos.periodo }} anterior"`
2. `title="Semana seguinte"` → `title="{{ termos.periodo }} seguinte"`
3. `<div class="label">Receita da Semana</div>` → `<div class="label">{{ termos.receita }}</div>`
4. `<h2>Check-ins por dia</h2>` → `<h2>{{ termos.por_dia }}</h2>`
5. `<h2>Lotação (últimas 4 semanas)</h2>` → `<h2>{{ termos.mapa }}</h2>`
6. `const S = DADOS.semanas;  // S[0] = Semana mais recente` →
   ```js
   const S = DADOS.periodos;  // S[0] = periodo mais recente
   const T = DADOS.termos;
   ```
7. `li.textContent = "Ninguém nesta semana";` → `li.textContent = T.vazio;`
8. `texto("rotulo", "Semana " + s.rotulo);` → `texto("rotulo", T.prefixo + s.rotulo);`
9. Nas linhas de `d-checkins` e `d-pct`, trocar `s.media4` e o texto "média 4 sem.":
   ```js
   texto("d-checkins", variacao(s.checkins, s.anterior.checkins, "vs anterior") + " · " + T.media + ": " + s.media.checkins);
   texto("k-pct", s.pct_gt + "%");
   texto("d-pct", "anterior: " + s.anterior.pct_gt + "% · " + T.media + ": " + s.media.pct_gt + "%");
   ```
   (a linha `texto("k-pct", ...)` fica entre as duas, como no original)

- [ ] **Step 6: Rodar tudo do semanal**

Run: `rtk test $PY -m pytest tests/test_weekly_summary.py -q`
Expected: todos passam (inclusive `test_mapa_de_calor_e_perfil`, que exige 1 a 2 destaques com o limite 3; se falhar com 0 destaques, o dado do demo esta magro: nao suba o limite, abra a duvida com o dono).

- [ ] **Step 7: Checar visualmente o semanal no navegador**

Run: `SUMMIT_DB_PATH=demo_database.db $PY -c "from datetime import date; from src.reports.weekly_summary import generate_weekly_summary; print(generate_weekly_summary(hoje=date(2026,9,28)))"`
(Se `demo_database.db` nao existir: `$PY scripts/seed_demo_db.py` primeiro.)
Abrir o caminho impresso com `mcp__Claude_Browser__navigate` (`file:///...`). Verificar: titulo "Lotação (desta semana)", setas funcionam, mapa e numeros aparecem, `read_console_messages` sem erros.

- [ ] **Step 8: Commit**

```bash
rtk git add src/reports/weekly_summary.py src/templates/reports/weekly_summary.html tests/test_weekly_summary.py && git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Refactor: motor _periodo generico; mapa de calor semanal so da Semana

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Motor do Resumo Mensal (`monthly_summary.py`)

**Files:**
- Create: `src/reports/monthly_summary.py`
- Create: `tests/test_monthly_summary.py`

- [ ] **Step 1: Escrever os testes que falham**

Create `tests/test_monthly_summary.py`:

```python
"""Resumo Mensal: Meses fechados e os 4 blocos so do Mes (novos, renovacoes, evolucao, inativos)."""
from datetime import date, datetime, time
from pathlib import Path

import pytest

from src.data.models import Frequencia, Membro, Pagamento
from src.reports.monthly_summary import generate_monthly_summary, mes_fechado, montar_meses

HOJE = date(2026, 10, 5)  # ultimo Mes fechado: setembro/2026


@pytest.mark.parametrize("hoje, primeiro_dia", [
    (date(2026, 9, 28), date(2026, 8, 1)),   # setembro ainda nao fechou
    (date(2026, 10, 1), date(2026, 9, 1)),   # dia 1: o mes passado fechou
    (date(2027, 1, 15), date(2026, 12, 1)),  # virada de ano
])
def test_mes_fechado(hoje, primeiro_dia):
    assert mes_fechado(hoje) == primeiro_dia


def _membro(s, nome, plano, cadastro=None, estado=None):
    m = Membro(nome=nome, plano=plano, data_cadastro=cadastro, estado_plano=estado,
               whatsapp="(31) 99999-0000")
    s.add(m)
    s.flush()
    return m


def _checkin(s, m, dia):
    s.add(Frequencia(member_id=m.id, checkin_datetime=datetime.combine(dia, time(18)), plano=m.plano))


def _pagamento(s, m, dia, vence):
    s.add(Pagamento(member_id=m.id, data_pagamento=datetime.combine(dia, time(10)),
                    tipo_transacao="Renovação Plano", valor=190.0, nova_data_vencimento=vence))


@pytest.fixture
def meses(db_session):
    s = db_session
    ana = _membro(s, "Ana", "Mensal", cadastro=date(2026, 9, 10))      # nova, voltou
    bia = _membro(s, "Bia", "Gympass", cadastro=date(2026, 9, 12))     # nova, nao voltou
    _membro(s, "Caio", "Mensal", cadastro=date(2026, 8, 30))           # cadastrada fora do mes
    for dia in (date(2026, 9, 10), date(2026, 9, 17)):
        _checkin(s, ana, dia)
    _checkin(s, bia, date(2026, 9, 12))

    dani = _membro(s, "Dani", "Mensal")                                # venceu 19/09 e renovou
    _pagamento(s, dani, date(2026, 8, 20), date(2026, 9, 19))
    _pagamento(s, dani, date(2026, 9, 19), date(2026, 10, 19))
    edu = _membro(s, "Edu", "Mensal")                                  # venceu 24/09 e nao renovou
    _pagamento(s, edu, date(2026, 8, 25), date(2026, 9, 24))
    fabio = _membro(s, "Fabio", "Trimestral")                          # vence so em dezembro
    _pagamento(s, fabio, date(2026, 9, 1), date(2026, 12, 1))
    gil = _membro(s, "Gil", "Gympass")                                 # nao e Assinante
    _pagamento(s, gil, date(2026, 8, 25), date(2026, 9, 24))

    hugo = _membro(s, "Hugo", "Mensal")                                # treinou em agosto, sumiu
    for dia in (date(2026, 8, 5), date(2026, 8, 12)):
        _checkin(s, hugo, dia)
    iara = _membro(s, "Iara", "Mensal")                                # treinou nos dois meses
    _checkin(s, iara, date(2026, 8, 10))
    _checkin(s, iara, date(2026, 9, 15))
    joao = _membro(s, "Joao", "Mensal")                                # so em julho: nao conta
    _checkin(s, joao, date(2026, 7, 20))
    lia = _membro(s, "Lia", "Mensal", estado="PENDENTE")               # PENDENTE fica fora de tudo
    _checkin(s, lia, date(2026, 8, 3))
    s.flush()
    return montar_meses(s, HOJE)


def test_doze_meses_do_mais_recente_para_o_mais_antigo(meses):
    assert len(meses) == 12
    assert meses[0]["rotulo"] == "Setembro/2026"
    assert meses[-1]["rotulo"] == "Outubro/2025"


def test_checkin_de_outro_mes_nao_entra_nos_totais(meses):
    assert meses[0]["checkins"] == 4          # Ana x2, Bia, Iara em setembro
    assert meses[1]["checkins"] == 3          # agosto: Hugo x2 e Iara (Lia e PENDENTE, fica fora)
    assert set(meses[0]["media"]) == {"checkins", "pct_gt", "receita"}


def test_evolucao_semana_a_semana(meses):
    evolucao = meses[0]["evolucao"]
    assert [b["rotulo"] for b in evolucao] == [
        "01/09 – 06/09", "07/09 – 13/09", "14/09 – 20/09", "21/09 – 27/09", "28/09 – 30/09"]
    assert [b["checkins"] for b in evolucao] == [0, 2, 2, 0, 0]
    assert evolucao[1]["pct_gt"] == 50.0      # Bia (Gympass) e Ana na semana de 07/09
    assert evolucao[2]["receita"] == 190.0    # pagamento da Dani em 19/09


def test_membros_novos(meses):
    novos = meses[0]["novos"]
    assert novos["total"] == 2 and novos["voltaram"] == 1
    assert novos["por_categoria"] == [
        {"categoria": "Assinante", "total": 1, "voltaram": 1},
        {"categoria": "Gym/Totalpass", "total": 1, "voltaram": 0},
    ]


def test_renovacoes(meses):
    renovacoes = meses[0]["renovacoes"]
    assert renovacoes["venciam"] == 2 and renovacoes["renovaram"] == 1
    assert [(r["nome"], r["vencimento"]) for r in renovacoes["nao_renovaram"]] == [("Edu", "24/09/2026")]
    assert renovacoes["nao_renovaram"][0]["whatsapp"].startswith("https://wa.me/")


def test_inativos(meses):
    inativos = meses[0]["inativos"]
    assert [(i["nome"], i["checkins"]) for i in inativos] == [("Hugo", 2)]
    assert inativos[0]["whatsapp"].startswith("https://wa.me/")


def test_gera_html_mensal(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr("src.reports.weekly_summary.get_reports_dir", lambda: tmp_path)
    html = Path(generate_monthly_summary(db_session=db_session, hoje=HOJE)).read_text(encoding="utf-8")
    assert "<title>Resumo Mensal" in html
    assert '"rotulo": "Setembro/2026"' in html
    assert '"mensal": true' in html
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `rtk test $PY -m pytest tests/test_monthly_summary.py -q`
Expected: erro de import (`src.reports.monthly_summary` nao existe).

- [ ] **Step 3: Implementar `src/reports/monthly_summary.py`**

```python
"""Resumo Mensal: o motor do Resumo Semanal com janela de Mes, mais 4 blocos so do Mes.

Mes = calendario fechado, dia 1 ao ultimo dia (termos em CONTEXT.md).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from src.core.plan_utils import ASSINANTE, CATEGORIAS, categoria_do_plano
from src.data.db import create_session
from src.reports.weekly_summary import _carregar, _comparar, _kpis, _periodo, gerar_html
from src.utils.utils import create_whatsapp_link

N_MESES = 12
N_MEDIA_MESES = 3
MIN_CELULA_MES = 5   # o Mes tem ~4x os check-ins da Semana, entao o limite do semanal (3) subiria para 5
MESES = ("Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro")
TERMOS = {
    "periodo": "Mês", "prefixo": "", "receita": "Receita do Mês",
    "por_dia": "Check-ins por dia da semana (soma do mês)", "mapa": "Lotação (mês inteiro)",
    "media": "média 3 meses", "vazio": "Ninguém neste mês", "mensal": True,
}


def _mes_anterior(primeiro_dia: date) -> date:
    return (primeiro_dia - timedelta(days=1)).replace(day=1)


def _proximo_mes(primeiro_dia: date) -> date:
    return (primeiro_dia.replace(day=28) + timedelta(days=4)).replace(day=1)


def mes_fechado(hoje: date) -> date:
    """Dia 1 do ultimo Mes fechado (o Mes de `hoje` ainda esta aberto)."""
    return _mes_anterior(hoje.replace(day=1))


def _evolucao(ini: date, fim: date, checkins, pagamentos) -> list:
    """Blocos segunda-domingo recortados ao Mes: check-ins, % Gym/Totalpass e Receita de cada um."""
    blocos, dia = [], ini
    while dia < fim:
        ate = min(dia + timedelta(days=7 - dia.weekday()), fim)
        no_bloco = [c for c in checkins if dia <= c[1].date() < ate]
        pag_bloco = [p for p in pagamentos if dia <= p[0].date() < ate]
        blocos.append({"rotulo": f"{dia:%d/%m} – {ate - timedelta(days=1):%d/%m}",
                       **_kpis(no_bloco, pag_bloco)})
        dia = ate
    return blocos


def _novos(membros, checkins, ini: date, fim: date) -> dict:
    """Cadastros do Mes por Categoria de Cliente; voltou = 2 ou mais check-ins ate o fim do Mes."""
    total_de_checkins = Counter(c[0] for c in checkins if c[1].date() < fim)
    por_categoria = {}
    for m in membros.values():
        if m.data_cadastro and ini <= m.data_cadastro < fim:
            categoria = categoria_do_plano(m.plano)
            item = por_categoria.setdefault(categoria, {"categoria": categoria, "total": 0, "voltaram": 0})
            item["total"] += 1
            item["voltaram"] += total_de_checkins[m.id] >= 2
    itens = [por_categoria[c] for c in CATEGORIAS if c in por_categoria]
    return {"total": sum(i["total"] for i in itens), "voltaram": sum(i["voltaram"] for i in itens),
            "por_categoria": itens}


def _renovacoes(membros, pagamentos, ini: date, fim: date) -> dict:
    """Assinantes com vencimento no Mes; renovou = existe pagamento com vencimento posterior."""
    vencimentos = defaultdict(list)
    for _, _, tipo, vence, mid in pagamentos:
        if vence and mid in membros and "treino" not in (tipo or "").lower():
            vencimentos[mid].append(vence)
    venciam = []  # (membro, vencimento no Mes, renovou)
    for mid, lista in vencimentos.items():
        m = membros[mid]
        no_mes = [v for v in lista if ini <= v < fim]
        if no_mes and categoria_do_plano(m.plano) == ASSINANTE:
            v = max(no_mes)
            venciam.append((m, v, any(outro > v for outro in lista)))
    nao = sorted(((m, v) for m, v, renovou in venciam if not renovou), key=lambda t: (t[1], t[0].nome))
    return {
        "venciam": len(venciam),
        "renovaram": sum(renovou for _, _, renovou in venciam),
        "nao_renovaram": [
            {"nome": m.nome, "plano": m.plano, "vencimento": v.strftime("%d/%m/%Y"),
             "whatsapp": create_whatsapp_link(m.whatsapp or "")}
            for m, v in nao
        ],
    }


def _inativos(membros, checkins, ini: date, fim: date, ini_anterior: date) -> list:
    """Treinaram no Mes anterior e nao vieram neste."""
    vieram = {c[0] for c in checkins if ini <= c[1].date() < fim}
    anterior = Counter(c[0] for c in checkins if ini_anterior <= c[1].date() < ini)
    lista = [
        {"nome": membros[mid].nome, "checkins": n, "whatsapp": create_whatsapp_link(membros[mid].whatsapp or "")}
        for mid, n in anterior.items() if mid not in vieram
    ]
    return sorted(lista, key=lambda i: (-i["checkins"], i["nome"]))


def montar_meses(session: Session, hoje: date) -> list:
    """Os 12 ultimos Meses fechados, do mais recente [0] para o mais antigo."""
    membros, checkins, pagamentos = _carregar(session)
    limites, ini = [], mes_fechado(hoje)
    # +3 Meses so para os comparativos do Mes mais antigo
    for _ in range(N_MESES + N_MEDIA_MESES):
        limites.append((ini, _proximo_mes(ini)))
        ini = _mes_anterior(ini)
    periodos = [
        _periodo(i, f, f"{MESES[i.month - 1]}/{i.year}", hoje, membros, checkins, pagamentos, MIN_CELULA_MES)
        for i, f in limites
    ]
    meses = _comparar(periodos, N_MESES, N_MEDIA_MESES)
    for mes, (ini, fim) in zip(meses, limites):
        mes.update({
            "evolucao": _evolucao(ini, fim, checkins, pagamentos),
            "novos": _novos(membros, checkins, ini, fim),
            "renovacoes": _renovacoes(membros, pagamentos, ini, fim),
            "inativos": _inativos(membros, checkins, ini, fim, _mes_anterior(ini)),
        })
    return meses


def generate_monthly_summary(db_session: Optional[Session] = None, hoje: Optional[date] = None) -> str:
    """Gera o HTML do Resumo Mensal e devolve o caminho do arquivo."""
    hoje = hoje or date.today()
    session = db_session or create_session()
    try:
        meses = montar_meses(session, hoje)
    finally:
        if db_session is None:
            session.close()
    return gerar_html(meses, title="Resumo Mensal",
                      subtitle="Gym/Totalpass, lotação, retenção e ações do mês",
                      termos=TERMOS, prefixo="resumo_mensal")
```

- [ ] **Step 4: Rodar e ver passar**

Run: `rtk test $PY -m pytest tests/test_monthly_summary.py -q`
Expected: todos passam. Se algum teste falhar, leia a mensagem antes de mexer no codigo: a fixture usa `datetime.combine(dia, time(18))` (18h e hora valida do mapa) e as contagens esperadas estao comentadas na propria fixture.

- [ ] **Step 5: Rodar tambem o semanal (o motor e compartilhado)**

Run: `rtk test $PY -m pytest tests/test_weekly_summary.py tests/test_monthly_summary.py -q`
Expected: tudo verde.

- [ ] **Step 6: Commit**

```bash
rtk git add src/reports/monthly_summary.py tests/test_monthly_summary.py && git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Add: Resumo Mensal (motor, Meses fechados e 4 blocos do Mes)

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Blocos do Mes no template

**Files:**
- Modify: `src/templates/reports/weekly_summary.html`

- [ ] **Step 1: CSS da tabela de evolucao**

No bloco `{% block extra_css %}`, depois da linha `.legenda { ... }`, adicionar:

```css
        .tabela { border-collapse: collapse; width: 100%; }
        .tabela th, .tabela td { padding: 6px 12px; text-align: right; border-bottom: 1px solid #eee; }
        .tabela th:first-child, .tabela td:first-child { text-align: left; }
```

- [ ] **Step 2: HTML dos blocos**

Antes de `<div class="duas-colunas">` que contem "Perfil por idade (%)" (a linha e `<div class="duas-colunas">` seguida de `<div class="section"><h2>Perfil por idade (%)</h2>`), inserir:

```html
{% if termos.mensal %}
<div class="section">
    <h2>Evolução semana a semana</h2>
    <table class="tabela" id="evolucao"></table>
</div>

<div class="duas-colunas">
    <div class="section">
        <h2>Membros novos</h2>
        <p class="legenda" id="novos-resumo"></p>
        <ul class="lista" id="novos"></ul>
    </div>
    <div class="section">
        <h2>Renovações</h2>
        <p class="legenda" id="renovacoes-resumo"></p>
        <h3>Não renovaram</h3>
        <ul class="lista" id="nao-renovaram"></ul>
    </div>
</div>

<div class="section">
    <h2>Inativos: treinaram no mês anterior e não vieram</h2>
    <ul class="lista" id="inativos"></ul>
</div>
{% endif %}

```

- [ ] **Step 3: JS**

Antes de `function mostrar(i) {`, adicionar:

```js
function extras(s) {
    const tabela = document.getElementById("evolucao");
    tabela.replaceChildren();
    const cabecalho = tabela.insertRow();
    for (const h of ["Semana", "Check-ins", "% Gym/Totalpass", "Receita"]) {
        const th = document.createElement("th");
        th.textContent = h;
        cabecalho.append(th);
    }
    for (const b of s.evolucao) {
        const tr = tabela.insertRow();
        tr.insertCell().textContent = b.rotulo;
        tr.insertCell().textContent = b.checkins;
        tr.insertCell().textContent = b.pct_gt + "%";
        tr.insertCell().textContent = reais(b.receita);
    }

    texto("novos-resumo", s.novos.total + " cadastros · " + s.novos.voltaram + " voltaram (2 ou mais check-ins)");
    lista("novos", s.novos.por_categoria, (li, n) => {
        li.textContent = n.categoria + ": " + n.total + " (" + n.voltaram + " voltaram)";
    });

    texto("renovacoes-resumo", s.renovacoes.renovaram + " de " + s.renovacoes.venciam + " assinantes renovaram");
    lista("nao-renovaram", s.renovacoes.nao_renovaram, (li, r) =>
        comWhatsApp(li, r.nome + " — " + r.plano + ", venceu em " + r.vencimento, r.whatsapp));

    lista("inativos", s.inativos, (li, i) =>
        comWhatsApp(li, i.nome + " — " + i.checkins + " check-ins no mês anterior", i.whatsapp));
}

```

E no fim de `mostrar(i)`, logo antes do `}` que a fecha (depois da linha `perfil(s, "genero", generos, "grafico-genero");`), adicionar:

```js
    if (T.mensal) extras(s);
```

- [ ] **Step 4: Gerar o mensal com o demo e ver no navegador**

Run: `SUMMIT_DB_PATH=demo_database.db $PY -c "from datetime import date; from src.reports.monthly_summary import generate_monthly_summary; print(generate_monthly_summary(hoje=date(2026,9,28)))"`
Abrir o arquivo impresso com `mcp__Claude_Browser__navigate`. Verificar:
- Cabecalho "Agosto/2026" (ultimo mes fechado em 28/09), setas navegam ate 12 meses.
- Aparecem: Evolucao semana a semana, Membros novos, Renovacoes, Inativos.
- `read_console_messages` sem erros. Ver tambem o semanal de novo: os 4 blocos do Mes NAO aparecem nele.
- Meses sem dado (anteriores a junho/2026) mostram zeros e "sem comparação", sem erro no console.

- [ ] **Step 5: Rodar os testes de HTML**

Run: `rtk test $PY -m pytest tests/test_weekly_summary.py tests/test_monthly_summary.py -q`
Expected: verde.

- [ ] **Step 6: Commit**

```bash
rtk git add src/templates/reports/weekly_summary.html && git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Add: blocos do Mes no template do resumo

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Botao "Resumo Mensal" na sidebar

**Files:**
- Modify: `src/ui/components/sidebar.py:54` e `:368`
- Modify: `src/ui/coordinators/reports_coordinator.py` (depois de `generate_weekly_summary`, ~linha 96)
- Modify: `src/ui/main_window.py:125`
- Modify: `tests/test_main_window_smoke.py`

- [ ] **Step 1: Teste que falha**

Em `tests/test_main_window_smoke.py`, na lista do `parametrize`, adicionar depois de `("reports_coordinator", "load_financial_data"),`:

```python
    ("reports_coordinator", "generate_monthly_summary"),
```

Run: `rtk test $PY -m pytest tests/test_main_window_smoke.py -q`
Expected: FAIL (`AttributeError ... generate_monthly_summary`).

- [ ] **Step 2: Sinal e botao (sidebar)**

Em `src/ui/components/sidebar.py`, depois de `reports_weekly_clicked = pyqtSignal()    # Submenu: Resumo Semanal`:

```python
    reports_monthly_clicked = pyqtSignal()   # Submenu: Resumo Mensal
```

Em `_build_reports_menu`, na lista `nav_items`, depois de `("⭐  Resumo Semanal", self.reports_weekly_clicked),`:

```python
            ("📆  Resumo Mensal", self.reports_monthly_clicked),
```

- [ ] **Step 3: Coordinator**

Em `src/ui/coordinators/reports_coordinator.py`, depois do metodo `generate_weekly_summary`:

```python
    def generate_monthly_summary(self):
        if not self.window.is_connected:
            return
        try:
            from src.reports.monthly_summary import generate_monthly_summary

            webbrowser.open(f"file://{generate_monthly_summary()}")
        except Exception as e:
            show_error(self.window, "Não foi possível gerar o resumo mensal. Tente novamente.", detail=e)
```

- [ ] **Step 4: Ligar o sinal**

Em `src/ui/main_window.py`, depois de `self.sidebar.reports_weekly_clicked.connect(...)`:

```python
        self.sidebar.reports_monthly_clicked.connect(self.reports_coordinator.generate_monthly_summary)
```

- [ ] **Step 5: Rodar**

Run: `rtk test $PY -m pytest tests/test_main_window_smoke.py -q`
Expected: verde.

- [ ] **Step 6: Verificar no app (manual)**

Rodar o app com o demo (PowerShell, na raiz): `$env:SUMMIT_DB_PATH = "demo_database.db"; python run.py`. Relatorios → "Resumo Mensal" abre o HTML no navegador. Se nao for possivel abrir a GUI aqui, dizer explicitamente na entrega que esta etapa nao foi verificada.

- [ ] **Step 7: Commit**

```bash
rtk git add src/ui/components/sidebar.py src/ui/coordinators/reports_coordinator.py src/ui/main_window.py tests/test_main_window_smoke.py && git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Add: botao Resumo Mensal na sidebar

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Demo com Membros novos e documentacao

**Files:**
- Modify: `scripts/seed_demo_db.py:208-223`
- Modify: `CONTEXT.md`
- Modify: `.claude/docs/REPORTS_STATUS.md`
- Modify: `docs/superpowers/specs/2026-09-29-resumo-mensal-e-ajustes-design.md`

- [ ] **Step 1: `data_cadastro` no demo = data do primeiro check-in**

Em `scripts/seed_demo_db.py`, depois de `checkins.sort(key=lambda c: c[1])`, adicionar:

```python
    primeiro_checkin = {}  # data_cadastro do demo: dia do 1o check-in (sem check-in: INICIO); nao gasta o rng
    for mid, dt, _ in checkins:
        primeiro_checkin.setdefault(mid, dt.date())
```

E no `INSERT INTO membros`, trocar `m["nasc"].isoformat(), INICIO.isoformat(), m["whatsapp"]` por `m["nasc"].isoformat(), primeiro_checkin.get(m["id"], INICIO).isoformat(), m["whatsapp"]`.

- [ ] **Step 2: Conferir que nada do semanal mudou**

Run: `rtk test $PY -m pytest tests/test_weekly_summary.py tests/test_monthly_summary.py -q`
Expected: verde (nao mexe no rng; so a coluna `data_cadastro`).

- [ ] **Step 3: CONTEXT.md**

Em `CONTEXT.md`, na secao `### Frequencia`, depois da definicao de **Semana**, adicionar:

```markdown
**Mes**:
Mes calendario fechado (dia 1 ao ultimo dia), usado no Resumo Mensal. A Semana que cruza a virada de mes fica inteira no Resumo Semanal e so e recortada na Evolucao do Resumo Mensal.
_Avoid_: Periodo de 30 dias
```

Na secao `### Relatorios`, depois de **Resumo Semanal**, adicionar:

```markdown
**Resumo Mensal**:
Mesmo relatorio do Resumo Semanal com janela de Mes, mais membros novos, renovacoes, evolucao semana a semana e inativos.
_Avoid_: Fechamento do mes
```

- [ ] **Step 4: REPORTS_STATUS.md**

Em `.claude/docs/REPORTS_STATUS.md`, logo depois da secao "Resumo Semanal" (antes da proxima secao `###`), adicionar:

```markdown
### Resumo Mensal (`src/reports/monthly_summary.py`)

Mesmo motor e mesmo template do Resumo Semanal (`weekly_summary.html`, parametrizado por `termos`). Spec: `docs/superpowers/specs/2026-09-29-resumo-mensal-e-ajustes-design.md`.

- 12 Meses fechados navegaveis; comparativo com o Mes anterior e a media dos 3 anteriores
- Mapa de calor do Mes inteiro (limite de destaque 5); o semanal usa so a Semana (limite 3)
- Blocos so do Mes: evolucao semana a semana, membros novos, renovacoes, inativos
```

- [ ] **Step 5: Alinhar o spec com o que foi feito**

Em `docs/superpowers/specs/2026-09-29-resumo-mensal-e-ajustes-design.md`:
- Trocar `(grafico de linhas)` por `(tabela)` no item "Evolucao semana a semana".
- Trocar `Botao "📅 Resumo Mensal"` por `Botao "📆 Resumo Mensal"` (o 📅 ja e o icone de Frequencia).
- Em "Documentacao a atualizar", trocar `` `scripts/seed_demo_db.py` (se o demo nao cobrir 2+ meses de dados)`` por `` `scripts/seed_demo_db.py` (data_cadastro = dia do 1o check-in, para o demo ter Membros novos)``.

- [ ] **Step 6: Commit**

```bash
rtk git add scripts/seed_demo_db.py CONTEXT.md .claude/docs/REPORTS_STATUS.md docs/superpowers/specs/2026-09-29-resumo-mensal-e-ajustes-design.md && git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "Docs: Resumo Mensal (CONTEXT, REPORTS_STATUS, spec) e demo com Membros novos

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Verificacao final

- [ ] **Step 1: Suite inteira**

Run: `rtk test $PY -m pytest tests -q`
Expected: mesmo resultado do baseline (Task 0) mais os testes novos passando. Qualquer falha nova e desta branch.

- [ ] **Step 2: Skill `superpowers:verification-before-completion`**

Antes de dizer que terminou: rodar de novo os comandos de verificacao dos Tasks 3 e 5 (gerar semanal e mensal com o demo, abrir no navegador, console sem erros) e relatar o que foi de fato verificado e o que nao foi (ex.: GUI PyQt do Task 6).

- [ ] **Step 3: Encerrar**

Usar `superpowers:finishing-a-development-branch` para decidir merge/PR da branch `feat/resumo-mensal-e-ajustes` para `dev`.
