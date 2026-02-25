# Orca Launcher (Windows)

Launcher do Orca que sobe o stack (Docker ou Sem Docker), exibe ícone na bandeja do sistema e pode iniciar com o Windows.

## Modos de execução

Na **primeira execução** o launcher pergunta como deseja rodar:

- **Com Docker** — usa `docker compose` (recomendado se já tiver Docker).
- **Sem Docker** — usa Python local com SQLite: cria `.venv` na raiz do projeto, instala `requirements.txt`, roda migrações, cria o superusuário padrão e sobe o Django com `runserver`. Ideal para quem não quer instalar Docker.

A escolha é salva em `orca_config.json` na raiz do projeto e não é perguntada de novo. Para trocar o modo, edite ou apague esse arquivo.

## O que o launcher faz

- **Docker:** verifica se o Docker está instalado/rodando; se não, oferece abrir a página de download do Docker Desktop.
- Sobe o stack (Docker: `docker compose -f docker-compose.yml up -d`; Sem Docker: processo Django em `http://127.0.0.1:8000`).
- Ícone na bandeja do sistema com menu:
  - **Abrir Orca** — abre o navegador em http://127.0.0.1:8000
  - **Iniciar Orca** — sobe o stack (útil depois de ter parado)
  - **Parar Orca** — para o stack (Docker: `docker compose down`; Sem Docker: encerra o processo Django)
  - **Reiniciar Orca** — para e sobe de novo (em ambos os modos)
  - **Iniciar com o Windows** — marca/desmarca para abrir o Orca ao ligar o PC
  - **Verificar atualizações** — aparece se a variável de ambiente `ORCA_VERSION_URL` estiver definida (URL de um arquivo de texto com a versão remota)
  - **Sobre** — mostra versão (Git) e modo (Docker / Sem Docker)
  - **Sair** — encerra o launcher (no modo Sem Docker também encerra o processo Django)

## Versão

A versão é obtida do arquivo `VERSION` na pasta do projeto (atualizado pelo hook com versão semântica) ou, na falta dele, com `git describe --tags --always`. Ela aparece no tooltip do ícone da bandeja, no menu **Sobre** e no rodapé da interface web do Orca.

## Uso sem construir o .exe (sem instalação)

**Windows:** na raiz do projeto, **`IniciarOrca.bat`** sobe o Django com `manage.py runserver` (usa .venv se existir, senão Python do PATH; `DATABASE=sqlite`). Dois cliques e acesse http://127.0.0.1:8000. Não inicia o launcher com ícone na bandeja — para isso, rode manualmente:

**Rodar o launcher (bandeja, Docker/Sem Docker) manualmente:**

1. Instale as dependências do launcher:
   ```bash
   pip install -r launcher/requirements-launcher.txt
   ```
2. Na **raiz do projeto Orca** (onde está `docker-compose.yml` e `manage.py`):
   ```bash
   python launcher/orca_launcher.py
   ```
   Ou, a partir da pasta `launcher`:
   ```bash
   python orca_launcher.py
   ```
   (O script usa a pasta pai como raiz do projeto quando não está empacotado.)

## Construir o executável (Windows)

No **Windows**, na raiz do projeto Orca:

```bash
pip install -r launcher/requirements-launcher.txt
cd launcher
pyinstaller build_exe.spec
```

O executável será gerado em `launcher/dist/OrcaLauncher.exe`. Copie `OrcaLauncher.exe` para a raiz do projeto para usar; ao executar, o launcher usa a pasta onde o .exe está como raiz do projeto.

## Distribuir para o usuário

1. Entregue a **pasta completa do projeto Orca** (código, `docker-compose.yml`, `manage.py`, etc.).
2. Coloque **`OrcaLauncher.exe`** na raiz dessa pasta.
3. **Modo Docker:** o usuário precisa ter o Docker Desktop instalado e aberto. Se não tiver, o launcher oferece o link de download.
4. **Modo Sem Docker:** o usuário precisa ter Python instalado; o launcher cria o `.venv` e instala dependências na primeira execução.
5. Ao abrir o launcher, escolha o modo (primeira vez), o stack sobe e o ícone aparece na bandeja. Se marcar "Iniciar com o Windows", o Orca será iniciado automaticamente no próximo boot.

## Iniciar com o Windows

- No menu do ícone (clique direito), marque **Iniciar com o Windows**.
- O launcher adiciona uma entrada em `HKEY_CURRENT_USER\...\Run` com o caminho do executável.
- Para desativar, desmarque **Iniciar com o Windows** no menu.

## Atualizações

Se definir a variável de ambiente `ORCA_VERSION_URL` com a URL de um arquivo de texto que contenha a versão remota (ex.: `https://raw.githubusercontent.com/seu/repo/main/VERSION`), o menu **Verificar atualizações** compara com a versão local. Se houver atualização, o usuário pode confirmar e o launcher executa `git pull`, reinstala dependências (no modo Sem Docker) ou reconstrói/sobe os containers (Docker) e reinicia o Orca.

## Superusuário (admin)

Na primeira execução, o launcher cria um superusuário para acessar o Django Admin e a aplicação:

- **Usuário:** `admin`
- **Senha:** `admin123`

Recomenda-se alterar a senha após o primeiro login (no Orca: perfil/configurações ou em `/admin/`).

No modo Docker, o container usa `CREATE_SUPERUSER=true` (definido pelo launcher) e o `docker-entrypoint.sh` cria o mesmo usuário se não existir nenhum superusuário.

## Requisitos

- **Windows** (bandeja do sistema e registro são específicos do Windows; no Mac/Linux o script pode rodar mas sem bandeja/startup).
- **Modo Docker:** Docker Desktop instalado e em execução.
- **Modo Sem Docker:** Python instalado (o launcher cria e usa `.venv` na raiz do projeto).
- Projeto Orca na mesma pasta do .exe (ou, ao rodar como script, na pasta pai da pasta `launcher`).
