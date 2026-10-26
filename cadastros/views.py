from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from . import services
from .forms import CicloForm
from .models import Ciclo


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


# Só POST: um GET (link, pré-carregamento do navegador) não pode alterar dados.
@require_POST
def encerrar_ciclo(request, ciclo_id):
    try:
        ciclo = services.encerrar_ciclo(ciclo_id)
    except Ciclo.DoesNotExist:
        raise Http404("Ciclo não encontrado.")
    except ValidationError as erro:
        messages.error(request, erro.message)
    else:
        messages.success(request, f"Ciclo “{ciclo}” encerrado.")
    return redirect("cadastros:ciclos")
