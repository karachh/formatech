from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField, RangeBoundary, RangeOperators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Func, Q

from core.models import RegistroBase


class Periodo(Func):
    """Função daterange() do PostgreSQL: o intervalo entre duas datas."""

    function = "DATERANGE"
    output_field = DateRangeField()


class Ciclo(RegistroBase):
    nome = models.CharField(max_length=100)
    inicio = models.DateField("início")
    fim = models.DateField()

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(fim__gt=F("inicio")), name="ciclo_fim_depois_inicio"),
            # RN002: o ciclo de uma formação vem da data, então ciclos não se sobrepõem.
            # '[]' inclui o primeiro e o último dia: ciclos que se encostam no mesmo dia conflitam.
            ExclusionConstraint(
                name="ciclo_sem_sobreposicao",
                expressions=[
                    (
                        Periodo("inicio", "fim", RangeBoundary(inclusive_lower=True, inclusive_upper=True)),
                        RangeOperators.OVERLAPS,
                    ),
                ],
                violation_error_message="Já existe um ciclo nesse período.",
            ),
        ]

    def __str__(self):
        return self.nome

    def clean(self):
        # Espelha o CHECK ciclo_fim_depois_inicio, com mensagem amigável no campo fim.
        # O erro no campo fim faz o Django pular a validação da sobreposição, que quebraria
        # com DataError: o PostgreSQL não monta um daterange com o fim antes do início.
        if self.inicio and self.fim and self.fim <= self.inicio:
            raise ValidationError({"fim": "O fim do ciclo deve ser depois do início."})
