"""Helpers compartilhados pelos geradores de relatório."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def get_reports_dir() -> Path:
    project_root = Path(__file__).parent.parent.parent
    reports_dir = project_root / "relatorios"
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def get_template_env() -> Environment:
    project_root = Path(__file__).parent.parent.parent
    templates_dir = project_root / "src" / "templates" / "reports"
    return Environment(loader=FileSystemLoader(str(templates_dir)))
