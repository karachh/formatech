from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from acesso.decorators import coordenador_required

from . import services
from .exportacao import gerar_pdf, gerar_planilha, nome_arquivo_relatorio
from .forms import CicloRelatorioForm


def _relatorio_exportacao(request):
    ciclos = services.listar_ciclos_encerrados()
    form = CicloRelatorioForm(request.GET or None, ciclos=ciclos)
    if not form.is_valid():
        return None, form
    if not form.cleaned_data["ciclo"]:
        form.add_error("ciclo", "Selecione um ciclo encerrado.")
        return None, form
    try:
        return services.consolidar_relatorio(form.cleaned_data["ciclo"]), form
    except ValidationError as erro:
        form.add_error("ciclo", erro)
        return None, form


@coordenador_required
def fechamento(request):
    ciclos = services.listar_ciclos_encerrados()
    form = CicloRelatorioForm(request.GET or None, ciclos=ciclos)
    relatorio = None

    if form.is_valid() and form.cleaned_data["ciclo"]:
        try:
            relatorio = services.consolidar_relatorio(form.cleaned_data["ciclo"])
        except ValidationError as erro:
            form.add_error("ciclo", erro)

    return render(
        request,
        "relatorios/fechamento.html",
        {"ciclos": ciclos, "form": form, "relatorio": relatorio},
    )


@coordenador_required
def excel(request):
    relatorio, form = _relatorio_exportacao(request)
    if relatorio is None:
        return HttpResponseBadRequest("; ".join(form.errors.get("ciclo", [])))

    resposta = HttpResponse(
        gerar_planilha(relatorio),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resposta["Content-Disposition"] = (
        f'attachment; filename="{nome_arquivo_relatorio(relatorio["ciclo"], "xlsx")}"'
    )
    return resposta


@coordenador_required
def pdf(request):
    relatorio, form = _relatorio_exportacao(request)
    if relatorio is None:
        return HttpResponseBadRequest("; ".join(form.errors.get("ciclo", [])))

    resposta = HttpResponse(gerar_pdf(relatorio), content_type="application/pdf")
    resposta["Content-Disposition"] = (
        f'attachment; filename="{nome_arquivo_relatorio(relatorio["ciclo"], "pdf")}"'
    )
    return resposta
