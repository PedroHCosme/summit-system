"""
Serviço de envio de e-mail para notas do Bloco de Notas.

Utiliza SMTP do Gmail com App Password para enviar notas
(bugs, ideias, sugestões) ao desenvolvedor.
"""

import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional


def _load_config() -> dict:
    """Carrega configuração SMTP do arquivo email_config.json."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "email_config.json"
    )
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Arquivo de configuração de e-mail não encontrado: {config_path}\n"
            "Crie o arquivo email_config.json na raiz do projeto."
        )
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


_TIPO_LABELS = {
    "bug": "🐛 Bug / Erro",
    "ideia": "💡 Ideia / Sugestão",
    "outro": "📝 Outro",
}


def send_note_email(
    titulo: str,
    conteudo: str,
    tipo: str = "outro",
    created_at: Optional[datetime] = None,
) -> None:
    """
    Envia uma nota por e-mail ao desenvolvedor.

    Args:
        titulo: Título da nota.
        conteudo: Corpo/conteúdo da nota.
        tipo: Tipo da nota (bug, ideia, outro).
        created_at: Data de criação da nota.

    Raises:
        Exception: Se houver falha no envio.
    """
    tipo_label = _TIPO_LABELS.get(tipo, tipo)
    subject = f"[Summit Notes] {tipo_label} — {titulo}"

    created_str = (
        created_at.strftime("%d/%m/%Y %H:%M") if created_at else datetime.now().strftime("%d/%m/%Y %H:%M")
    )

    html_body = f"""\
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px;">
        <div style="background: #1a2540; color: #fff; padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">📝 Summit — Bloco de Notas</h2>
        </div>
        <div style="border: 1px solid #ddd; border-top: none; padding: 20px; border-radius: 0 0 8px 8px;">
            <table style="width: 100%; margin-bottom: 15px;">
                <tr><td style="color: #888; width: 100px;">Tipo:</td><td><strong>{tipo_label}</strong></td></tr>
                <tr><td style="color: #888;">Criado em:</td><td>{created_str}</td></tr>
            </table>
            <h3 style="color: #1a2540; border-bottom: 2px solid #E67E22; padding-bottom: 8px;">{titulo}</h3>
            <div style="white-space: pre-wrap; line-height: 1.6; background: #f8f9fa; padding: 15px; border-radius: 6px;">
{conteudo or '(sem conteúdo)'}
            </div>
        </div>
        <p style="color: #999; font-size: 12px; margin-top: 10px;">
            Enviado automaticamente pelo Summit Escalada.
        </p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject

    cfg = _load_config()
    smtp_user = cfg["smtp_user"]
    developer_email = cfg["developer_email"]

    msg["From"] = smtp_user
    msg["To"] = developer_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user, cfg["smtp_password"])
        server.sendmail(smtp_user, developer_email, msg.as_string())

