from django.urls import path

from . import views

app_name = "presenca"

urlpatterns = [
    path("presenca/<int:formacao_id>/", views.lancar_presenca, name="lancar_presenca"),
]
