# Orca - interpretador opcional do script (venv do usuário)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0003_executor_type_and_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='script_interpreter_path',
            field=models.CharField(
                blank=True,
                help_text='Opcional. Caminho do Python/interpretador do ambiente do usuário. Em branco usa o do sistema (PATH). Ex: /app/venv/bin/python',
                max_length=500,
                verbose_name='Interpretador (ex: /venv/bin/python)',
            ),
        ),
    ]
