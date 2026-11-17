from django.db import transaction

from .models import Presenca


def situacoes_da_formacao(formacao_id):
    """{perseverante_id: situacao} do que já foi lançado na formação."""
    return dict(
        Presenca.objects.filter(formacao_id=formacao_id).values_list("perseverante_id", "situacao")
    )


def salvar_presencas(formacao_id, situacoes):
    # NFR001: se uma linha falhar, o atomic() desfaz todas as outras.
    with transaction.atomic():
        for perseverante_id, situacao in situacoes.items():
            # Cria na primeira vez; na reabertura (T014.4), corrige a linha existente.
            Presenca.objects.update_or_create(
                formacao_id=formacao_id,
                perseverante_id=perseverante_id,
                defaults={"situacao": situacao},
            )
