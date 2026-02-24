"""
Versão do Orca a partir do Git (git describe --tags --always).
Usado no Django (context processor) e no launcher.
"""
import subprocess
from pathlib import Path


def get_version():
    """Retorna a versão (ex.: v1.0.0 ou hash)."""
    base = Path(__file__).resolve().parent.parent
    try:
        r = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            cwd=str(base),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0 and r.stdout:
            return r.stdout.strip()
    except Exception:
        pass
    return "0.0.0"
