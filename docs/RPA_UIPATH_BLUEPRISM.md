# Como orquestrar UiPath e Blue Prism no Orca

O Orca pode executar processos **UiPath** e **Blue Prism** como tarefas agendadas, com retry, timeout e histórico iguais aos scripts.

**Requisito:** Orca (ou o processo que executa a tarefa) deve rodar em **Windows**, com UiPath Robot ou Blue Prism instalados.

---

## Onde configurar

Na interface: **Pipelines** → **Nova tarefa** (ou **Editar tarefa**).

1. **Tipo de executor:** escolha **UiPath** ou **Blue Prism**.
2. **Configuração do executor (RPA):** preencha o JSON no textarea conforme abaixo.
3. **Timeout** e **Retries** funcionam igual aos scripts; use para processos longos ou instáveis.

---

## UiPath

O Orca chama o **UiRobot** (ou UiPath.Agent) em linha de comando com o arquivo do processo.

### Campos do executor_config

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `process_file` ou `project_path` | Sim | Caminho do arquivo .xaml do processo ou do projeto (ex: `C:\\Projetos\\MeuProcesso\\Main.xaml` ou relativo ao base_dir). |
| `executable_path` | Não | Caminho completo do UiRobot.exe. Se omitido, usa o do PATH. |

### Exemplos

**Básico:**
```json
{
  "process_file": "C:\\Automation\\MeuProcesso\\Main.xaml"
}
```

**Com executável fixo:**
```json
{
  "process_file": "C:\\Automation\\MeuProcesso\\Main.xaml",
  "executable_path": "C:\\Program Files\\UiPath\\Studio\\UiRobot.exe"
}
```

**Caminho relativo** (ao base_dir do Orca):
```json
{
  "process_file": "automation/MeuProcesso/Main.xaml"
}
```

---

## Blue Prism

O Orca chama o **AutomateC.exe** para rodar um processo publicado.

### Campos do executor_config

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `process_name` | Sim | Nome exato do processo no Blue Prism (como publicado). |
| `user` | Não* | Usuário do Blue Prism (necessário se não usar SSO). |
| `password` | Não* | Senha (usar com `user`). |
| `sso` | Não | Se `true`, usa autenticação SSO em vez de user/password. |
| `resource` | Não | Nome do resource/máquina onde rodar. |
| `executable_path` | Não | Caminho completo do AutomateC.exe. Se omitido, usa o do PATH. |

\* Ou informa `user` + `password`, ou `sso: true`.

### Exemplos

**Com user e senha:**
```json
{
  "process_name": "Processo de Faturamento",
  "user": "admin",
  "password": "sua_senha"
}
```

**Com SSO:**
```json
{
  "process_name": "Processo de Faturamento",
  "sso": true
}
```

**Com resource (máquina específica):**
```json
{
  "process_name": "Processo de Faturamento",
  "user": "admin",
  "password": "sua_senha",
  "resource": "VM-RPA-01"
}
```

---

## Dicas

- **Caminhos no Docker:** Se o Orca rodar em Linux/Docker e o RPA em Windows, será necessário um **worker em Windows** que receba o job (futuro) ou rodar o Orca no mesmo Windows onde estão UiPath/Blue Prism.
- **Segurança:** Evite senhas em texto no JSON em produção; use variáveis de ambiente ou integração futura com Orchestrator/API do Blue Prism.
- **Histórico:** stdout, stderr e código de saída do UiRobot/AutomateC são gravados em **Execuções**, igual aos scripts.

---

**Ver também:** [Arquitetura do orquestrador](/documentacao/arquitetura/) – visão geral do Core Engine e executores.
