from django.core.exceptions import ValidationError
from django.utils import timezone

from cadastros import services as cadastros
from cadastros.models import Formador, Tema

from . import repositories
from .models import Formacao

MENSAGEM_SEM_CICLO = "Não há ciclo cadastrado para esta data."


# Consultas de apoio à tela. A view só conversa com este serviço;
# o que é da app cadastros passa pelo serviço dela.
def listar_ciclos():
    return cadastros.listar_ciclos()


def listar_temas():
    return cadastros.listar_temas()


def listar_formadores_ativos():
    return cadastros.listar_formadores_ativos()


def ciclo_do_cronograma(ciclo_id=None):
    """O ciclo escolhido na tela; sem escolha, o ciclo que contém o dia de hoje (ou None)."""
    if ciclo_id:
        return cadastros.buscar_ciclo(ciclo_id)
    return cadastros.buscar_ciclo_da_data(timezone.localdate())


def ciclo_da_formacao(formacao):
    """RN002: o ciclo não é guardado na formação, é derivado da data."""
    return cadastros.buscar_ciclo_da_data(formacao.data)


def listar_formacoes_do_ciclo(ciclo):
    return repositories.listar_formacoes_do_ciclo(ciclo)


def buscar_formacao(formacao_id):
    """Formação inexistente propaga Formacao.DoesNotExist."""
    return repositories.buscar_formacao(formacao_id)


def agendar_formacao(data, tema_id, formador_id, descricao=""):
    """Agenda uma formação (RF006). Toda formação nasce prevista (T006.3)."""
    formacao = Formacao(
        data=data,
        tema=_buscar_tema(tema_id),
        formador=_buscar_formador(formador_id),
        descricao=(descricao or "").strip(),
        situacao=Formacao.Situacao.PREVISTA,
    )
    return _validar_e_salvar(formacao)


def editar_formacao(formacao_id, data, tema_id, descricao=""):
    """Altera data, tema e descrição.

    Formador e situação ficam com a escalação (US007): a troca de formador
    precisa ser registrada como fato (RN007), e não sobrescrita aqui.
    """
    formacao = repositories.buscar_formacao(formacao_id)
    formacao.data = data
    formacao.tema = _buscar_tema(tema_id)
    formacao.descricao = (descricao or "").strip()
    return _validar_e_salvar(formacao)


def _validar_e_salvar(formacao):
    # tema e formador já foram conferidos; excluí-los evita consultar o banco de novo.
    formacao.clean_fields(exclude=["tema", "formador"])
    # Integridade estrutural, não regra opinativa (RN001): sem ciclo, a formação
    # não apareceria em cronograma nenhum.
    if ciclo_da_formacao(formacao) is None:
        raise ValidationError({"data": MENSAGEM_SEM_CICLO})
    return repositories.salvar_formacao(formacao)


def _buscar_tema(tema_id):
    if not tema_id:
        return None  # CA002: o tema pode ficar em branco.
    try:
        return cadastros.buscar_tema(tema_id)
    except (Tema.DoesNotExist, TypeError, ValueError):
        raise ValidationError({"tema_id": "Selecione um tema válido."})


def _buscar_formador(formador_id):
    if not formador_id:
        return None  # Escalado depois, na US007.
    try:
        formador = cadastros.buscar_formador(formador_id)
    except (Formador.DoesNotExist, TypeError, ValueError):
        raise ValidationError({"formador_id": "Selecione um formador válido."})
    if not formador.ativo:
        raise ValidationError({"formador_id": "Este formador está inativo."})
    return formador



def classificar_cobertura(ciclo):
    """RN005: sempre calculado, nunca armazenado.

    Devolve {"nao_alocados": [...], "agendados": [...], "realizados": [...]}.
    Cancelada não cobre nada. Se um tema tem várias formações, vale a mais
    avançada: realizada > prevista.
    """
    temas = repositories.listar_temas_da_apostila()
    situacao_por_tema = {}
    for formacao in repositories.listar_formacoes_com_tema_do_ciclo(ciclo):
        if formacao.situacao == Formacao.Situacao.REALIZADA:
            situacao_por_tema[formacao.tema_id] = Formacao.Situacao.REALIZADA
        elif formacao.situacao == Formacao.Situacao.PREVISTA:
            situacao_por_tema.setdefault(formacao.tema_id, Formacao.Situacao.PREVISTA)

    cobertura = {"nao_alocados": [], "agendados": [], "realizados": []}
    for tema in temas:
        situacao = situacao_por_tema.get(tema.pk)
        if situacao == Formacao.Situacao.REALIZADA:
            cobertura["realizados"].append(tema)
        elif situacao == Formacao.Situacao.PREVISTA:
            cobertura["agendados"].append(tema)
        else:
            cobertura["nao_alocados"].append(tema)
    return cobertura
