from io import BytesIO

from django.utils.text import slugify
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill


def nome_arquivo_relatorio(ciclo, extensao):
    nome = slugify(ciclo.nome) or "ciclo"
    return f"relatorio-fechamento-{nome}.{extensao}"


def gerar_planilha(relatorio):
    arquivo = BytesIO()
    pasta = Workbook()
    planilha = pasta.active
    planilha.title = "Fechamento"
    planilha.sheet_view.showGridLines = False

    planilha.merge_cells("A1:D1")
    planilha["A1"] = "Relatório de fechamento do ciclo"
    planilha["A1"].font = Font(bold=True, color="FFFFFF", size=16)
    planilha["A1"].fill = PatternFill("solid", fgColor="1F4E78")
    planilha["A1"].alignment = Alignment(vertical="center")
    planilha.row_dimensions[1].height = 26
    planilha.merge_cells("A2:D2")
    planilha["A2"] = f"Ciclo: {relatorio['ciclo'].nome}"
    planilha.merge_cells("A3:D3")
    ciclo = relatorio["ciclo"]
    planilha["A3"] = f"Período: {ciclo.inicio:%d/%m/%Y} a {ciclo.fim:%d/%m/%Y}"

    linha = 5
    linha = _adicionar_secao(
        planilha,
        linha,
        "Formações realizadas",
        ("Data", "Formação", "Formador"),
        [
            (formacao.data, formacao.titulo, formacao.formador.nome if formacao.formador else "A definir")
            for formacao in relatorio["realizadas"]
        ],
        "Nenhuma formação realizada neste ciclo.",
    )
    linha = _adicionar_secao(
        planilha,
        linha,
        "Formações canceladas",
        ("Data", "Formação", "Formador"),
        [
            (formacao.data, formacao.titulo, formacao.formador.nome if formacao.formador else "A definir")
            for formacao in relatorio["canceladas"]
        ],
        "Nenhuma formação cancelada neste ciclo.",
    )

    cobertura = relatorio["cobertura"]
    linha = _adicionar_secao(
        planilha,
        linha,
        "Cobertura final da apostila",
        ("Classificação", "Quantidade", "Temas"),
        [
            (
                titulo,
                len(cobertura[chave]),
                ", ".join(tema.nome for tema in cobertura[chave]) or "Nenhum",
            )
            for chave, titulo in (
                ("realizados", "Realizados"),
                ("agendados", "Agendados"),
                ("nao_alocados", "Não alocados"),
            )
        ],
    )
    linha = _adicionar_secao(
        planilha,
        linha,
        "Carga por formador",
        ("Formador", "Formações realizadas"),
        [(formador.nome, total) for formador, total in relatorio["carga"]],
        "Nenhum formador ativo cadastrado.",
    )
    linha = _adicionar_secao(
        planilha,
        linha,
        "Número de trocas de formador",
        ("Trocas",),
        [(relatorio["trocas"],)],
    )

    linhas_frequencia = [
        (
            perseverante.nome,
            contagem["presente"],
            contagem["ausente"],
            contagem["justificado"],
        )
        for perseverante, contagem in relatorio["frequencias"]
    ]
    if linhas_frequencia:
        totais = relatorio["totais_frequencia"]
        linhas_frequencia.append(
            ("Total", totais["presente"], totais["ausente"], totais["justificado"])
        )
        vazio = None
    else:
        vazio = "Nenhum perseverante cadastrado neste ciclo."
    _adicionar_secao(
        planilha,
        linha,
        "Frequência da turma",
        ("Perseverante", "Presente", "Ausente", "Justificado"),
        linhas_frequencia,
        vazio,
    )

    for coluna, largura in {"A": 28, "B": 32, "C": 34, "D": 18}.items():
        planilha.column_dimensions[coluna].width = largura
    planilha.freeze_panes = "A5"
    planilha.page_setup.orientation = "landscape"
    planilha.page_setup.fitToWidth = 1
    planilha.page_setup.fitToHeight = 0
    planilha.sheet_properties.pageSetUpPr.fitToPage = True
    pasta.save(arquivo)
    return arquivo.getvalue()


def _adicionar_secao(planilha, linha, titulo, cabecalhos, dados, sem_dados=None):
    fim = len(cabecalhos)
    planilha.merge_cells(start_row=linha, start_column=1, end_row=linha, end_column=fim)
    celula = planilha.cell(row=linha, column=1, value=titulo)
    celula.font = Font(bold=True, color="FFFFFF")
    celula.fill = PatternFill("solid", fgColor="4472C4")
    linha += 1

    for coluna, cabecalho in enumerate(cabecalhos, start=1):
        celula = planilha.cell(row=linha, column=coluna, value=cabecalho)
        celula.font = Font(bold=True)
        celula.fill = PatternFill("solid", fgColor="D9EAF7")
    linha += 1

    linhas = dados or ([(sem_dados,) + ("",) * (fim - 1)] if sem_dados else [])
    for valores in linhas:
        for coluna, valor in enumerate(valores, start=1):
            celula = planilha.cell(row=linha, column=coluna, value=valor)
            celula.alignment = Alignment(vertical="top", wrap_text=True)
            if hasattr(valor, "strftime"):
                celula.number_format = "dd/mm/yyyy"
        linha += 1
    return linha + 1
