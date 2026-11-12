from django.urls import path

from . import views

app_name = "cronograma"

urlpatterns = [
    path("cronograma/", views.cronograma, name="cronograma"),
    path("cronograma/<int:formacao_id>/editar/", views.editar_formacao, name="editar_formacao"),
    path("cobertura/", views.cobertura, name="cobertura"),
    path("exportar/", views.exportar, name="exportar"),
]
