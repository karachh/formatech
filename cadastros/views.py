from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from acesso.decorators import coordenador_required

from . import services
from .forms import CicloForm, TemaForm
from .models import Ciclo, Tema

@coordenador_required
def ciclos(request):
    form = CicloForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            ciclo = services.abrir_ciclo(**form.cleaned_data)
        except ValidationError as erro:
            form.add_error(None, erro)
        else:
            messages.success(request, f"Ciclo “{ciclo}” cadastrado.")
        
            return redirect("cadastros:ciclos")
    return render(request, "cadastros/ciclos.html", {"form": form, "ciclos": services.listar_ciclos()})


@coordenador_required
def editar_ciclo(request, ciclo_id):
    try:
        ciclo = services.buscar_ciclo(ciclo_id)
    except Ciclo.DoesNotExist:
        raise Http404("Ciclo não encontrado.")
    form = CicloForm(
        request.POST or None,
        initial={"nome": ciclo.nome, "inicio": ciclo.inicio, "fim": ciclo.fim},
        datas_editaveis=ciclo.datas_editaveis,
    )
    if request.method == "POST" and form.is_valid():
        try:
            ciclo = services.editar_ciclo(ciclo_id, **form.cleaned_data)
        except ValidationError as erro:
            form.add_error(None, erro)
        else:
            messages.success(request, f"Ciclo “{ciclo}” alterado.")
            return redirect("cadastros:ciclos")
    return render(request, "cadastros/editar_ciclo.html", {"form": form, "ciclo": ciclo})


@coordenador_required
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



@coordenador_required
def temas(request):
    form = TemaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            tema = services.cadastrar_tema(**form.cleaned_data)
        except ValidationError as erro:
            form.add_error(None, erro)
        else:
            messages.success(request, f"Tema “{tema}” cadastrado.")
            return redirect("cadastros:temas")
    return render(request, "cadastros/temas.html", {"form": form, "temas": services.listar_temas()})


@coordenador_required
def editar_tema(request, tema_id):
    try:
        tema = services.buscar_tema(tema_id)
    except Tema.DoesNotExist:
        raise Http404("Tema não encontrado.")
    form = TemaForm(
        request.POST or None,
        initial={"nome": tema.nome, "tipo": tema.tipo, "rotulo": tema.rotulo},
    )
    if request.method == "POST" and form.is_valid():
        try:
            tema = services.editar_tema(tema_id, **form.cleaned_data)
        except ValidationError as erro:
            form.add_error(None, erro)
        else:
            messages.success(request, f"Tema “{tema}” alterado.")
            return redirect("cadastros:temas")
    return render(request, "cadastros/editar_tema.html", {"form": form, "tema": tema})