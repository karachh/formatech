from .models import Formacao


def listar_formacoes_do_ciclo(ciclo):
    """RN002: pertencem ao ciclo as formações com data entre o início e o fim, inclusive."""
    return list(
        Formacao.objects.filter(data__range=(ciclo.inicio, ciclo.fim))
        .select_related("tema", "formador")
        .order_by("data", "id")
    )


def buscar_formacao(formacao_id):
    """Levanta Formacao.DoesNotExist se o id não existir."""
    return Formacao.objects.select_related("tema", "formador").get(pk=formacao_id)


def salvar_formacao(formacao):
    formacao.save()
    return formacao
