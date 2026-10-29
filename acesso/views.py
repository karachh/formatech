from django.contrib.auth import login as login_django, logout as logout_django
from django.contrib.auth.decorators import login_not_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from . import services
from .forms import LoginForm


@login_not_required
def login(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            usuario = services.autenticar(**form.cleaned_data)
        except ValidationError as erro:
            form.add_error(None, erro)
        else:
            login_django(request, usuario)
            return redirect("acesso:home")
    return render(request, "acesso/login.html", {"form": form})


@require_POST
def logout(request):
    logout_django(request)
    return redirect("acesso:login")


def home(request):
    return render(request, "acesso/home.html")