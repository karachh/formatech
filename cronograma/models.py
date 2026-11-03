from django.db import models
from django.db.models import Q

from cadastros.models import Formador, Tema
from core.models import RegistroBase


class Formacao(RegistroBase):
    """O encontro: a entidade central do sistema.

    Não tem campo de ciclo: o ciclo é derivado da data (RN002). Guardar os dois
    criaria duas versões da mesma verdade.
    """

    class Situacao(models.TextChoices):
        PREVISTA = "prevista", "Prevista"
        REALIZADA = "realizada", "Realizada"
        CANCELADA = "cancelada", "Cancelada"

    data = models.DateField()
    # CA002: o tema pode ficar em branco. PROTECT impede apagar um tema já usado.
    tema = models.ForeignKey(Tema, on_delete=models.PROTECT, null=True, blank=True)
    # Opcional: a formação pode ser agendada e o formador escalado depois (US007).
    formador = models.ForeignKey(Formador, on_delete=models.PROTECT, null=True, blank=True)
    situacao = models.CharField("situação", max_length=10, choices=Situacao, default=Situacao.PREVISTA)
    descricao = models.CharField("descrição", max_length=200, blank=True)

    class Meta:
        constraints = [
            # choices só vale nos formulários; o CHECK impede outro valor gravado por fora.
            models.CheckConstraint(
                condition=Q(situacao__in=["prevista", "realizada", "cancelada"]),
                name="formacao_situacao_valida",
            ),
        ]

    def __str__(self):
        return f"{self.data:%d/%m/%Y} · {self.tema or 'Sem tema'}"