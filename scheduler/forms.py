import json
from django import forms
from .models import Pipeline, Task, ScheduleType, ScriptType, ExecutorType


class PipelineForm(forms.ModelForm):
    class Meta:
        model = Pipeline
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'pipeline', 'name', 'description',
            'executor_type', 'executor_config', 'script_path', 'script_type', 'script_interpreter_path',
            'depends_on', 'retries', 'retry_delay', 'timeout',
            'schedule_config', 'is_active',
        ]
        widgets = {
            'pipeline': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'executor_type': forms.Select(attrs={'class': 'form-select'}),
            'executor_config': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': '{} ou ex: {"process_file": "path/to/Main.xaml"} (UiPath) ou {"process_name": "Meu Processo", "user": "admin", "password": "***"} (Blue Prism)',
            }),
            'script_path': forms.TextInput(attrs={'class': 'form-control'}),
            'script_type': forms.Select(attrs={'class': 'form-select'}),
            'script_interpreter_path': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: /app/venv/bin/python ou vazio para usar o do PATH',
            }),
            'depends_on': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
            'retries': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'retry_delay': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'timeout': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'schedule_config': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 6,
                'placeholder': '{} ou {"hour": 8, "minute": 0} ou [{"hour": 8, "minute": 0}, {"hour": 10, "minute": 30}, {"hour": 14, "minute": 18}]',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agendamento é opcional: sem dependências usa cron; com dependências a tarefa roda após as dependências
        self.fields['schedule_config'].required = False
        # Exibe executor_config como JSON legível no textarea
        if self.initial.get('executor_config') and isinstance(self.initial['executor_config'], dict):
            self.initial['executor_config'] = json.dumps(
                self.initial['executor_config'], indent=2, ensure_ascii=False
            )
        # Limita depends_on apenas a tarefas do mesmo pipeline (dependências de outro pipeline não aparecem)
        pipeline_id = None
        if self.instance and self.instance.pk:
            pipeline_id = self.instance.pipeline_id
            self.fields['depends_on'].queryset = Task.objects.filter(
                pipeline=self.instance.pipeline
            ).exclude(id=self.instance.pk)
        else:
            pipeline_id = self.data.get('pipeline') or (self.initial.get('pipeline') or None)
            if hasattr(pipeline_id, 'pk'):
                pipeline_id = pipeline_id.pk
            if pipeline_id:
                self.fields['depends_on'].queryset = Task.objects.filter(pipeline_id=pipeline_id)
            else:
                self.fields['depends_on'].queryset = Task.objects.none()
    
    def clean_schedule_config(self):
        """Valida que schedule_config é JSON válido. Aceita {}, lista de {hour, minute} ou objeto único."""
        config = self.cleaned_data.get('schedule_config')
        if config is None:
            return {}
        if isinstance(config, str):
            raw = config.strip()
            if not raw:
                return {}
            try:
                config = json.loads(raw)
            except json.JSONDecodeError:
                raise forms.ValidationError(
                    "Configuração de agendamento deve ser JSON válido. Ex: {} ou [{\"hour\": 8, \"minute\": 0}, ...]"
                )
        if isinstance(config, list):
            if not config:
                return {}
            for i, item in enumerate(config):
                if not isinstance(item, dict):
                    raise forms.ValidationError(
                        f"Item {i + 1} da lista deve ser um objeto com hour e minute."
                    )
                try:
                    h, m = int(item.get('hour', 0)), int(item.get('minute', 0))
                except (TypeError, ValueError):
                    raise forms.ValidationError(
                        f"Item {i + 1}: hour e minute devem ser números."
                    )
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    raise forms.ValidationError(
                        f"Item {i + 1}: hour deve ser 0-23 e minute 0-59."
                    )
            return config
        return config if isinstance(config, dict) else {}

    def clean_executor_config(self):
        """Valida executor_config como JSON. Para RPA, exige campos mínimos."""
        data = self.cleaned_data.get('executor_config')
        executor_type = self.cleaned_data.get('executor_type') or ExecutorType.SCRIPT
        if data is None:
            return {}
        if isinstance(data, str):
            raw = data.strip()
            if not raw:
                return {}
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                raise forms.ValidationError("Configuração do executor deve ser JSON válido.")
        if not isinstance(data, dict):
            return {}
        if executor_type == ExecutorType.UIPATH and not data.get('process_file') and not data.get('project_path'):
            raise forms.ValidationError("UiPath exige 'process_file' ou 'project_path' em executor_config.")
        if executor_type == ExecutorType.BLUEPRISM and not data.get('process_name'):
            raise forms.ValidationError("Blue Prism exige 'process_name' em executor_config.")
        return data

    def clean(self):
        cleaned = super().clean()
        executor_type = cleaned.get('executor_type') or ExecutorType.SCRIPT
        script_path = cleaned.get('script_path') or ''
        if executor_type == ExecutorType.SCRIPT and not (script_path and script_path.strip()):
            self.add_error('script_path', 'Caminho do script é obrigatório para executor tipo Script.')
        # Garante que dependências são apenas do mesmo pipeline (ignora qualquer outra enviada)
        pipeline = cleaned.get('pipeline')
        depends_on = cleaned.get('depends_on')
        if pipeline and depends_on is not None:
            valid = list(depends_on.filter(pipeline=pipeline))
            cleaned['depends_on'] = valid
        return cleaned

