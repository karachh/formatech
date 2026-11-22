from django.core.exceptions import ValidationError

from cadastros import services as cadastros
from cronograma import services as cronograma

from . import repositories
from .models import Presenca


def buscar_formacao(formacao_id):
    """Formação inexistente propaga Formacao.DoesNotExist."""
    return cronograma.buscar_formacao(formacao_id)


def grade_de_presenca(formacao):
    """[(perseverante, situacao)] com os perseverantes ativos do ciclo da formação.

    Quem já tem presença lançada vem com a situação salva (T014.4);
    quem ainda não tem vem como presente (T014.2).
    """
    ciclo = cronograma.ciclo_da_formacao(formacao)
    if ciclo is None:
        raise ValidationError(cronograma.MENSAGEM_SEM_CICLO)
    salvas = repositories.situacoes_da_formacao(formacao.pk)
    return [
        (perseverante, salvas.get(perseverante.pk, Presenca.Situacao.PRESENTE))
        for perseverante in cadastros.listar_perseverantes_ativos(ciclo.pk)
    ]


def lancar_presencas(formacao_id, situacoes):
    """Grava a presença da turma inteira de uma vez (RF014, NFR001).

    situacoes: {perseverante_id: situacao}. Só aceita perseverantes da grade.
    """
    formacao = buscar_formacao(formacao_id)
    da_grade = {perseverante.pk for perseverante, _ in grade_de_presenca(formacao)}
    if not set(situacoes) <= da_grade:
        raise ValidationError("A lista tem perseverante que não é do ciclo desta formação.")
    if not set(situacoes.values()) <= set(Presenca.Situacao.values):
        raise ValidationError("Selecione uma situação válida para cada perseverante.")
    repositories.salvar_presencas(formacao.pk, situacoes)
    return formacao

def listar_ciclos():
    return cadastros.listar_ciclos()


def listar_perseverantes_do_ciclo(ciclo_id):
    return cadastros.listar_perseverantes(ciclo_id)


def frequencia_do_perseverante(perseverante):
    return repositories.contar_presencas_por_situacao(perseverante.pk, perseverante.ciclo)

