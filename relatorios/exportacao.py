from functools import partial
from io import BytesIO
from xml.sax.saxutils import escape

from django.utils.text import slugify
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle


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


def gerar_pdf(relatorio):
    arquivo = BytesIO()
    ciclo = relatorio["ciclo"]
    documento = SimpleDocTemplate(
        arquivo,
        pagesize=landscape(A4),
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Relatório de fechamento - {ciclo.nome}",
    )
    estilos = getSampleStyleSheet()
    estilos.add(
        ParagraphStyle(
            name="TituloRelatorio",
            parent=estilos["Title"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1F4E78"),
        )
    )
    estilos.add(
        ParagraphStyle(
            name="CelulaRelatorio",
            parent=estilos["BodyText"],
            fontSize=8,
            leading=10,
            wordWrap="CJK",
        )
    )
    estilos.add(
        ParagraphStyle(
            name="SecaoRelatorio",
            parent=estilos["Heading2"],
            keepWithNext=True,
            textColor=colors.HexColor("#1F4E78"),
        )
    )

    conteudo = [
        Paragraph("Relatório de fechamento do ciclo", estilos["TituloRelatorio"]),
        Spacer(1, 4 * mm),
        Paragraph(f"<b>Ciclo:</b> {escape(ciclo.nome)}", estilos["BodyText"]),
        Paragraph(
            f"<b>Período:</b> {ciclo.inicio:%d/%m/%Y} a {ciclo.fim:%d/%m/%Y}",
            estilos["BodyText"],
        ),
        Spacer(1, 5 * mm),
    ]
    largura = documento.width
    _adicionar_tabela_pdf(
        conteudo,
        estilos,
        "Formações realizadas",
        ("Data", "Formação", "Formador"),
        [
            (
                f"{formacao.data:%d/%m/%Y}",
                formacao.titulo,
                formacao.formador.nome if formacao.formador else "A definir",
            )
            for formacao in relatorio["realizadas"]
        ],
        (largura * 0.15, largura * 0.55, largura * 0.30),
        "Nenhuma formação realizada neste ciclo.",
    )
    _adicionar_tabela_pdf(
        conteudo,
        estilos,
        "Formações canceladas",
        ("Data", "Formação", "Formador"),
        [
            (
                f"{formacao.data:%d/%m/%Y}",
                formacao.titulo,
                formacao.formador.nome if formacao.formador else "A definir",
            )
            for formacao in relatorio["canceladas"]
        ],
        (largura * 0.15, largura * 0.55, largura * 0.30),
        "Nenhuma formação cancelada neste ciclo.",
    )

    cobertura = relatorio["cobertura"]
    temas_cobertura = []
    for chave, titulo in (
        ("realizados", "Realizado"),
        ("agendados", "Agendado"),
        ("nao_alocados", "Não alocado"),
    ):
        temas = cobertura[chave]
        if temas:
            temas_cobertura.extend((titulo, tema.nome) for tema in temas)
        else:
            temas_cobertura.append((titulo, "Nenhum tema"))
    _adicionar_tabela_pdf(
        conteudo,
        estilos,
        "Cobertura final da apostila",
        ("Classificação", "Tema"),
        temas_cobertura,
        (largura * 0.25, largura * 0.75),
    )
    _adicionar_tabela_pdf(
        conteudo,
        estilos,
        "Carga por formador",
        ("Formador", "Formações realizadas"),
        [(formador.nome, total) for formador, total in relatorio["carga"]],
        (largura * 0.70, largura * 0.30),
        "Nenhum formador ativo cadastrado.",
    )
    conteudo.extend(
        [
            Paragraph("Número de trocas de formador", estilos["SecaoRelatorio"]),
            Paragraph(str(relatorio["trocas"]), estilos["BodyText"]),
            Spacer(1, 4 * mm),
        ]
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
        mensagem = None
    else:
        mensagem = "Nenhum perseverante cadastrado neste ciclo."
    _adicionar_tabela_pdf(
        conteudo,
        estilos,
        "Frequência da turma",
        ("Perseverante", "Presente", "Ausente", "Justificado"),
        linhas_frequencia,
        (largura * 0.52, largura * 0.16, largura * 0.16, largura * 0.16),
        mensagem,
    )

    rodape = partial(_rodape_pdf, ciclo=ciclo.nome)
    documento.build(conteudo, onFirstPage=rodape, onLaterPages=rodape)
    return arquivo.getvalue()


def _adicionar_tabela_pdf(conteudo, estilos, titulo, cabecalhos, linhas, larguras, sem_dados=None):
    conteudo.append(Paragraph(escape(titulo), estilos["SecaoRelatorio"]))
    dados = [
        [Paragraph(f"<b>{escape(str(valor))}</b>", estilos["CelulaRelatorio"]) for valor in cabecalhos]
    ]
    for linha in linhas:
        dados.append(
            [
                Paragraph(escape(str(valor)), estilos["CelulaRelatorio"])
                for valor in linha
            ]
        )
    tabela = LongTable(
        dados,
        colWidths=larguras,
        repeatRows=1,
        splitByRow=1,
        hAlign="LEFT",
    )
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1F1F1F")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#A6A6A6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    conteudo.append(tabela)
    conteudo.append(Spacer(1, 4 * mm))
    if sem_dados and not linhas:
        conteudo.append(Paragraph(escape(sem_dados), estilos["BodyText"]))
        conteudo.append(Spacer(1, 3 * mm))


def _rodape_pdf(canvas, doc, ciclo):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(doc.leftMargin, 9 * mm, f"FORMATECH · Fechamento: {ciclo}")
    canvas.drawRightString(
        doc.pagesize[0] - doc.rightMargin,
        9 * mm,
        f"Página {doc.page}",
    )
    canvas.restoreState()
