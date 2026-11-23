from datetime import date
from io import BytesIO
import re
from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from openpyxl import load_workbook

from acesso.models import Usuario
from cadastros.models import Ciclo, Formador, Perseverante, Tema
from cronograma import services as cronograma
from cronograma.models import Formacao
from presenca.models import Presenca
from relatorios import services
from relatorios.exportacao import gerar_pdf, gerar_planilha


class ConsolidacaoPuraTests(SimpleTestCase):
    def test_consolida_dados_de_cada_servico_sem_acessar_orm(self):
        ciclo = SimpleNamespace(pk=17, situacao=Ciclo.Situacao.ENCERRADO)
        realizada = SimpleNamespace(situacao=Formacao.Situacao.REALIZADA)
        cancelada = SimpleNamespace(situacao=Formacao.Situacao.CANCELADA)
        pessoa = SimpleNamespace(pk=23)
        contagem = {"presente": 2, "ausente": 1, "justificado": 0}
        cobertura = {
            "nao_alocados": ["não alocado"],
            "agendados": ["agendado"],
            "realizados": ["realizado"],
        }

        with (
            patch("relatorios.services.cadastros.buscar_ciclo", return_value=ciclo),
            patch(
                "relatorios.services.cronograma.listar_formacoes_do_ciclo",
                return_value=[realizada, cancelada],
            ),
            patch(
                "relatorios.services.cronograma.classificar_cobertura",
                return_value=cobertura,
            ),
            patch(
                "relatorios.services.cronograma.carga_por_formador",
                return_value=[("Ana", 1)],
            ),
            patch(
                "relatorios.services.cronograma.numero_de_trocas_do_ciclo",
                return_value=2,
            ),
            patch("relatorios.services.cadastros.listar_perseverantes", return_value=[pessoa]),
            patch("relatorios.services.presenca.frequencia_do_perseverante", return_value=contagem),
        ):
            relatorio = services.consolidar_relatorio("17")

        self.assertEqual(relatorio["realizadas"], [realizada])
        self.assertEqual(relatorio["canceladas"], [cancelada])
        self.assertEqual(relatorio["total_temas"], 3)
        self.assertEqual(relatorio["trocas"], 2)
        self.assertEqual(relatorio["frequencias"], [(pessoa, contagem)])
        self.assertEqual(
            relatorio["totais_frequencia"],
            {"presente": 2, "ausente": 1, "justificado": 0},
        )


class ExportacaoPuraTests(SimpleTestCase):
    def relatorio(self, quantidade=1):
        ciclo = SimpleNamespace(
            nome="Ciclo 2027",
            inicio=date(2027, 1, 1),
            fim=date(2027, 12, 31),
        )
        formador = SimpleNamespace(nome="Ana")
        formacao = SimpleNamespace(
            data=date(2027, 3, 1),
            titulo="Aula e oração",
            formador=formador,
        )
        frequencias = [
            (
                SimpleNamespace(nome=f"Perseverante {indice}"),
                {"presente": 1, "ausente": 0, "justificado": 0},
            )
            for indice in range(quantidade)
        ]
        return {
            "ciclo": ciclo,
            "realizadas": [formacao],
            "canceladas": [],
            "cobertura": {
                "realizados": [SimpleNamespace(nome="Tema realizado")],
                "agendados": [],
                "nao_alocados": [SimpleNamespace(nome="=1+1")],
            },
            "total_temas": 2,
            "carga": [(formador, 1)],
            "trocas": 2,
            "frequencias": frequencias,
            "totais_frequencia": {
                "presente": quantidade,
                "ausente": 0,
                "justificado": 0,
            },
        }

    def test_planilha_abre_com_os_blocos_e_textos_como_texto(self):
        planilha = load_workbook(
            BytesIO(gerar_planilha(self.relatorio())),
            data_only=True,
        ).active
        valores = {
            celula.value: celula
            for linha in planilha.iter_rows()
            for celula in linha
            if celula.value is not None
        }

        self.assertIn("Relatório de fechamento do ciclo", valores)
        self.assertIn("Formações canceladas", valores)
        self.assertIn("Cobertura final da apostila", valores)
        self.assertIn("Número de trocas de formador", valores)
        self.assertEqual(valores["=1+1"].data_type, "s")

    def test_pdf_valido_com_tabela_multipagina(self):
        dados = gerar_pdf(self.relatorio(quantidade=150))

        self.assertTrue(dados.startswith(b"%PDF-"))
        self.assertGreater(len(re.findall(rb"/Type\s*/Page\b", dados)), 1)


