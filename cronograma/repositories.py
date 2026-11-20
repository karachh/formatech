from cadastros.models import Tema
from .models import Formacao
from django.db.models import Count


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


def _formacoes_realizadas():
    return Formacao.objects.filter(situacao=Formacao.Situacao.REALIZADA)


def listar_temas_ministrados_por_formador(formador_id):
    return list(
        _formacoes_realizadas()
        .filter(formador_id=formador_id, tema__isnull=False)
        .values_list("tema__nome", flat=True)
        .distinct()
        .order_by("tema__nome")
    )


def listar_historico_temas_por_formador(formador_id):
    return list(
        _formacoes_realizadas()
        .filter(formador_id=formador_id, tema__isnull=False)
        .select_related("tema")
        .order_by("-data", "-pk")
    )


def listar_historico_formadores_por_tema(tema_id):
    return list(
        _formacoes_realizadas()
        .filter(tema_id=tema_id, formador__isnull=False)
        .select_related("formador")
        .order_by("-data", "-pk")
    )


def contar_formacoes_do_formador_no_ciclo(formador_id, ciclo):
    return (
        Formacao.objects.filter(
            formador_id=formador_id,
            data__range=(ciclo.inicio, ciclo.fim),
        )
        .exclude(situacao=Formacao.Situacao.CANCELADA)
        .count()
    )


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

def contar_formacoes_por_formador(ciclo):
    linhas = (
        Formacao.objects.filter(
            data__range=(ciclo.inicio, ciclo.fim),
            situacao=Formacao.Situacao.REALIZADA,
            formador__isnull=False,
        )
        .values("formador_id")
        .annotate(total=Count("id"))
    )
    return {linha["formador_id"]: linha["total"] for linha in linhas}