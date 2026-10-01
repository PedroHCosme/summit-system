# Membros arquivados e legenda — Plano de implementacao

Spec: [2026-10-01-arquivar-membros-inativos-design.md](../specs/2026-10-01-arquivar-membros-inativos-design.md). Branch: `feat/arquivar-inativos`.

**Ambiente**: testes com `/c/Users/Usuario/.conda/envs/alcoa/python.exe -m pytest <arquivo> -q`. A suite inteira tem 5 falhas antigas em `tests/test_web_checkin.py` (400), nao relacionadas. Commits: `git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "..."`, mensagem terminando com `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Comentarios e docstrings em portugues. TDD: escreva o teste, veja falhar pelo motivo certo, depois implemente.

---

## Task 1 — Regra: `esta_arquivado` e `ids_arquivados`

**Arquivos**: `src/core/plan_status.py`, `src/reports/_common.py`, `tests/test_arquivados.py` (novo).

1. Teste primeiro, em `tests/test_arquivados.py`:

```python
"""Membro arquivado: mais de 90 dias sem check-in, sem plano vigente e sem pagamento recente."""
from datetime import date, datetime, time, timedelta

import pytest

from src.core.plan_status import esta_arquivado
from src.data.models import Frequencia, Membro, Pagamento
from src.reports._common import ids_arquivados

HOJE = date(2026, 10, 1)


def _dia(dias_atras, hora=10):
    return datetime.combine(HOJE - timedelta(days=dias_atras), time(hora))


def _arquivado(**campos):
    base = dict(ultimo_checkin=None, ultimo_pagamento=None, vencimento_plano=None,
                vencimento_treino=None, data_cadastro=None)
    return esta_arquivado(**{**base, **campos}, hoje=HOJE)


@pytest.mark.parametrize("dias, esperado", [(90, False), (91, True)])
def test_limite_de_90_dias_do_ultimo_checkin(dias, esperado):
    assert _arquivado(ultimo_checkin=_dia(dias)) is esperado


@pytest.mark.parametrize("campo", ["vencimento_plano", "vencimento_treino"])
def test_plano_ou_treino_vigente_protege(campo):
    velho = _dia(200)
    assert _arquivado(ultimo_checkin=velho, **{campo: HOJE}) is False
    assert _arquivado(ultimo_checkin=velho, **{campo: HOJE - timedelta(days=1)}) is True


@pytest.mark.parametrize("dias, esperado", [(90, False), (91, True)])
def test_pagamento_recente_protege(dias, esperado):
    assert _arquivado(ultimo_checkin=_dia(200), ultimo_pagamento=_dia(dias, 11)) is esperado


@pytest.mark.parametrize("cadastro_ha, esperado", [(30, False), (91, True)])
def test_quem_nunca_fez_checkin_conta_desde_o_cadastro(cadastro_ha, esperado):
    assert _arquivado(data_cadastro=HOJE - timedelta(days=cadastro_ha)) is esperado


def test_checkin_vale_mais_que_o_cadastro():
    assert _arquivado(ultimo_checkin=_dia(200), data_cadastro=HOJE - timedelta(days=5)) is True


def test_sem_nenhuma_data_esta_arquivado():
    assert _arquivado() is True


def test_ids_arquivados_le_o_banco(db_session):
    def membro(nome, **campos):
        m = Membro(nome=nome, plano="Mensal", estado_plano="ATIVO", **campos)
        db_session.add(m)
        db_session.flush()
        return m

    sumido = membro("Sumido")
    ativo = membro("Ativo")
    pagou = membro("Pagou")
    vigente = membro("Vigente", vencimento_plano=HOJE + timedelta(days=5))
    for m, dias in ((sumido, 120), (ativo, 3), (pagou, 120), (vigente, 120)):
        db_session.add(Frequencia(member_id=m.id, checkin_datetime=_dia(dias), plano="Mensal"))
    db_session.add(Pagamento(member_id=pagou.id, data_pagamento=_dia(10), tipo_transacao="Renovacao Plano", valor=190.0))
    db_session.flush()

    assert ids_arquivados(db_session, HOJE) == {sumido.id}
