from django.urls import path

from . import views

app_name = "cronograma"

urlpatterns = [
    path("cronograma/", views.cronograma, name="cronograma"),
    path("cronograma/<int:formacao_id>/editar/", views.editar_formacao, name="editar_formacao"),
    path("cronograma/<int:formacao_id>/escalar/", views.escalar_formador, name="escalar_formador"),
    path("cronograma/<int:formacao_id>/situacao/", views.alterar_situacao, name="alterar_situacao"),
    path("cobertura/", views.cobertura, name="cobertura"),
    path("historico/", views.historico, name="historico"),
    path("exportar/", views.exportar, name="exportar"),
    path("carga/", views.carga, name="carga"),
    path("meu-cronograma/", views.meu_cronograma, name="meu_cronograma"),
    path("cronograma/<int:formacao_id>/trocar/", views.trocar_formador, name="trocar_formador"),
]
