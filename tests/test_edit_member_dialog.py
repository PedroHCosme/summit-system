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
