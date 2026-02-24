# 🚀 Guia de Setup Rápido - Orca

## Passo a Passo

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Banco de Dados

```bash
python manage.py migrate
```

### 3. Criar Superusuário

```bash
python manage.py createsuperuser
```

Siga as instruções para criar um usuário admin.

### 4. Executar o Servidor

```bash
python manage.py runserver
```

O scheduler será iniciado automaticamente!

### 5. Acessar a Interface

Abra seu navegador em: `http://localhost:8000`

Faça login com o superusuário criado.

## Estrutura de Diretórios

Certifique-se de que os seguintes diretórios existem:

- `scripts/` - Para seus scripts
- `logs/` - Para logs (criado automaticamente)
- `static/` - Para arquivos estáticos
- `media/` - Para uploads (criado automaticamente)

## Primeiros Passos

1. **Criar um Pipeline**
   - Vá em "Pipelines" → "Novo Pipeline"
   - Dê um nome e descrição
   - Salve

2. **Adicionar uma Tarefa**
   - Abra o pipeline criado
   - Clique em "Nova Tarefa"
   - Configure:
     - Nome da tarefa
     - Caminho do script (ex: `scripts/teste.py`)
     - Tipo de script (Python/Batch/PowerShell)
     - Agendamento (veja exemplos no README.md)
   - Salve

3. **Verificar Execuções**
   - Vá em "Execuções" para ver o histórico
   - Ou veja no Dashboard

## Exemplo de Script de Teste

Crie `scripts/teste.py`:

```python
from datetime import datetime
import sys

print(f"✅ Script executado com sucesso às {datetime.now()}")
sys.exit(0)
```

Depois crie uma tarefa que execute este script a cada minuto:

- Tipo de Agendamento: Intervalo
- Configuração: `{"minutes": 1}`

## Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'django'"
**Solução**: Instale as dependências: `pip install -r requirements.txt`

### Erro: "No such file or directory: 'scripts/...'"
**Solução**: Certifique-se de que o caminho do script está correto e o arquivo existe

### Scheduler não inicia
**Solução**: Verifique os logs ou execute manualmente:
```bash
python manage.py start_scheduler
```

### Scripts .bat ou .ps1 não funcionam
**Solução**: Estes tipos só funcionam no Windows. No Linux/Mac, use apenas scripts Python.

## Próximos Passos

- Leia o README.md completo para mais detalhes
- Explore a interface web
- Crie pipelines complexos com dependências
- Configure agendamentos avançados

