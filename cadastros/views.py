from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from acesso.decorators import coordenador_required

from . import services
from .forms import CicloFiltroForm, CicloForm, FormadorForm, PerseveranteForm, TemaForm
from .models import Ciclo, Formador, Perseverante, Tema

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


@coordenador_required
def formadores(request):
    form = FormadorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            formador = services.cadastrar_formador(**form.cleaned_data)
        except ValidationError as erro:
            form.add_error(None, erro)
        else:
            messages.success(request, f"Formador “{formador}” cadastrado.")
            return redirect("cadastros:formadores")
    return render(
        request,
        "cadastros/formadores.html",
        {"form": form, "formadores": services.listar_formadores()},
    )


@coordenador_required
def editar_formador(request, formador_id):
    try:
        formador = services.buscar_formador(formador_id)
    except Formador.DoesNotExist:
        raise Http404("Formador não encontrado.")
    form = FormadorForm(
        request.POST or None,
        initial={
            "nome": formador.nome,
            "inicio_servico": formador.inicio_servico,
            "capacitado": formador.capacitado,
        },
    )
    if request.method == "POST" and form.is_valid():
        try:
            formador = services.editar_formador(formador_id, **form.cleaned_data)
        except ValidationError as erro:
            form.add_error(None, erro)
        else:
            messages.success(request, f"Formador “{formador}” alterado.")
            return redirect("cadastros:formadores")
    return render(
        request,
        "cadastros/editar_formador.html",
        {"form": form, "formador": formador},
    )


@coordenador_required
@require_POST
def inativar_formador(request, formador_id):
    try:
        formador = services.inativar_formador(formador_id)
    except Formador.DoesNotExist:
        raise Http404("Formador não encontrado.")
    except ValidationError as erro:
        messages.error(request, erro.message)
    else:
        messages.success(request, f"Formador “{formador}” inativado.")
    return redirect("cadastros:formadores")


@coordenador_required
def perseverantes(request):
    ciclos = services.listar_ciclos()
    filtro = CicloFiltroForm(request.GET or None, ciclos=ciclos)
    ciclo = None
    participantes = []
    if filtro.is_bound and filtro.is_valid() and filtro.cleaned_data["ciclo"]:
        ciclo = services.buscar_ciclo(filtro.cleaned_data["ciclo"])
        participantes = services.listar_perseverantes(ciclo.pk)

    form = PerseveranteForm(
        request.POST or None,
        ciclos=ciclos,
        initial={"ciclo_id": ciclo.pk if ciclo else None},
    )
    if request.method == "POST" and form.is_valid():
        try:
            participante = services.cadastrar_perseverante(**form.cleaned_data)
        except ValidationError as erro:
            form.add_error(None, erro)
        else:
            messages.success(request, f"Perseverante “{participante}” cadastrado.")
            return redirect(f"{reverse('cadastros:perseverantes')}?ciclo={participante.ciclo_id}")
    return render(
        request,
        "cadastros/perseverantes.html",
        {
            "form": form,
            "filtro": filtro,
            "ciclos": ciclos,
            "ciclo": ciclo,
            "perseverantes": participantes,
        },
    )


@coordenador_required
def editar_perseverante(request, perseverante_id):
    try:
        participante = services.buscar_perseverante(perseverante_id)
    except Perseverante.DoesNotExist:
        raise Http404("Perseverante não encontrado.")
    ciclos = services.listar_ciclos()
    form = PerseveranteForm(
        request.POST or None,
        ciclos=ciclos,
        initial={"nome": participante.nome, "ciclo_id": participante.ciclo_id},
    )
    if request.method == "POST" and form.is_valid():
        try:
            participante = services.editar_perseverante(perseverante_id, **form.cleaned_data)
        except ValidationError as erro:
            form.add_error(None, erro)
        else:
            messages.success(request, f"Perseverante “{participante}” alterado.")
            return redirect(f"{reverse('cadastros:perseverantes')}?ciclo={participante.ciclo_id}")
    return render(
        request,
        "cadastros/editar_perseverante.html",
        {"form": form, "participante": participante},
    )


@coordenador_required
@require_POST
def inativar_perseverante(request, perseverante_id):
    try:
        participante = services.inativar_perseverante(perseverante_id)
    except Perseverante.DoesNotExist:
        raise Http404("Perseverante não encontrado.")
    except ValidationError as erro:
        messages.error(request, erro.message)
    else:
        messages.success(request, f"Perseverante “{participante}” inativado.")
    return redirect(f"{reverse('cadastros:perseverantes')}?ciclo={participante.ciclo_id}")


@coordenador_required
@require_POST
def excluir_perseverante(request, perseverante_id):
    try:
        participante = services.excluir_perseverante(perseverante_id)
    except Perseverante.DoesNotExist:
        raise Http404("Perseverante não encontrado.")
    messages.success(request, "Perseverante excluído a pedido.")
    return redirect(f"{reverse('cadastros:perseverantes')}?ciclo={participante.ciclo_id}")
