from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render

from acesso.decorators import coordenador_required
from cronograma.models import Formacao

from . import services
from .forms import PresencaForm


@coordenador_required
def lancar_presenca(request, formacao_id):
    try:
        formacao = services.buscar_formacao(formacao_id)
    except Formacao.DoesNotExist:
        raise Http404("Formação não encontrada.")

    try:
        grade = services.grade_de_presenca(formacao)
    except ValidationError as erro:
        grade = []
        messages.error(request, " ".join(erro.messages))

    form = PresencaForm(request.POST or None, grade=grade)
    if request.method == "POST" and grade and form.is_valid():
        try:
            services.lancar_presencas(formacao_id, form.situacoes())
        except ValidationError as erro:
            form.add_error(None, erro)
        else:
            messages.success(request, f"Presença da formação de {formacao.data:%d/%m/%Y} gravada.")
            # Volta para a própria tela: reabrir mostra o que foi salvo (T014.4).
            return redirect("presenca:lancar_presenca", formacao_id=formacao.pk)
    return render(request, "presenca/lancar_presenca.html", {"form": form, "formacao": formacao})
