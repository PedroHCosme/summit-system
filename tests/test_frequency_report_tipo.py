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
