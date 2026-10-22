from django.urls import path

from . import views

app_name = 'cadastros'

urlpatterns = [
    path('ciclos/', views.ciclos, name='ciclos'),
]
