#!/usr/bin/env python3
"""
Launcher do Orca para Windows.
- Modo Docker ou Sem Docker (venv + SQLite)
- Ícone na bandeja: Abrir, Parar, Reiniciar, Iniciar com o Windows, Atualizar, Sair
- Versionamento automático (Git) e verificação de atualização
"""
import json
import os
import sys
import subprocess
import threading
import webbrowser
import urllib.request
from pathlib import Path

# Suporte a bandeja do sistema
try:
    import pystray
    from pystray import MenuItem as Item
    from PIL import Image
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False

# Caminho do projeto = pasta onde está o executável (ou do script)
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent.parent

ORCA_URL = "http://127.0.0.1:8000"
COMPOSE_FILE = "docker-compose.yml"
CONFIG_FILE_NAME = "orca_config.json"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "Orca"
# URL para verificar versão remota (arquivo VERSION no repositório; ajuste para seu repo)
VERSION_URL = os.environ.get("ORCA_VERSION_URL", "")
DOCKER_DESKTOP_URL = "https://www.docker.com/products/docker-desktop/"


def get_project_root():
    """Raiz do projeto Orca."""
    return APP_DIR


def get_config_path():
    return get_project_root() / CONFIG_FILE_NAME


def is_windows():
    return sys.platform == "win32"


def _subprocess_flags():
    return {"creationflags": subprocess.CREATE_NO_WINDOW} if is_windows() else {}


# --- Config (modo: docker | standalone) ---

def load_config():
    """Carrega config; retorna None se não existir."""
    p = get_config_path()
    if not p.exists():
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_config(mode: str):
    """Salva modo (docker ou standalone)."""
    p = get_config_path()
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"mode": mode}, f, indent=2)


def get_mode():
    """Retorna 'docker' ou 'standalone'. Se não houver config, retorna None."""
    cfg = load_config()
    if not cfg or "mode" not in cfg:
        return None
    return cfg["mode"] if cfg["mode"] in ("docker", "standalone") else None


def show_mode_dialog():
    """Mostra diálogo para escolher modo (tkinter). Retorna 'docker' ou 'standalone'."""
    try:
        import tkinter as tk
        from tkinter import messagebox
    except ImportError:
        return "docker"  # fallback
    choice = [None]

    def on_docker():
        choice[0] = "docker"
        top.destroy()

    def on_standalone():
        choice[0] = "standalone"
        top.destroy()

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.title(APP_NAME)
    msg = "Como deseja rodar o Orca?\n\n• Com Docker: usa containers (recomendado se já tiver Docker).\n• Sem Docker: usa Python local com SQLite (cria .venv automaticamente)."
    # Usar messagebox não permite dois botões customizados; usar Toplevel com dois botões
    top = tk.Toplevel(root)
    top.title(APP_NAME + " - Primeira execução")
    top.attributes("-topmost", True)
    tk.Label(top, text=msg, justify=tk.LEFT, padx=20, pady=10).pack(anchor=tk.W)
    frm = tk.Frame(top)
    frm.pack(pady=10)
    tk.Button(frm, text="Com Docker", command=on_docker, width=14).pack(side=tk.LEFT, padx=5)
    tk.Button(frm, text="Sem Docker (Python local)", command=on_standalone, width=22).pack(side=tk.LEFT, padx=5)
    top.geometry("+400+300")
    root.wait_window(top)
    root.destroy()
    return choice[0] or "docker"


# --- Docker ---

def docker_available():
    try:
        r = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
            **_subprocess_flags(),
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def docker_compose_up(project_root: Path):
    cwd = str(project_root)
    env = os.environ.copy()
    env["CREATE_SUPERUSER"] = "true"  # entrypoint cria admin/admin123 se não existir
    try:
        subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "up", "-d", "--wait"],
            cwd=cwd,
            env=env,
            timeout=120,
            **_subprocess_flags(),
        )
    except (subprocess.TimeoutExpired, Exception):
        pass


def docker_compose_down(project_root: Path):
    cwd = str(project_root)
    try:
        subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "down"],
            cwd=cwd,
            capture_output=True,
            timeout=30,
            **_subprocess_flags(),
        )
    except Exception:
        pass


