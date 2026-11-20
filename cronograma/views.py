from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from acesso.decorators import coordenador_required
from cadastros.forms import CicloFiltroForm
from cadastros.models import Formador, Tema

from . import services
from .forms import (
    AgendamentoForm,
    EscalacaoForm,
    FormacaoForm,
    HistoricoFormadorForm,
    HistoricoTemaForm,
    SituacaoForm,
)
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
            "situacoes": Formacao.Situacao.choices,
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


@coordenador_required
def escalar_formador(request, formacao_id):
    try:
        formacao = services.buscar_formacao(formacao_id)
    except Formacao.DoesNotExist:
        raise Http404("Formação não encontrada.")

    formadores = services.listar_formadores_ativos()
    form = EscalacaoForm(
        request.POST if request.method == "POST" else request.GET or None,
        formadores=formadores,
    )
    dados = None

    if request.method == "POST" and form.is_valid():
        try:
            formacao = services.escalar_formador(formacao_id, form.cleaned_data["formador_id"])
        except ValidationError as erro:
            form.add_error(None, erro)
        else:
            messages.success(request, f"Formador “{formacao.formador}” escalado.")
            return redirect(_url_do_cronograma(services.ciclo_da_formacao(formacao)))
    elif request.method == "GET" and request.GET and form.is_valid():
        try:
            dados = services.dados_para_escalacao(formacao_id, form.cleaned_data["formador_id"])
        except ValidationError as erro:
            form.add_error(None, erro)

    return render(
        request,
        "cronograma/escalar_formador.html",
        {"form": form, "formacao": formacao, "dados": dados},
    )


@coordenador_required
@require_POST
def alterar_situacao(request, formacao_id):
    form = SituacaoForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Selecione uma situação válida.")
        return redirect(reverse("cronograma:cronograma"))

    try:
        formacao = services.alterar_situacao(formacao_id, form.cleaned_data["situacao"])
    except Formacao.DoesNotExist:
        raise Http404("Formação não encontrada.")
    except ValidationError as erro:
        messages.error(request, " ".join(erro.messages))
        return redirect(reverse("cronograma:cronograma"))

    messages.success(request, f"Situação alterada para {formacao.get_situacao_display()}.")
    return redirect(_url_do_cronograma(services.ciclo_da_formacao(formacao)))


def cobertura(request):
    ciclos = services.listar_ciclos()
    ciclo_id = request.GET.get("ciclo") or None
    ciclo = services.ciclo_do_cronograma(ciclo_id)
    contexto = {"ciclos": ciclos, "ciclo": ciclo, "cobertura": None}
    if ciclo is not None:
        contexto["cobertura"] = services.classificar_cobertura(ciclo)
    return render(request, "cronograma/cobertura.html", contexto)


@require_GET
def historico(request):
    formadores = services.listar_formadores()
    temas = services.listar_temas()
    formador_form = HistoricoFormadorForm(request.GET or None, formadores=formadores)
    tema_form = HistoricoTemaForm(request.GET or None, temas=temas)
    formador = None
    tema = None
    historico_temas = None
    historico_formadores = None

    if formador_form.is_valid() and formador_form.cleaned_data["formador_id"]:
        try:
            formador = services.buscar_formador(formador_form.cleaned_data["formador_id"])
        except Formador.DoesNotExist:
            raise Http404("Formador não encontrado.")
        historico_temas = services.historico_temas_por_formador(formador.pk)

    if tema_form.is_valid() and tema_form.cleaned_data["tema_id"]:
        try:
            tema = services.buscar_tema(tema_form.cleaned_data["tema_id"])
        except Tema.DoesNotExist:
            raise Http404("Tema não encontrado.")
        historico_formadores = services.historico_formadores_por_tema(tema.pk)

    return render(
        request,
        "cronograma/historico.html",
        {
            "formador_form": formador_form,
            "tema_form": tema_form,
            "formador": formador,
            "tema": tema,
            "historico_temas": historico_temas,
            "historico_formadores": historico_formadores,
        },
    )


@coordenador_required
def exportar(request):
    ano, mes = services.mes_da_exportacao(request.GET.get("mes"))
    texto = services.exportar_cronograma_do_mes(ano, mes)
    return render(request, "cronograma/exportar.html", {"mes": f"{ano:04d}-{mes:02d}", "texto": texto})


@coordenador_required
def carga(request):
    ciclos = services.listar_ciclos()
    ciclo = services.ciclo_do_cronograma(request.GET.get("ciclo") or None)
    contexto = {"ciclos": ciclos, "ciclo": ciclo, "carga": None}
    if ciclo is not None:
        contexto["carga"] = services.carga_por_formador(ciclo)
    return render(request, "cronograma/carga.html", contexto)