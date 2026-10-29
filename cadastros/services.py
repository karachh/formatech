from django.core.exceptions import ValidationError

from . import repositories
from .models import MENSAGEM_SOBREPOSICAO, MENSAGEM_TEMA_REPETIDO, Ciclo, Tema


def listar_ciclos():
    return repositories.listar_ciclos()


def buscar_ciclo(ciclo_id):
    """Ciclo inexistente propaga Ciclo.DoesNotExist."""
    return repositories.buscar_ciclo(ciclo_id)


def abrir_ciclo(nome, inicio, fim):
    """Cria um ciclo (RF002, CA001). Levanta ValidationError com a mensagem para o usuário."""
    return _validar_e_salvar(Ciclo(nome=(nome or "").strip(), inicio=inicio, fim=fim))


def editar_ciclo(ciclo_id, nome, inicio, fim):
    """Altera nome e datas (RF002, T002.8). Ciclo encerrado só aceita mudança no nome."""
    ciclo = repositories.buscar_ciclo(ciclo_id)
    if not ciclo.datas_editaveis and (inicio, fim) != (ciclo.inicio, ciclo.fim):
        raise ValidationError("Ciclo encerrado: as datas não podem ser alteradas.")
    ciclo.nome, ciclo.inicio, ciclo.fim = (nome or "").strip(), inicio, fim
    return _validar_e_salvar(ciclo)


def encerrar_ciclo(ciclo_id):
    """Encerra um ciclo aberto (RF002, T002.7). Ciclo inexistente propaga Ciclo.DoesNotExist."""
    ciclo = repositories.buscar_ciclo(ciclo_id)
    if ciclo.situacao == Ciclo.Situacao.ENCERRADO:
        raise ValidationError(f"O ciclo “{ciclo}” já está encerrado.")
    ciclo.situacao = Ciclo.Situacao.ENCERRADO
    return repositories.salvar_ciclo(ciclo)


def _validar_e_salvar(ciclo):
    # Sem full_clean(): ele consulta o banco para checar a sobreposição, e o NFM001
    # exige que a regra rode sem banco. Quem garante a RN002 é a EXCLUDE.
    ciclo.clean_fields()
    ciclo.clean()
    try:
        return repositories.salvar_ciclo(ciclo)
    except repositories.PeriodoOcupado:
        raise ValidationError(MENSAGEM_SOBREPOSICAO)


def listar_temas():
    return repositories.listar_temas()


def buscar_tema(tema_id):
    """Tema inexistente propaga Tema.DoesNotExist."""
    return repositories.buscar_tema(tema_id)


def cadastrar_tema(nome, tipo, rotulo=""):
    """Cria um tema (RF005)."""
    return _validar_e_salvar_tema(Tema(nome=(nome or "").strip(), tipo=tipo, rotulo=(rotulo or "").strip()))


def editar_tema(tema_id, nome, tipo, rotulo=""):
    """Altera um tema (RF005)."""
    tema = repositories.buscar_tema(tema_id)
    tema.nome, tema.tipo, tema.rotulo = (nome or "").strip(), tipo, (rotulo or "").strip()
    return _validar_e_salvar_tema(tema)


def carregar_temas(linhas):
    """Carga inicial: cria os temas que ainda não existem. Devolve quantos foram criados."""
    criados = 0
    for linha in linhas:
        nome = (linha["nome"] or "").strip()
        if nome and not repositories.existe_tema(nome):
            cadastrar_tema(nome, linha["tipo"], linha.get("rotulo", ""))
            criados += 1
    return criados


def _validar_e_salvar_tema(tema):
    tema.clean_fields()
    try:
        return repositories.salvar_tema(tema)
    except repositories.NomeDeTemaEmUso:
        raise ValidationError(MENSAGEM_TEMA_REPETIDO)
