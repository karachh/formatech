from django.urls import path

from . import views

app_name = 'cadastros'

urlpatterns = [
    path('ciclos/', views.ciclos, name='ciclos'),
    path('ciclos/<int:ciclo_id>/editar/', views.editar_ciclo, name='editar_ciclo'),
    path('ciclos/<int:ciclo_id>/encerrar/', views.encerrar_ciclo, name='encerrar_ciclo'),
    path('temas/', views.temas, name='temas'),
    path('temas/<int:tema_id>/editar/', views.editar_tema, name='editar_tema'),
    path('formadores/', views.formadores, name='formadores'),
    path('formadores/<int:formador_id>/editar/', views.editar_formador, name='editar_formador'),
    path('formadores/<int:formador_id>/inativar/', views.inativar_formador, name='inativar_formador'),
    path('perseverantes/', views.perseverantes, name='perseverantes'),
    path('perseverantes/<int:perseverante_id>/editar/', views.editar_perseverante, name='editar_perseverante'),
    path('perseverantes/<int:perseverante_id>/inativar/', views.inativar_perseverante, name='inativar_perseverante'),
]
