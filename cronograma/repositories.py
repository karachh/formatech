from cadastros.models import Tema
from .models import Formacao


def listar_formacoes_do_ciclo(ciclo):
    """RN002: pertencem ao ciclo as formações com data entre o início e o fim, inclusive."""
    return list(
        Formacao.objects.filter(data__range=(ciclo.inicio, ciclo.fim))
        .select_related("tema", "formador")
        .order_by("data", "id")
    )


def buscar_formacao(formacao_id):
    return Formacao.objects.select_related("tema", "formador").get(pk=formacao_id)


def salvar_formacao(formacao):
    formacao.save()
    return formacao


def listar_temas_da_apostila():
    return list(Tema.objects.filter(tipo=Tema.Tipo.APOSTILA).order_by("rotulo", "nome"))


def listar_formacoes_com_tema_do_ciclo(ciclo):
    return list(
        Formacao.objects.filter(data__range=(ciclo.inicio, ciclo.fim), tema__isnull=False)
        .select_related("tema")
        .order_by("data", "id")
    )


def listar_formacoes_do_mes(ano, mes):
    """Formações do mês, sem as canceladas."""
    return list(
        Formacao.objects.filter(data__year=ano, data__month=mes)
        .exclude(situacao=Formacao.Situacao.CANCELADA)
        .select_related("tema", "formador")
        .order_by("data", "id")
    )