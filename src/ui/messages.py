"""Mensagens ao usuário em linguagem simples (o dono da academia é leigo em TI).

Regra do projeto: nenhuma mensagem de erro pode mandar o usuário "olhar o
console" nem despejar o texto cru da exceção no corpo principal. O texto
principal explica em português claro o que aconteceu e o que fazer; o detalhe
técnico (a exceção) fica escondido em "Mostrar detalhes", útil só pro suporte.
"""

from PyQt6.QtWidgets import QMessageBox


def show_error(parent, message, detail=None, title="Ops, algo não deu certo"):
    """Mostra um erro amigável.

    Args:
        parent: janela pai (para o diálogo aparecer centralizado nela).
        message: frase clara em português — o que aconteceu + o próximo passo.
        detail: exceção ou texto técnico (opcional). Vai para "Mostrar detalhes",
                nunca para o corpo principal.
        title: título curto e tranquilizador.
    """
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle(title)
    box.setText(message)
    if detail is not None:
        box.setDetailedText(str(detail))
    box.exec()


def show_warning(parent, message, title="Atenção"):
    """Aviso simples, sem detalhe técnico (ex.: campo obrigatório, ação inválida)."""
    QMessageBox.warning(parent, title, message)


def show_info(parent, message, title="Tudo certo"):
    """Confirmação amigável de uma ação bem-sucedida."""
    QMessageBox.information(parent, title, message)
