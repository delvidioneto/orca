from datetime import datetime
import os

print(f"🔥 Script teste.py executado às {datetime.now()}")

# Tenta gravar na pasta do script; se for somente leitura (ex: volume :ro no Docker), usa logs/
_log_dir = os.path.dirname(os.path.abspath(__file__))
_log_path = os.path.join(_log_dir, "teste_exec.log")
try:
    with open(_log_path, "a", encoding="utf-8") as f:
        f.write(f"Executado às {datetime.now()}\n")
except OSError:
    _log_path = os.path.join(_log_dir, "..", "logs", "teste_exec.log")
    os.makedirs(os.path.dirname(_log_path), exist_ok=True)
    with open(_log_path, "a", encoding="utf-8") as f:
        f.write(f"Executado às {datetime.now()}\n")