class RelatorioFechamentoTests(TestCase):
    def setUp(self):
        self.ciclo = Ciclo.objects.create(
            nome="Ciclo 2027",
            inicio=date(2027, 1, 1),
            fim=date(2027, 12, 31),
            situacao=Ciclo.Situacao.ENCERRADO,
        )
        self.ciclo_aberto = Ciclo.objects.create(
            nome="Ciclo 2028",
            inicio=date(2028, 1, 1),
            fim=date(2028, 12, 31),
            situacao=Ciclo.Situacao.ABERTO,
        )
        self.ana = self.criar_formador("Ana")
        self.bia = self.criar_formador("Bia")
        self.inativo = self.criar_formador("Caio", ativo=False)
        self.tema_a = Tema.objects.create(nome="Tema A", tipo=Tema.Tipo.APOSTILA)
        self.tema_b = Tema.objects.create(nome="Tema B", tipo=Tema.Tipo.APOSTILA)
        self.tema_c = Tema.objects.create(nome="Tema C", tipo=Tema.Tipo.APOSTILA)
        self.tema_d = Tema.objects.create(nome="Tema D", tipo=Tema.Tipo.APOSTILA)
        self.davi = Perseverante.objects.create(nome="Davi", ciclo=self.ciclo)
        self.eva = Perseverante.objects.create(nome="Eva", ciclo=self.ciclo)

        self.realizada_a = self.criar_formacao(
            date(2027, 3, 1), self.tema_a, self.ana, Formacao.Situacao.REALIZADA
        )
        self.cancelada = self.criar_formacao(
            date(2027, 3, 8), self.tema_b, self.bia, Formacao.Situacao.CANCELADA
        )
        self.prevista = self.criar_formacao(
            date(2027, 3, 15), self.tema_c, self.bia, Formacao.Situacao.PREVISTA
        )
        self.realizada_b = self.criar_formacao(
            date(2027, 3, 22), self.tema_b, self.ana, Formacao.Situacao.REALIZADA
        )
        self.sem_tema = self.criar_formacao(
            date(2027, 3, 29), None, None, Formacao.Situacao.REALIZADA, "Oração"
        )
        self.realizada_fora = self.criar_formacao(
            date(2028, 3, 1), self.tema_d, self.inativo, Formacao.Situacao.REALIZADA
        )

        cronograma.trocar_formador(self.realizada_a.pk, self.bia.pk)
        Presenca.objects.create(
            formacao=self.realizada_a,
            perseverante=self.davi,
            situacao=Presenca.Situacao.PRESENTE,
        )
        Presenca.objects.create(
            formacao=self.cancelada,
            perseverante=self.davi,
            situacao=Presenca.Situacao.PRESENTE,
        )
        Presenca.objects.create(
            formacao=self.realizada_b,
            perseverante=self.davi,
            situacao=Presenca.Situacao.PRESENTE,
        )
        Presenca.objects.create(
            formacao=self.prevista,
            perseverante=self.eva,
            situacao=Presenca.Situacao.AUSENTE,
        )
        Presenca.objects.create(
            formacao=self.realizada_b,
            perseverante=self.eva,
            situacao=Presenca.Situacao.JUSTIFICADO,
        )

    def criar_formador(self, nome, ativo=True):
        return Formador.objects.create(
            nome=nome,
            inicio_servico=date(2020, 1, 1),
            capacitado=True,
            ativo=ativo,
        )

    def criar_formacao(self, data, tema, formador, situacao, descricao=""):
        return Formacao.objects.create(
            data=data,
            tema=tema,
            formador=formador,
            situacao=situacao,
            descricao=descricao,
        )

    def entrar_como_coordenador(self):
        coordenador = Usuario.objects.create_user(
            username="coordenador",
            password="senha",
            perfil=Usuario.Perfil.COORDENADOR,
        )
        self.client.force_login(coordenador)

    def test_consolida_os_cinco_blocos_e_totais(self):
        relatorio = services.consolidar_relatorio(self.ciclo.pk)

        self.assertEqual(
            [formacao.titulo for formacao in relatorio["realizadas"]],
            ["Tema A", "Tema B", "Oração"],
        )
        self.assertEqual(relatorio["canceladas"], [self.cancelada])
        self.assertEqual(relatorio["total_temas"], 4)
        self.assertEqual(
            [tema.nome for tema in relatorio["cobertura"]["realizados"]],
            ["Tema A", "Tema B"],
        )
        self.assertEqual(
            [tema.nome for tema in relatorio["cobertura"]["agendados"]],
            ["Tema C"],
        )
        self.assertEqual(
            [tema.nome for tema in relatorio["cobertura"]["nao_alocados"]],
            ["Tema D"],
        )
        self.assertEqual(
            {formador.nome: total for formador, total in relatorio["carga"]},
            {"Ana": 1, "Bia": 1},
        )
        self.assertNotIn("Caio", [formador.nome for formador, _ in relatorio["carga"]])
        self.assertEqual(relatorio["trocas"], 1)
        self.assertEqual(
            {
                perseverante.nome: frequencia
                for perseverante, frequencia in relatorio["frequencias"]
            },
            {
                "Davi": {"presente": 2, "ausente": 0, "justificado": 0},
                "Eva": {"presente": 0, "ausente": 1, "justificado": 1},
            },
        )
        self.assertEqual(
            relatorio["totais_frequencia"],
            {"presente": 2, "ausente": 1, "justificado": 1},
        )
        self.assertNotIn(self.realizada_fora, relatorio["realizadas"])

    def test_nao_lista_ciclos_abertos(self):
        self.assertEqual(services.listar_ciclos_encerrados(), [self.ciclo])

    def test_recusa_ciclo_aberto_e_id_inexistente(self):
        for ciclo_id in (self.ciclo_aberto.pk, 999999, None):
            with self.subTest(ciclo_id=ciclo_id):
                with self.assertRaises(ValidationError):
                    services.consolidar_relatorio(ciclo_id)

    def test_tela_mostra_os_blocos_consolidados(self):
        self.entrar_como_coordenador()
        resposta = self.client.get(
            reverse("relatorios:fechamento"),
            {"ciclo": self.ciclo.pk},
        )

        self.assertEqual(resposta.status_code, 200)
        for texto in (
            "Formações realizadas",
            "Formações canceladas",
            "Cobertura final da apostila",
            "Carga por formador",
            "Número de trocas de formador",
            "Frequência da turma",
            "Oração",
            "Tema D",
        ):
            with self.subTest(texto=texto):
                self.assertContains(resposta, texto)
        self.assertContains(resposta, "Exportar Excel")
        self.assertContains(resposta, "Exportar PDF")

    def test_selecao_de_ciclo_aberto_na_tela_nao_gera_relatorio(self):
        self.entrar_como_coordenador()
        resposta = self.client.get(
            reverse("relatorios:fechamento"),
            {"ciclo": self.ciclo_aberto.pk},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIsNone(resposta.context["relatorio"])
        self.assertTrue(resposta.context["form"].has_error("ciclo"))

    def test_coordenador_e_perfil_exigido_para_tela_e_exportacoes(self):
        urls = (
            reverse("relatorios:fechamento"),
            reverse("relatorios:excel"),
            reverse("relatorios:pdf"),
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)

        formador = Usuario.objects.create_user(
            username="formador",
            password="senha",
            perfil=Usuario.Perfil.FORMADOR,
        )
        self.client.force_login(formador)
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    self.client.get(url, {"ciclo": self.ciclo.pk}).status_code,
                    403,
                )

    def test_exporta_excel_com_os_dados_consolidados(self):
        self.entrar_como_coordenador()
        resposta = self.client.get(
            reverse("relatorios:excel"),
            {"ciclo": self.ciclo.pk},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn("relatorio-fechamento-ciclo-2027.xlsx", resposta["Content-Disposition"])
        planilha = load_workbook(BytesIO(resposta.content), data_only=True).active
        valores = {
            celula.value
            for linha in planilha.iter_rows()
            for celula in linha
            if celula.value is not None
        }
        for texto in ("Relatório de fechamento do ciclo", "Ciclo: Ciclo 2027", "Tema A", "Oração", "Davi"):
            self.assertIn(texto, valores)
        self.assertIn(1, valores)

    def test_exporta_pdf_identificado_e_valido(self):
        self.entrar_como_coordenador()
        resposta = self.client.get(
            reverse("relatorios:pdf"),
            {"ciclo": self.ciclo.pk},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta["Content-Type"], "application/pdf")
        self.assertIn("relatorio-fechamento-ciclo-2027.pdf", resposta["Content-Disposition"])
        self.assertTrue(resposta.content.startswith(b"%PDF-"))

    def test_exportacao_sem_ciclo_e_rejeitada(self):
        self.entrar_como_coordenador()
        for url in (reverse("relatorios:excel"), reverse("relatorios:pdf")):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 400)


