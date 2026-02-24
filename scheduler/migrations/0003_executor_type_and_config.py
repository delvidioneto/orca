# Orca - executor_type (script | uipath | blueprism) e executor_config

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0002_add_script_type_choices'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='executor_type',
            field=models.CharField(
                choices=[
                    ('script', 'Script (.py, .ps1, ...)'),
                    ('uipath', 'UiPath'),
                    ('blueprism', 'Blue Prism'),
                ],
                default='script',
                max_length=20,
                verbose_name='Tipo de Executor',
            ),
        ),
        migrations.AddField(
            model_name='task',
            name='executor_config',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Para UiPath: process_file, executable_path. Para Blue Prism: process_name, user, password ou sso.',
                verbose_name='Configuração do Executor (RPA)',
            ),
        ),
        migrations.AlterField(
            model_name='task',
            name='script_path',
            field=models.CharField(blank=True, max_length=500, verbose_name='Caminho do Script'),
        ),
        migrations.AddIndex(
            model_name='taskexecution',
            index=models.Index(fields=['task', 'status'], name='scheduler_te_task_status_idx'),
        ),
    ]