# --- Standalone (venv + Django) ---

def python_available():
    """Verifica se há Python no PATH."""
    for name in ("python", "python3", "py"):
        try:
            subprocess.run(
                [name, "--version"],
                capture_output=True,
                timeout=5,
                **_subprocess_flags(),
            )
            return name
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def get_venv_python(project_root: Path):
    """Caminho do python do .venv."""
    if is_windows():
        return project_root / ".venv" / "Scripts" / "python.exe"
    return project_root / ".venv" / "bin" / "python"


def ensure_venv(project_root: Path):
    """Cria .venv se não existir; instala requirements; roda migrate."""
    venv_dir = project_root / ".venv"
    py = python_available()
    if not py:
        raise RuntimeError("Python não encontrado. Instale Python e tente novamente.")
    if not venv_dir.exists():
        subprocess.run(
            [py, "-m", "venv", ".venv"],
            cwd=str(project_root),
            check=True,
            timeout=120,
            **_subprocess_flags(),
        )
    venv_python = get_venv_python(project_root)
    if not venv_python.exists():
        raise RuntimeError(".venv não encontrado após criação.")
    req = project_root / "requirements.txt"
    if req.exists():
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", "requirements.txt", "-q"],
            cwd=str(project_root),
            timeout=300,
            **_subprocess_flags(),
        )
    # Migrate
    subprocess.run(
        [str(venv_python), "manage.py", "migrate", "--noinput"],
        cwd=str(project_root),
        capture_output=True,
        timeout=60,
        **_subprocess_flags(),
    )
    # Superusuário padrão (ignora erro se já existir)
    _ensure_superuser(project_root, venv_python)
    return venv_python


def _ensure_superuser(project_root: Path, venv_python: Path):
    """Cria superusuário admin se não existir (Django: DJANGO_SUPERUSER_*)."""
    env = os.environ.copy()
    env["DATABASE"] = "sqlite"
    env.setdefault("DJANGO_SUPERUSER_USERNAME", "admin")
    env.setdefault("DJANGO_SUPERUSER_PASSWORD", "admin123")
    env.setdefault("DJANGO_SUPERUSER_EMAIL", "admin@orca.local")
    subprocess.run(
        [str(venv_python), "manage.py", "createsuperuser", "--noinput"],
        cwd=str(project_root),
        env=env,
        capture_output=True,
        timeout=30,
        **_subprocess_flags(),
    )
    # returncode pode ser 1 se o usuário já existir — ok


def start_django(project_root: Path):
    """Sobe Django com runserver. Retorna o processo Popen."""
    venv_python = get_venv_python(project_root)
    if not venv_python.exists():
        venv_python = ensure_venv(project_root)
    env = os.environ.copy()
    env["DATABASE"] = "sqlite"
    return subprocess.Popen(
        [str(venv_python), "manage.py", "runserver", "0.0.0.0:8000"],
        cwd=str(project_root),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **_subprocess_flags(),
    )


def stop_django(process_ref: list):
    """Encerra o processo Django se existir."""
    if process_ref and process_ref[0] is not None:
        try:
            process_ref[0].terminate()
            process_ref[0].wait(timeout=10)
        except Exception:
            try:
                process_ref[0].kill()
            except Exception:
                pass
        process_ref[0] = None


# --- Startup (Registry) ---

def get_startup_enabled():
    if not is_windows():
        return False
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False


def set_startup(enabled: bool):
    if not is_windows():
        return
    try:
        import winreg
        path = str(Path(sys.executable).resolve()) if getattr(sys, "frozen", False) else f'"{sys.executable}" "{Path(__file__).resolve()}"'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
        try:
            if enabled:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, path)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except OSError:
                    pass
        finally:
            winreg.CloseKey(key)
    except Exception:
        pass


# --- Versão (VERSION / Git) ---