```

2. Rode, veja falhar (ImportError). Depois implemente:

`src/core/plan_status.py`: trocar `from datetime import date` por `from datetime import date, timedelta`; incluir logo depois dos limiares de inatividade:

```python
# Membro arquivado: sem check-in ha mais de 3 meses e sem plano vigente nem pagamento recente
DIAS_ARQUIVAR = 90
```

e, depois de `calcular_status_membro`:

```python
def esta_arquivado(
    ultimo_checkin,
    ultimo_pagamento,
    vencimento_plano,
    vencimento_treino,
    data_cadastro,
    hoje: Optional[date] = None,
) -> bool:
    """
    True se o membro nao deve aparecer nos relatorios (CONTEXT.md: Arquivado).

    Arquivado = mais de DIAS_ARQUIVAR dias desde o ultimo check-in (quem nunca
    veio conta desde o cadastro), sem plano/treino vigente e sem pagamento no
    mesmo prazo. Calculado na hora, nada e gravado: um check-in desarquiva.
    """
    hoje = hoje or date.today()
    for vencimento in (vencimento_plano, vencimento_treino):
        venc = _coerce_to_date(vencimento)
        if venc and venc >= hoje:
            return False
    limite = hoje - timedelta(days=DIAS_ARQUIVAR)
    pagou = _coerce_to_date(ultimo_pagamento)
    if pagou and pagou >= limite:
        return False
    referencia = _coerce_to_date(ultimo_checkin) or _coerce_to_date(data_cadastro)
    # ponytail: sem check-in nem cadastro nao ha o que mostrar, entao arquiva
    return referencia is None or referencia < limite
```

`src/reports/_common.py`: imports `from datetime import date`, `from typing import Optional`, `from sqlalchemy import func`, `from src.core.plan_status import esta_arquivado`, `from src.data.models import Frequencia, Membro, Pagamento`; funcao:

```python
def ids_arquivados(session, hoje: Optional[date] = None) -> set:
    """Ids dos Membros arquivados (regra em plan_status.esta_arquivado)."""
    ultimo_checkin = dict(
        session.query(Frequencia.member_id, func.max(Frequencia.checkin_datetime))
        .group_by(Frequencia.member_id).all()
    )
    ultimo_pagamento = dict(
        session.query(Pagamento.member_id, func.max(Pagamento.data_pagamento))
        .group_by(Pagamento.member_id).all()
    )
    return {
        m.id for m in session.query(Membro)
        if esta_arquivado(ultimo_checkin.get(m.id), ultimo_pagamento.get(m.id), m.vencimento_plano,
                          m.vencimento_treino, m.data_cadastro, hoje)
    }
```

3. Rode `tests/test_arquivados.py` (verde) e a suite inteira (so as 5 falhas antigas). Commit: `Add: regra de membro arquivado (90 dias sem check-in, sem plano vigente nem pagamento)`.

---

## Task 2 — Membros e Financeiro: excluir arquivados + rodape + legenda

**Arquivos**: `src/reports/analytics.py`, `src/reports/members_report.py`, `src/reports/finance_report.py`, `src/templates/reports/_legenda_membros.html` (novo), `src/templates/reports/members_report.html`, `src/templates/reports/finance_report.html`, `tests/test_reports_overhaul.py`.

1. Teste primeiro, no fim de `tests/test_reports_overhaul.py` (usa os helpers `_seed_plans`, `_add_member`, `_add_checkin`, `_add_payment` do proprio arquivo):

```python
def test_arquivado_sai_das_contagens_mas_fica_na_receita_por_plano(db_session):
    _seed_plans(db_session)
    sumido = _add_member(db_session, "Sumido", plano="Anual", venc_offset=-200)
    ativo = _add_member(db_session, "Ativo Hoje", venc_offset=20)
    _add_checkin(db_session, sumido.id, days_ago=120)
    _add_checkin(db_session, ativo.id, days_ago=2)
    _add_payment(db_session, sumido.id, 190.0, days_ago=100)
    inicio = datetime.combine(date.today() - timedelta(days=150), time.min)
    fim = datetime.combine(date.today(), time.max)

    payload = ReportAnalyticsService(db_session).compute_member_features(inicio, fim)
    assert "Sumido" not in {r["nome"] for r in payload["list_data"]}
    assert payload["executive_summary"]["total_base"] == 1
    assert payload["arquivados"] == 1
    assert "Sumido" in {f.nome for f in payload["todos_features"]}

    membros_html = Path(generate_members_report(
        db_session=db_session, start_date=inicio, end_date=fim, period_label="Teste")).read_text(encoding="utf-8")
    assert "Como classificamos os membros" in membros_html
    assert "Membros arquivados (fora destas contagens): 1" in membros_html
    assert "Sumido" not in membros_html

    financeiro_html = Path(generate_finance_report(
        period="Teste", start_date=inicio, end_date=fim,
        payment_service=PaymentService(db_session=db_session),
        member_service=MemberService(db_session=db_session),
    )).read_text(encoding="utf-8")
    assert "Como classificamos os membros" in financeiro_html
    assert "Membros arquivados (fora destas contagens): 1" in financeiro_html
    assert "Anual" in financeiro_html  # ranking por plano continua com a receita de quem arquivou
