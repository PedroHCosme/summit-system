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
