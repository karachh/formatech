from django.urls import path

from . import views

app_name = 'cadastros'

urlpatterns = [
    path('ciclos/', views.ciclos, name='ciclos'),
    path('ciclos/<int:ciclo_id>/encerrar/', views.encerrar_ciclo, name='encerrar_ciclo'),
]
