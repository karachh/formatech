from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q

from core.models import RegistroBase


class Usuario(RegistroBase, AbstractUser):
    class Perfil(models.TextChoices):
        COORDENADOR = "coordenador", "Coordenador"
        FORMADOR = "formador", "Formador"

    perfil = models.CharField(max_length=20, choices=Perfil, default=Perfil.FORMADOR)

    class Meta:
        constraints = [
            # choices só vale nos formulários; o CHECK impede outro valor gravado por fora.
            models.CheckConstraint(condition=Q(perfil__in=["coordenador", "formador"]), name="usuario_perfil_valido"),
        ]