def get_local_version(project_root: Path):
    """Versão local: arquivo VERSION (semântico) ou git describe."""
    version_file = project_root / "VERSION"
    if version_file.is_file():
        try:
            value = version_file.read_text(encoding="utf-8").strip()
            if value:
                return value
        except Exception:
            pass
    try:
        r = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=5,
            **_subprocess_flags(),
        )
        if r.returncode == 0 and r.stdout:
            return r.stdout.strip()
    except Exception:
        pass
    return "0.0.0"


def get_remote_version(url: str):
    """Obtém versão remota (conteúdo de um arquivo de texto)."""
    if not url or not url.strip():
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "OrcaLauncher"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.read().decode("utf-8").strip()
    except Exception:
        return None


def parse_version(s: str):
    """Extrai número para comparação simples (ex: v1.2.0 -> (1,2,0))."""
    s = (s or "").strip().lstrip("v")
    parts = []
    for x in s.replace("-", ".").split("."):
        try:
            parts.append(int(x))
        except ValueError:
            break
    return tuple(parts) if parts else (0, 0, 0)


# --- Atualização ---

def check_update_available(project_root: Path, remote_url: str):
    """Retorna (True, remote_version) se houver atualização."""
    if not remote_url:
        return False, None
    remote = get_remote_version(remote_url)
    if not remote:
        return False, None
    local = get_local_version(project_root)
    return parse_version(remote) > parse_version(local), remote


