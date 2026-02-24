"""
URL configuration for orca_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as accounts_views
from .views import DocumentacaoView, DocumentacaoPageView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', accounts_views.home_redirect, name='home'),
    path('', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('scheduler/', include('scheduler.urls')),
    path('documentacao/', DocumentacaoView.as_view(), name='documentacao'),
    path('documentacao/<slug:slug>/', DocumentacaoPageView.as_view(), name='documentacao_page'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

