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
