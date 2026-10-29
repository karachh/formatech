from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField, RangeBoundary, RangeOperators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Func, Q

from core.models import RegistroBase

MENSAGEM_SOBREPOSICAO = "Já existe um ciclo nesse período."
MENSAGEM_TEMA_REPETIDO = "Já existe um tema com esse nome."


class Periodo(Func):
    """Função daterange() do PostgreSQL: o intervalo entre duas datas."""

    function = "DATERANGE"
    output_field = DateRangeField()


class Ciclo(RegistroBase):
    class Situacao(models.TextChoices):
        ABERTO = "aberto", "Aberto"
        ENCERRADO = "encerrado", "Encerrado"

    nome = models.CharField(max_length=100)
    inicio = models.DateField("início")
    fim = models.DateField()
    situacao = models.CharField("situação", max_length=10, choices=Situacao, default=Situacao.ABERTO)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(fim__gt=F("inicio")), name="ciclo_fim_depois_inicio"),
            # choices só vale nos formulários; o CHECK impede outro valor gravado por fora.
            models.CheckConstraint(condition=Q(situacao__in=["aberto", "encerrado"]), name="ciclo_situacao_valida"),
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
                violation_error_message=MENSAGEM_SOBREPOSICAO,
            ),
        ]

    def __str__(self):
        return self.nome

    @property
    def datas_editaveis(self):
        # As datas definem quais formações pertencem ao ciclo (RN002): após o encerramento, ficam congeladas.
        return self.situacao == self.Situacao.ABERTO

    def clean(self):
        # Espelha o CHECK ciclo_fim_depois_inicio, com mensagem amigável no campo fim.
        # O erro no campo fim faz o Django pular a validação da sobreposição, que quebraria
        # com DataError: o PostgreSQL não monta um daterange com o fim antes do início.
        if self.inicio and self.fim and self.fim <= self.inicio:
            raise ValidationError({"fim": "O fim do ciclo deve ser depois do início."})


class Tema(RegistroBase):
    class Tipo(models.TextChoices):
        APOSTILA = "apostila", "Apostila"
        OPCIONAL = "opcional", "Opcional"

    nome = models.CharField(max_length=150)
    tipo = models.CharField(max_length=10, choices=Tipo, default=Tipo.APOSTILA)
    rotulo = models.CharField("rótulo na apostila", max_length=50, blank=True)

    class Meta:
        constraints = [
            # choices só vale nos formulários; o CHECK impede outro valor gravado por fora.
            models.CheckConstraint(condition=Q(tipo__in=["apostila", "opcional"]), name="tema_tipo_valido"),
            models.UniqueConstraint(fields=["nome"], name="tema_nome_unico", violation_error_message=MENSAGEM_TEMA_REPETIDO),
        ]

    def __str__(self):
        return self.nome