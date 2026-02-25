"""
Versão do Orca: variável de ambiente ORCA_VERSION, arquivo VERSION (semântico), Git ou 0.0.0.
Usado no Django (context processor) e no launcher.
"""
import os
import subprocess
from pathlib import Path


def get_version():
    """Retorna a versão. Ordem: 1) ORCA_VERSION 2) arquivo VERSION 3) Git 4) 0.0.0."""
    # Override por variável de ambiente (útil em Docker: docker run -e ORCA_VERSION=1.0.0)
    env_version = os.environ.get("ORCA_VERSION", "").strip()
    if env_version:
        return env_version

    # Base = raiz do projeto (pasta onde está manage.py)
    try:
        from django.conf import settings
        base = Path(settings.BASE_DIR)
    except Exception:
        base = Path(__file__).resolve().parent.parent

    # 1) Arquivo VERSION na raiz (atualizado pelo hook com versão semântica, ex.: v1.0.2)
    version_file = base / "VERSION"
    if version_file.is_file():
        try:
            value = version_file.read_text(encoding="utf-8").strip()
            if value:
                return value
        except Exception:
            pass

    # 2) Git (fallback quando não há VERSION)
    try:
        r = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            cwd=str(base),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0 and r.stdout and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass

    return "0.0.0"
