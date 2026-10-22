from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from . import services
from .forms import CicloForm


def ciclos(request):
    form = CicloForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            ciclo = services.abrir_ciclo(**form.cleaned_data)
        except ValidationError as erro:
            form.add_error(None, erro)
        else:
            messages.success(request, f"Ciclo “{ciclo}” cadastrado.")
            # Redireciona após gravar: recarregar a página não reenvia o formulário.
            return redirect("cadastros:ciclos")
    return render(request, "cadastros/ciclos.html", {"form": form, "ciclos": services.listar_ciclos()})
