# Generated for Orca - novos tipos de script

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='script_type',
            field=models.CharField(
                choices=[
                    ('python', 'Python (.py)'),
                    ('shell', 'Shell (.sh)'),
                    ('batch', 'Batch (.bat)'),
                    ('powershell', 'PowerShell (.ps1)'),
                    ('node', 'Node.js (.js)'),
                    ('perl', 'Perl (.pl)'),
                    ('ruby', 'Ruby (.rb)'),
                    ('go', 'Go (.go)'),
                ],
                default='python',
                max_length=20,
                verbose_name='Tipo de Script',
            ),
        ),
    ]
