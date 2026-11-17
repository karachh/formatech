from django.db import models
from django.db.models import Q

from cadastros.models import Perseverante
from core.models import RegistroBase
from cronograma.models import Formacao


class Presenca(RegistroBase):
    """Uma linha por perseverante em cada formação."""

    class Situacao(models.TextChoices):
        PRESENTE = "presente", "Presente"
        AUSENTE = "ausente", "Ausente"
        JUSTIFICADO = "justificado", "Justificado"

    # PROTECT impede apagar uma formação com presença lançada.
    formacao = models.ForeignKey(Formacao, on_delete=models.PROTECT)
    # NFC002: a exclusão a pedido do perseverante apaga as presenças dele (decisão da US004).
    perseverante = models.ForeignKey(Perseverante, on_delete=models.CASCADE)
    situacao = models.CharField("situação", max_length=11, choices=Situacao)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["formacao", "perseverante"], name="presenca_unica_por_formacao"),
            # choices só vale nos formulários; o CHECK impede outro valor gravado por fora.
            models.CheckConstraint(
                condition=Q(situacao__in=["presente", "ausente", "justificado"]),
                name="presenca_situacao_valida",
            ),
        ]

    def __str__(self):
        return f"{self.perseverante} · {self.formacao} · {self.get_situacao_display()}"
