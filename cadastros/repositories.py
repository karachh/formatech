from django.db import IntegrityError, transaction

from .models import Ciclo


class PeriodoOcupado(Exception):
    """O banco recusou o ciclo pela EXCLUDE ciclo_sem_sobreposicao (RN002)."""


def listar_ciclos():
    return list(Ciclo.objects.order_by("-inicio"))


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