class RelatorioSemDadosTests(TestCase):
    def test_ciclo_sem_dados_tem_contagens_vazias_e_cobertura_zero(self):
        ciclo = Ciclo.objects.create(
            nome="Ciclo vazio",
            inicio=date(2030, 1, 1),
            fim=date(2030, 12, 31),
            situacao=Ciclo.Situacao.ENCERRADO,
        )

        relatorio = services.consolidar_relatorio(ciclo.pk)

        self.assertEqual(relatorio["realizadas"], [])
        self.assertEqual(relatorio["canceladas"], [])
        self.assertEqual(relatorio["total_temas"], 0)
        self.assertEqual(relatorio["carga"], [])
        self.assertEqual(relatorio["trocas"], 0)
        self.assertEqual(relatorio["frequencias"], [])
        self.assertEqual(
            relatorio["totais_frequencia"],
            {"presente": 0, "ausente": 0, "justificado": 0},
        )

    def test_tela_mostra_mensagens_para_ciclo_sem_dados(self):
        ciclo = Ciclo.objects.create(
            nome="Ciclo vazio",
            inicio=date(2030, 1, 1),
            fim=date(2030, 12, 31),
            situacao=Ciclo.Situacao.ENCERRADO,
        )
        coordenador = Usuario.objects.create_user(
            username="coordenador",
            password="senha",
            perfil=Usuario.Perfil.COORDENADOR,
        )
        self.client.force_login(coordenador)

        resposta = self.client.get(
            reverse("relatorios:fechamento"),
            {"ciclo": ciclo.pk},
        )

        self.assertContains(resposta, "Nenhuma formação realizada neste ciclo.")
        self.assertContains(resposta, "Nenhuma formação cancelada neste ciclo.")
        self.assertContains(resposta, "Nenhum formador ativo cadastrado.")
        self.assertContains(resposta, "Nenhum perseverante cadastrado neste ciclo.")
