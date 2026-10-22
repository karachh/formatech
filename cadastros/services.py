from django.core.exceptions import ValidationError

from . import repositories
from .models import MENSAGEM_SOBREPOSICAO, Ciclo


def listar_ciclos():
    return repositories.listar_ciclos()


def abrir_ciclo(nome, inicio, fim):
    """Cria um ciclo (RF002, CA001). Levanta ValidationError com a mensagem para o usuário."""
    ciclo = Ciclo(nome=(nome or "").strip(), inicio=inicio, fim=fim)
    # Sem full_clean(): ele consulta o banco para checar a sobreposição, e o NFM001
    # exige que a regra rode sem banco. Quem garante a RN002 é a EXCLUDE.
    ciclo.clean_fields()
    ciclo.clean()
    try:
        return repositories.salvar_ciclo(ciclo)
    except repositories.PeriodoOcupado:
        raise ValidationError(MENSAGEM_SOBREPOSICAO)
