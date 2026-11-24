from django.core.exceptions import ValidationError

from cadastros import services as cadastros
from cadastros.models import Ciclo
from cronograma import services as cronograma
from cronograma.models import Formacao
from presenca import services as presenca


def listar_ciclos_encerrados():
    return [
        ciclo
        for ciclo in cadastros.listar_ciclos()
        if ciclo.situacao == Ciclo.Situacao.ENCERRADO
    ]


def consolidar_relatorio(ciclo_id):
    try:
        ciclo = cadastros.buscar_ciclo(ciclo_id)
    except (Ciclo.DoesNotExist, TypeError, ValueError):
        raise ValidationError({"ciclo": "Selecione um ciclo válido."})

    if ciclo.situacao != Ciclo.Situacao.ENCERRADO:
        raise ValidationError({"ciclo": "O relatório só pode ser gerado para um ciclo encerrado."})

    formacoes = cronograma.listar_formacoes_do_ciclo(ciclo)
    cobertura = cronograma.classificar_cobertura(ciclo)
    formadores = cronograma.carga_por_formador(ciclo)

    frequencias = []
    totais_frequencia = {"presente": 0, "ausente": 0, "justificado": 0}
    for perseverante in cadastros.listar_perseverantes(ciclo.pk):
        contagem = presenca.frequencia_do_perseverante(perseverante)
        frequencias.append((perseverante, contagem))
        for situacao, total in contagem.items():
            totais_frequencia[situacao] += total

    return {
        "ciclo": ciclo,
        "realizadas": [
            formacao
            for formacao in formacoes
            if formacao.situacao == Formacao.Situacao.REALIZADA
        ],
        "canceladas": [
            formacao
            for formacao in formacoes
            if formacao.situacao == Formacao.Situacao.CANCELADA
        ],
        "cobertura": cobertura,
        "total_temas": sum(len(temas) for temas in cobertura.values()),
        "carga": formadores,
        "trocas": cronograma.numero_de_trocas_do_ciclo(ciclo),
        "frequencias": frequencias,
        "totais_frequencia": totais_frequencia,
    }
