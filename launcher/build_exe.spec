# PyInstaller spec para gerar OrcaLauncher.exe
# Uso: pyinstaller build_exe.spec
# Saída: dist/OrcaLauncher.exe

import os
from pathlib import Path

# Pasta do spec: launcher/. Se rodar da raiz (pyinstaller build_exe.spec), SPECPATH = build_exe.spec → parent = raiz; então usar raiz/launcher
_spec_dir = Path(os.path.abspath(SPECPATH)).parent
if not (_spec_dir / 'orca_launcher.py').exists():
    _spec_dir = _spec_dir / 'launcher'
orca_root = _spec_dir.parent
logo = orca_root / 'static' / 'images' / 'logo.png'
datas = []
if logo.exists():
    datas.append((str(logo), 'static/images'))

a = Analysis(
    [str(_spec_dir / 'orca_launcher.py')],
    pathex=[str(_spec_dir)],
    datas=datas,
    hiddenimports=['pystray', 'PIL', 'PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='OrcaLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Sem janela de console (só bandeja)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