```

2. Rode: falha em `payload["arquivados"]` (KeyError). Implemente em etapas e rode entre elas:

**a) `analytics.py`** — importar `from src.reports._common import ids_arquivados`. Em `compute_member_features`, depois da query `rows`, calcule `arquivados = ids_arquivados(self.db_session)`. O laco que monta `features` passa a se chamar `todos` (mesmo codigo); depois dele:

```python
        features = [f for f in todos if f.member_id not in arquivados]
```

(o p90, os segmentos e tudo que ja usa `features` seguem iguais). No dict devolvido, manter `"member_features": features` e acrescentar:

```python
            "todos_features": todos,
            "arquivados": len(todos) - len(features),
```

Adicione ainda a funcao de modulo `legenda_segmentos()` (importando de `plan_status` tambem `DIAS_ARQUIVAR`):

```python
def legenda_segmentos() -> Dict[str, Any]:
    """Texto da legenda 'Como classificamos os membros', montado das constantes de plan_status."""
    def dias(extra: int) -> str:
        return (f"{LIMIAR_INATIVO_PADRAO + extra} dias (mensal e similares), "
                f"{LIMIAR_INATIVO_QUOTA + extra} (pacote) ou {LIMIAR_INATIVO_AVULSO + extra} (Gympass, Totalpass, diaria)")

    return {
        "intro": (f"Ativo = o ultimo check-in esta dentro do limite do plano: {LIMIAR_INATIVO_PADRAO} dias "
                  f"(mensal e similares), {LIMIAR_INATIVO_QUOTA} (pacote, que tambem exige creditos) ou "
                  f"{LIMIAR_INATIVO_AVULSO} (Gympass, Totalpass, diaria, cortesia)."),
        "linhas": [
            {"nome": "Muito ativo", "regra": "Dentro do limite do plano e entre os 10% que mais vieram no periodo (minimo 4 check-ins)."},
            {"nome": "Estavel", "regra": "Dentro do limite do plano, com frequencia normal."},
            {"nome": "Risco moderado", "regra": f"Passou do limite do plano sem check-in: mais de {dias(0)}."},
            {"nome": "Risco alto", "regra": f"Sem check-in ha mais de {dias(14)}; ou plano vencido e mais de 14 dias sem check-in."},
            {"nome": "Reativacao urgente", "regra": f"Sem check-in ha mais de {dias(30)}."},
            {"nome": "Arquivado", "regra": (f"Mais de {DIAS_ARQUIVAR} dias sem check-in, sem plano vigente e sem pagamento no mesmo prazo. "
                                            "Fica fora dos relatorios e volta sozinho com um check-in ou pagamento.")},
        ],
    }
```

Rode: ainda falha, agora em `"Como classificamos..."`.

**b) Template compartilhado** `src/templates/reports/_legenda_membros.html` (sem `extends`; use as classes `section` ja existentes nos dois relatorios; tabela simples com o estilo que o proprio relatorio ja usa para tabelas, ou CSS inline minimo):

```html
<div class="section">
    <h2>Como classificamos os membros</h2>
    <p>{{ legenda.intro }}</p>
    <table style="border-collapse: collapse; width: 100%;">
        {% for linha in legenda.linhas %}
        <tr>
            <td style="padding: 6px 12px; border-bottom: 1px solid #eee; white-space: nowrap;"><strong>{{ linha.nome }}</strong></td>
            <td style="padding: 6px 12px; border-bottom: 1px solid #eee;">{{ linha.regra }}</td>
        </tr>
        {% endfor %}
    </table>
    <p class="legenda" style="color: #666; font-size: 0.85em;">Membros arquivados (fora destas contagens): {{ arquivados }}</p>
