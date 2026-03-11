#!/usr/bin/env python3
"""
Atualiza a versão (MAJOR.MINOR.PATCH) no Orca. Única forma de alterar a versão do app.
Uso: python install/version/bump_version.py major|minor|patch

Grava em install/version/VERSION (ex.: v1.0.2). O app lê esse arquivo via orca_project.version.get_version.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Raiz do repositório = dois níveis acima (install/version/ -> install -> raiz)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VERSION_FILE = REPO_ROOT / "install" / "version" / "VERSION"


def parse_version(s: str) -> tuple[int, int, int]:
    """Extrai (major, minor, patch) de uma string como 'v1.0.1-3', '1.0.0' ou '2.0'."""
    s = re.sub(r"^v", "", s.strip())
    s = re.sub(r"-.*$", "", s)
    parts = re.findall(r"\d+", s)
    major = int(parts[0]) if len(parts) >= 1 else 0
    minor = int(parts[1]) if len(parts) >= 2 else 0
    patch = int(parts[2]) if len(parts) >= 3 else 0
    return (major, minor, patch)


def read_current_version() -> tuple[int, int, int]:
    """Lê a versão atual de install/version/VERSION."""
    if not VERSION_FILE.exists():
        return (0, 0, 0)
    text = VERSION_FILE.read_text(encoding="utf-8")
    return parse_version(text)


def bump(major: int, minor: int, patch: int, part: str) -> tuple[int, int, int]:
    """Retorna (major, minor, patch) após incrementar a parte indicada."""
    part = part.lower()
    if part == "major":
        return (major + 1, 0, 0)
    if part == "minor":
        return (major, minor + 1, 0)
    if part == "patch":
        return (major, minor, patch + 1)
    raise ValueError(f"Parte inválida: {part}. Use major, minor ou patch.")


def write_version(new_version: str) -> None:
    """Escreve a nova versão no arquivo VERSION (formato vX.Y.Z)."""
    version_str = f"v{new_version}" if not new_version.startswith("v") else new_version
    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    VERSION_FILE.write_text(version_str.strip() + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python install/version/bump_version.py major|minor|patch", file=sys.stderr)
        return 1
    part = sys.argv[1].strip().lower()
    if part not in ("major", "minor", "patch"):
        print("Parte deve ser: major, minor ou patch", file=sys.stderr)
        return 1

    current = read_current_version()
    new = bump(current[0], current[1], current[2], part)
    new_version = f"{new[0]}.{new[1]}.{new[2]}"

    write_version(new_version)
    print(new_version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
