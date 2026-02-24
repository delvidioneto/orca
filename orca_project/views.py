"""Views globais do projeto Orca."""
from pathlib import Path

import markdown
from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

# Índice da documentação: slug, título, descrição, e arquivo .md (ou None para template)
DOC_ENTRIES = [
    {
        "slug": "uso",
        "title": "Pipelines e Tarefas",
        "description": "Como criar pipelines, tarefas e configurar o agendamento via JSON.",
        "icon": "bi-diagram-3",
        "file": None,  # usa template
    },
    {
        "slug": "rpa",
        "title": "RPA – UiPath e Blue Prism",
        "description": "Orquestrar processos UiPath e Blue Prism com exemplos de configuração.",
        "icon": "bi-robot",
        "file": "RPA_UIPATH_BLUEPRISM.md",
    },
    {
        "slug": "arquitetura",
        "title": "Arquitetura do Orquestrador",
        "description": "Core Engine, executores, lock, retry e evolução futura.",
        "icon": "bi-cpu",
        "file": "ORCHESTRATOR_ARCHITECTURE.md",
    },
    {
        "slug": "executores",
        "title": "Executores de Script",
        "description": "Tipos de script (.py, .sh, .ps1, etc.), Strategy e Factory.",
        "icon": "bi-code-slash",
        "file": "ARCHITECTURE_EXECUTORS.md",
    },
]


class DocumentacaoView(LoginRequiredMixin, TemplateView):
    """Redireciona para o índice da documentação."""
    template_name = "documentacao_index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["doc_entries"] = DOC_ENTRIES
        return context


class DocumentacaoPageView(LoginRequiredMixin, TemplateView):
    """Exibe uma página da documentação (template ou .md)."""
    template_name = "documentacao_page.html"

    def get_template_names(self):
        if self.kwargs.get("slug") == "uso":
            return ["documentacao_uso.html"]
        return ["documentacao_page.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get("slug")
        entry = next((e for e in DOC_ENTRIES if e["slug"] == slug), None)
        if not entry:
            raise Http404("Página de documentação não encontrada.")
        context["entry"] = entry
        context["doc_entries"] = DOC_ENTRIES
        context["content_html"] = self._get_content(slug, entry)
        return context

    def _get_content(self, slug, entry):
        if entry["file"] is None:
            return None  # página 'uso' usa template próprio
        base_dir = getattr(settings, "BASE_DIR", Path(__file__).resolve().parent.parent)
        docs_dir = base_dir if isinstance(base_dir, Path) else Path(base_dir)
        md_path = docs_dir / "docs" / entry["file"]
        if not md_path.is_file():
            return f"<p>Arquivo não encontrado: {entry['file']}</p>"
        text = md_path.read_text(encoding="utf-8")
        return markdown.markdown(
            text,
            extensions=["tables", "fenced_code", "nl2br"],
            extension_configs={"tables": {}},
        )