</div>
```

Em `members_report.html` e `finance_report.html`, logo antes do `{% endblock %}` que fecha `{% block content %}` (linhas 267 e 228), inclua `{% include "_legenda_membros.html" %}`.

**c) Geradores**: em `members_report.py` e `finance_report.py` importe `legenda_segmentos` de `src.reports.analytics` e acrescente ao `context`: `"legenda": legenda_segmentos(), "arquivados": retention["arquivados"]` (no financeiro a variavel e `retention_current["arquivados"]`). Rode: o teste agora so deve falhar em `"Anual" in financeiro_html` (porque `member_features` ja nao tem o Sumido).

**d) Financeiro**: o ranking por plano usa todos os membros (receita real de quem arquivou depois):

```python
        for feature in retention_current["todos_features"]:   # em vez de member_features
            planos_map[feature.plano] = ...
```

Mantenha comentario `# receita por plano usa todos os membros: arquivado so sai das contagens, nao do caixa`. Os demais usos de `member_features` (segmentos, receita em risco) continuam com os nao arquivados.

3. Rode `tests/test_reports_overhaul.py` e a suite inteira. Commit: `Add: membros arquivados saem dos relatorios de Membros e Financeiro, com legenda de classificacao`.

---

## Task 3 — Frequencia, Semanal e Mensal

**Arquivos**: `src/reports/frequency_report.py`, `src/reports/weekly_summary.py`, `src/reports/monthly_summary.py`, `tests/test_frequency_report_tipo.py` (ou novo `tests/test_frequency_arquivados.py`), `tests/test_weekly_summary.py`, `tests/test_monthly_summary.py`.

1. Testes primeiro:

Frequencia (novo arquivo `tests/test_frequency_arquivados.py`):

```python
from datetime import date, datetime, timedelta
from pathlib import Path

from src.data.models import Frequencia, Membro
from src.reports.frequency_report import generate_frequency_report


def test_arquivado_sai_dos_membros_em_risco(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr("src.reports.frequency_report.get_reports_dir", lambda: tmp_path)
    for nome, dias in (("Sumido Total", 120), ("Parou Ontem", 20)):
        m = Membro(nome=nome, plano="Mensal", estado_plano="ATIVO", voucher_credits=0,
                   data_cadastro=date.today() - timedelta(days=400))
        db_session.add(m)
        db_session.flush()
        db_session.add(Frequencia(member_id=m.id, checkin_datetime=datetime.now() - timedelta(days=dias), plano="Mensal"))
    db_session.commit()

    html = Path(generate_frequency_report(db_session=db_session, days=7)).read_text(encoding="utf-8")

    assert "Parou Ontem" in html
    assert "Sumido Total" not in html
```

Mensal (em `tests/test_monthly_summary.py`, usa `_membro`, `_checkin`, `_pagamento`, `HOJE=2026-10-05`):

```python
def test_arquivado_sai_das_listas_de_contato(db_session):
    s = db_session
    zeca = _membro(s, "Zeca", "Mensal", cadastro=date(2026, 1, 5))    # sumiu em maio: arquivado
    bento = _membro(s, "Bento", "Mensal", cadastro=date(2026, 1, 5))  # igual, mas pagou em setembro
    _pagamento(s, bento, date(2026, 9, 20), date(2026, 10, 20))
    for m in (zeca, bento):
        for dia in (date(2026, 5, 3), date(2026, 5, 10)):
            _checkin(s, m, dia)
    ivo = _membro(s, "Ivo", "Mensal")      # veio em abril com plano vencido, depois sumiu: arquivado
    jade = _membro(s, "Jade", "Mensal")    # igual, mas pagou em setembro
    _pagamento(s, jade, date(2026, 9, 20), date(2026, 10, 20))
    for m in (ivo, jade):
        m.vencimento_plano = date(2026, 4, 1)
        _checkin(s, m, date(2026, 4, 10))
    s.flush()

    meses = {m["rotulo"]: m for m in montar_meses(s, HOJE)}

    inativos = {i["nome"] for i in meses["Junho/2026"]["inativos"]}
    assert "Bento" in inativos and "Zeca" not in inativos
    vencidos = {v["nome"] for v in meses["Abril/2026"]["vencidos"]}
    assert "Jade" in vencidos and "Ivo" not in vencidos
```

Semanal (em `tests/test_weekly_summary.py`; adicione `from datetime import datetime, time` e `Frequencia, Pagamento` aos imports):

