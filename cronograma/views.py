from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from acesso.decorators import coordenador_required
from cadastros.forms import CicloFiltroForm

from . import services
from .forms import AgendamentoForm, FormacaoForm
from .models import Formacao


def _url_do_cronograma(ciclo):
    return f"{reverse('cronograma:cronograma')}?ciclo={ciclo.pk}"


@coordenador_required
def cronograma(request):
    ciclos = services.listar_ciclos()
    filtro = CicloFiltroForm(request.GET or None, ciclos=ciclos)
    ciclo_id = filtro.cleaned_data["ciclo"] if filtro.is_valid() else None
    ciclo = services.ciclo_do_cronograma(ciclo_id)

    form = AgendamentoForm(
        request.POST or None,
        temas=services.listar_temas(),
        formadores=services.listar_formadores_ativos(),
    )
    if request.method == "POST" and form.is_valid():
        try:
            formacao = services.agendar_formacao(**form.cleaned_data)
        except ValidationError as erro:
            form.add_error(None, erro)
        else:
            messages.success(request, f"Formação de {formacao.data:%d/%m/%Y} agendada.")
            return redirect(_url_do_cronograma(services.ciclo_da_formacao(formacao)))
    return render(
        request,
        "cronograma/cronograma.html",
        {
            "form": form,
            "filtro": filtro,
            "ciclo": ciclo,
            "formacoes": services.listar_formacoes_do_ciclo(ciclo) if ciclo else [],
        },
    )


@coordenador_required
def editar_formacao(request, formacao_id):
    try:
        formacao = services.buscar_formacao(formacao_id)
    except Formacao.DoesNotExist:
        raise Http404("Formação não encontrada.")
    form = FormacaoForm(
        request.POST or None,
        temas=services.listar_temas(),
        initial={"data": formacao.data, "tema_id": formacao.tema_id, "descricao": formacao.descricao},
    )
    if request.method == "POST" and form.is_valid():
        try:
            formacao = services.editar_formacao(formacao_id, **form.cleaned_data)
        except ValidationError as erro:
            form.add_error(None, erro)
        else:
            messages.success(request, f"Formação de {formacao.data:%d/%m/%Y} alterada.")
            return redirect(_url_do_cronograma(services.ciclo_da_formacao(formacao)))
    return render(request, "cronograma/editar_formacao.html", {"form": form, "formacao": formacao})
