from django.urls import path

from . import views

app_name = "acesso"

urlpatterns = [
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("home/", views.home, name="home"),
]