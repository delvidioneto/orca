# Orca – instalação e execução no Windows

Execute os scripts desta pasta a partir de qualquer lugar; eles usam a raiz do projeto automaticamente.

| Arquivo | Uso |
|---------|-----|
| **IniciarOrca.bat** | Cria .venv (se precisar), instala dependências, roda migrações e inicia o servidor (janela visível). |
| **IniciarOrca.vbs** | Igual ao acima, mas em segundo plano (sem janela). |
| **PararOrca.bat** | Encerra o servidor iniciado em segundo plano. |
| **AdicionarInicioWindows.bat** | Adiciona o Orca à inicialização do Windows (uma vez). |
| **RemoverInicioWindows.bat** | Remove o Orca da inicialização do Windows. |

**Requisito:** Python no PATH (`python` ou `py`).

**Acesso:** http://127.0.0.1:8000
