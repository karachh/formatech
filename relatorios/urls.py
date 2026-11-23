from django.urls import path

from . import views

app_name = "relatorios"

urlpatterns = [
    path("relatorios/fechamento/", views.fechamento, name="fechamento"),
]