```python
def test_arquivado_sai_dos_candidatos(db_session):
    def candidato(nome):
        m = Membro(nome=nome, plano="Gympass", whatsapp="(31) 99999-0000")
        db_session.add(m)
        db_session.flush()
        for dia in (16, 17, 18, 19, 20, 22, 23, 24):  # 8 check-ins Gym/Totalpass em junho
            db_session.add(Frequencia(member_id=m.id, checkin_datetime=datetime(2026, 6, dia, 18), plano="Gympass"))
        return m

    candidato("Gil Sumido")
    hana = candidato("Hana Pagou")
    db_session.add(Pagamento(member_id=hana.id, data_pagamento=datetime(2026, 9, 1, 10),
                             tipo_transacao="Gympass", valor=15.0))
    db_session.flush()

    semana = next(s for s in montar_semanas(db_session, HOJE) if s["rotulo"] == "06/07 – 11/07")

    nomes = {c["nome"] for c in semana["candidatos"]}
    assert "Hana Pagou" in nomes and "Gil Sumido" not in nomes
```

(`HOJE = 2026-09-28` nesse arquivo. Confira que a janela de Candidatos da Semana 06/07 cobre 15/06–12/07 e que `categoria_do_plano("Gympass")` e Gym/Totalpass; ajuste dias/rotulo se algum pressuposto falhar, sem enfraquecer a assercao.)

2. Rode os tres, veja falharem (arquivado ainda aparece; no mensal `meses["..."]` pode vir com a lista cheia).

3. Implemente:

`frequency_report.py`: importar `from src.reports._common import ids_arquivados` (o modulo ja importa `get_reports_dir` de la, estenda o import). Em `at_risk_rows`, selecione tambem `Membro.id` (primeira coluna) e filtre depois da consulta:

```python
        arquivados = ids_arquivados(db_session)
        at_risk_rows = [m for m in at_risk_rows if m.id not in arquivados]
```

`weekly_summary.py`: `from src.reports._common import get_reports_dir, get_template_env, ids_arquivados` (estender import existente). Assinaturas:

- `_candidatos(membros, janela, arquivados=frozenset())`: acrescentar `and mid not in arquivados` ao filtro do comprehension.
- `_vencidos(membros, no_periodo, hoje, arquivados=frozenset())`: `ids = {c[0] for c in no_periodo if c[2] == ASSINANTE and c[0] not in arquivados}`.
- `_periodo(..., min_celula, arquivados=frozenset())` repassa `arquivados` a `_candidatos` e `_vencidos`.
- `montar_semanas`: `arquivados = ids_arquivados(session, hoje)` depois de `_carregar`; passar `arquivados` ao chamar `_periodo`.

`monthly_summary.py`: importar `ids_arquivados`; `_inativos(membros, checkins, ini, fim, ini_anterior, arquivados=frozenset())` com `if mid not in vieram and mid not in arquivados`; `montar_meses`: `arquivados = ids_arquivados(session, hoje)`, passado a `_periodo` e `_inativos`. Comentario curto: `# arquivado (CONTEXT.md) so sai das listas de contato; numeros e Renovacoes nao mudam`.

4. Rode os tres arquivos, depois a suite inteira. Commit: `Add: membros arquivados saem de Frequencia e das listas de contato dos resumos`.

---

## Task 4 — Documentacao

**Arquivos**: `CONTEXT.md`, `.claude/docs/REPORTS_STATUS.md`, `.claude/docs/BUSINESS_RULES.md`.

- `CONTEXT.md`: novo termo **Arquivado** no formato dos termos vizinhos (regra de 90 dias, plano vigente e pagamento protegem, calculado na hora, nada gravado, volta sozinho, sai dos relatorios; Receita nao muda).
- `REPORTS_STATUS.md`: secao curta "Membros arquivados" (onde sai, limites do spec) e a legenda nos Relatorios de Membros e Financeiro.
- `BUSINESS_RULES.md`: uma linha na secao de status de membro apontando o 4o estado computado "arquivado" (conferir a estrutura do arquivo antes de editar).
- Sem codigo. Commit: `Docs: membros arquivados e legenda de classificacao`.

## Verificacao final (controlador)

Suite inteira (so as 5 falhas antigas), revisao da branch inteira por subagente, e gerar os relatorios sobre `demo_database.db` (`python scripts/seed_demo_db.py` se preciso) para conferir no navegador que a legenda aparece e nada quebra.
