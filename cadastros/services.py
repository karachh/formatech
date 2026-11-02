from django.core.exceptions import ValidationError

from . import repositories
from .models import (
    MENSAGEM_SOBREPOSICAO,
    MENSAGEM_TEMA_REPETIDO,
    Ciclo,
    Formador,
    Perseverante,
    Tema,
)


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


def listar_formadores():
    return repositories.listar_formadores()


def buscar_formador(formador_id):
    """Formador inexistente propaga Formador.DoesNotExist."""
    return repositories.buscar_formador(formador_id)


def cadastrar_formador(nome, inicio_servico, capacitado):
    formador = Formador(
        nome=(nome or "").strip(),
        inicio_servico=inicio_servico,
        capacitado=capacitado,
    )
    formador.clean_fields()
    return repositories.salvar_formador(formador)


def editar_formador(formador_id, nome, inicio_servico, capacitado):
    formador = repositories.buscar_formador(formador_id)
    formador.nome = (nome or "").strip()
    formador.inicio_servico = inicio_servico
    formador.capacitado = capacitado
    formador.clean_fields()
    return repositories.salvar_formador(formador)


def inativar_formador(formador_id):
    formador = repositories.buscar_formador(formador_id)
    if not formador.ativo:
        raise ValidationError(f'O formador "{formador}" já está inativo.')
    return repositories.inativar_formador(formador)


def listar_perseverantes(ciclo_id):
    return repositories.listar_perseverantes(ciclo_id)


def listar_perseverantes_ativos(ciclo_id):
    return repositories.listar_perseverantes_ativos(ciclo_id)


def buscar_perseverante(perseverante_id):
    """Perseverante inexistente propaga Perseverante.DoesNotExist."""
    return repositories.buscar_perseverante(perseverante_id)


def cadastrar_perseverante(nome, ciclo_id):
    ciclo = _buscar_ciclo_perseverante(ciclo_id)
    perseverante = Perseverante(nome=(nome or "").strip(), ciclo=ciclo)
    perseverante.clean_fields(exclude=["ciclo"])
    return repositories.salvar_perseverante(perseverante)


def editar_perseverante(perseverante_id, nome, ciclo_id):
    perseverante = repositories.buscar_perseverante(perseverante_id)
    perseverante.nome = (nome or "").strip()
    perseverante.ciclo = _buscar_ciclo_perseverante(ciclo_id)
    perseverante.clean_fields(exclude=["ciclo"])
    return repositories.salvar_perseverante(perseverante)


def inativar_perseverante(perseverante_id):
    perseverante = repositories.buscar_perseverante(perseverante_id)
    if not perseverante.ativo:
        raise ValidationError(f'O perseverante "{perseverante}" já está inativo.')
    return repositories.inativar_perseverante(perseverante)


def _buscar_ciclo_perseverante(ciclo_id):
    if not ciclo_id:
        raise ValidationError({"ciclo_id": "Selecione um ciclo."})
    try:
        return repositories.buscar_ciclo(ciclo_id)
    except (Ciclo.DoesNotExist, TypeError, ValueError):
        raise ValidationError({"ciclo_id": "Selecione um ciclo válido."})
