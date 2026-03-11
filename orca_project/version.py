import os
from pathlib import Path


def get_version():
    env_version = os.environ.get("ORCA_VERSION", "").strip()
    if env_version:
        return env_version

    try:
        from django.conf import settings
        base = Path(settings.BASE_DIR)
    except Exception:
        base = Path(__file__).resolve().parent.parent

    version_file = base / "install" / "version" / "VERSION"
    if version_file.is_file():
        try:
            value = version_file.read_text(encoding="utf-8").strip()
            if value:
                return value
        except Exception:
            pass

    return "0.0.0"
