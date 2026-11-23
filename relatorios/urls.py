from django.urls import path

from . import views

app_name = "relatorios"

urlpatterns = [
    path("relatorios/fechamento/", views.fechamento, name="fechamento"),
    path("relatorios/fechamento/excel/", views.excel, name="excel"),
]
