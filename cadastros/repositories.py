from django.db import IntegrityError, transaction

from .models import Ciclo, Tema


class PeriodoOcupado(Exception):
    """O banco recusou o ciclo pela EXCLUDE ciclo_sem_sobreposicao (RN002)."""


def listar_ciclos():
    return list(Ciclo.objects.order_by("-inicio"))


def buscar_ciclo(ciclo_id):
    """Levanta Ciclo.DoesNotExist se o id não existir."""
    return Ciclo.objects.get(pk=ciclo_id)


def salvar_ciclo(ciclo):
    try:
        # O atomic() isola a falha: sem ele, a transação de quem chamou fica inutilizável.
        with transaction.atomic():
            ciclo.save()
    except IntegrityError as erro:
        # O psycopg informa qual restrição recusou a gravação.
        restricao = getattr(getattr(erro.__cause__, "diag", None), "constraint_name", None)
        if restricao == "ciclo_sem_sobreposicao":
            raise PeriodoOcupado from erro
        raise
    return ciclo


class NomeDeTemaEmUso(Exception):
    """O banco recusou o tema pela UNIQUE tema_nome_unico."""


def listar_temas():
    return list(Tema.objects.order_by("nome"))


def buscar_tema(tema_id):
    """Levanta Tema.DoesNotExist se o id não existir."""
    return Tema.objects.get(pk=tema_id)


def existe_tema(nome):
    return Tema.objects.filter(nome=nome).exists()


def salvar_tema(tema):
    try:
        with transaction.atomic():
            tema.save()
    except IntegrityError as erro:
        restricao = getattr(getattr(erro.__cause__, "diag", None), "constraint_name", None)
        if restricao == "tema_nome_unico":
            raise NomeDeTemaEmUso from erro
        raise
    return tema
