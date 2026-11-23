from django.core.exceptions import ValidationError
from django.shortcuts import render

from acesso.decorators import coordenador_required

from . import services
from .forms import CicloRelatorioForm


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