def do_update(project_root: Path, mode: str, django_process_ref: list):
    """git pull e reinicia (Docker ou standalone)."""
    cwd = str(project_root)
    try:
        subprocess.run(["git", "pull"], cwd=cwd, capture_output=True, timeout=60, **_subprocess_flags())
    except Exception:
        pass
    if mode == "standalone" and django_process_ref is not None:
        stop_django(django_process_ref)
        req = project_root / "requirements.txt"
        venv_python = get_venv_python(project_root)
        if req.exists() and venv_python.exists():
            subprocess.run([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt", "-q"], cwd=cwd, timeout=300, **_subprocess_flags())
        subprocess.run([str(venv_python), "manage.py", "migrate", "--noinput"], cwd=cwd, capture_output=True, timeout=60, **_subprocess_flags())
        django_process_ref.clear()
        django_process_ref.append(start_django(project_root))
    elif mode == "docker":
        docker_compose_down(project_root)
        docker_compose_up(project_root)


# --- Ícone bandeja ---

def create_icon_image():
    try:
        if getattr(sys, "frozen", False) and getattr(sys, "_MEIPASS", None):
            logo = Path(sys._MEIPASS) / "static" / "images" / "logo.png"
        else:
            logo = APP_DIR / "static" / "images" / "logo.png"
        if logo.exists():
            img = Image.open(logo).convert("RGBA")
            img = img.resize((64, 64), Image.Resampling.LANCZOS)
            return img
    except Exception:
        pass
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    d.ellipse([4, 4, size - 4, size - 4], fill=(244, 208, 63), outline=(44, 62, 80))
    return img


def run_tray(project_root: Path, mode: str, django_process_ref: list):
    startup = [get_startup_enabled()]
    version_str = [get_local_version(project_root)]

    def on_open(icon, item):
        webbrowser.open(ORCA_URL)

    def on_start(icon, item):
        def _start():
            if mode == "docker":
                docker_compose_up(project_root)
            else:
                if not django_process_ref or django_process_ref[0] is None:
                    p = start_django(project_root)
                    django_process_ref.clear()
                    django_process_ref.append(p)
        threading.Thread(target=_start, daemon=True).start()

    def on_stop(icon, item):
        def _stop():
            if mode == "docker":
                docker_compose_down(project_root)
            else:
                stop_django(django_process_ref)
        threading.Thread(target=_stop, daemon=True).start()

    def on_restart(icon, item):
        def _restart():
            if mode == "docker":
                docker_compose_down(project_root)
                docker_compose_up(project_root)
            else:
                stop_django(django_process_ref)
                p = start_django(project_root)
                django_process_ref.clear()
                django_process_ref.append(p)
        threading.Thread(target=_restart, daemon=True).start()

    def on_startup(icon, item):
        startup[0] = not startup[0]
        set_startup(startup[0])

    def on_check_update(icon, item):
        def _check():
            ok, remote = check_update_available(project_root, VERSION_URL)
            if not ok or not remote:
                try:
                    import tkinter as tk
                    from tkinter import messagebox
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showinfo(APP_NAME, "Você está na versão mais recente." if not remote else "Não foi possível verificar atualizações.")
                    root.destroy()
                except Exception:
                    pass
                return
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                if messagebox.askyesno(APP_NAME, f"Existe uma nova atualização ({remote}). Deseja atualizar agora?"):
                    do_update(project_root, mode, django_process_ref)
                    version_str[0] = get_local_version(project_root)
                    messagebox.showinfo(APP_NAME, "Atualização concluída. Orca foi reiniciado.")
                root.destroy()
            except Exception:
                pass
        threading.Thread(target=_check, daemon=True).start()

    def on_about(icon, item):
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(APP_NAME, f"Orca\nVersão: {version_str[0]}\nModo: {'Docker' if mode == 'docker' else 'Sem Docker (SQLite)'}")
            root.destroy()
        except Exception:
            pass

    def on_quit(icon, item):
        if mode == "standalone":
            stop_django(django_process_ref)
        icon.stop()

    menu_items = [
        Item("Abrir Orca", on_open, default=True),
        Item("Iniciar Orca", on_start),
        Item("Parar Orca", on_stop),
        Item("Reiniciar Orca", on_restart),
        pystray.Menu.SEPARATOR,
        Item("Iniciar com o Windows", on_startup, checked=lambda item: startup[0]),
    ]
    if VERSION_URL:
        menu_items.append(Item("Verificar atualizações", on_check_update))
    menu_items.append(Item("Sobre", on_about))
    menu_items.append(Item("Sair", on_quit))

    menu = pystray.Menu(*menu_items)
    image = create_icon_image()
    icon = pystray.Icon("orca", image, f"{APP_NAME} ({version_str[0]})", menu)
    icon.run()


def run_without_tray(project_root: Path, mode: str, django_process_ref: list):
    if mode == "docker":
        docker_compose_up(project_root)
    else:
        django_process_ref.append(start_django(project_root))
    webbrowser.open(ORCA_URL)
    print("Orca em execução. Acesse:", ORCA_URL)
    try:
        input("Pressione Enter para encerrar...")
    except EOFError:
        pass
    if mode == "docker":
        docker_compose_down(project_root)
    else:
        stop_django(django_process_ref)


def main():
    project_root = get_project_root()

    # Escolha do modo (primeira execução)
    mode = get_mode()
    if mode is None:
        mode = show_mode_dialog()
        if mode not in ("docker", "standalone"):
            mode = "docker"
        save_config(mode)

    if mode == "docker":
        compose_path = project_root / COMPOSE_FILE
        if not compose_path.exists():
            print(f"Arquivo não encontrado: {compose_path}")
            if is_windows():
                input("Pressione Enter para sair...")
            sys.exit(1)
        if not docker_available():
            print("Docker não está instalado ou não está rodando.")
            print("Instale o Docker Desktop:", DOCKER_DESKTOP_URL)
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                if messagebox.askyesno(APP_NAME, "Docker não encontrado. Deseja abrir a página de download do Docker Desktop?"):
                    webbrowser.open(DOCKER_DESKTOP_URL)
                root.destroy()
            except Exception:
                pass
            if is_windows():
                input("Pressione Enter para sair...")
            sys.exit(1)

    # Standalone: garantir venv e migrações na primeira vez
    django_process_ref = []
    if mode == "standalone":
        try:
            ensure_venv(project_root)
        except Exception as e:
            print("Erro ao preparar ambiente:", e)
            if is_windows():
                input("Pressione Enter para sair...")
            sys.exit(1)

    # Inicia o stack em background
    def start_stack():
        if mode == "docker":
            docker_compose_up(project_root)
        else:
            p = start_django(project_root)
            django_process_ref.append(p)

    t = threading.Thread(target=start_stack, daemon=True)
    t.start()

    if HAS_PYSTRAY:
        run_tray(project_root, mode, django_process_ref)
    else:
        t.join()
        run_without_tray(project_root, mode, django_process_ref)


if __name__ == "__main__":
    main()
