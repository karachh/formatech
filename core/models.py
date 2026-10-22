from django.db import models


class RegistroBase(models.Model):
    """Campos de auditoria herdados por todo modelo (RN008).

    O auto_now só age no save(): update() e save(update_fields=[...]) sem
    "atualizado_em" deixam o campo como estava.
    """

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
