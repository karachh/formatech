from datetime import date

from django.test import TestCase
from django.urls import reverse

from acesso.models import Usuario
from cadastros.models import Ciclo, Formador, Tema
from cronograma import services
from cronograma.exportacao import ExportadorTexto
from cronograma.models import Formacao

URL = reverse("cronograma:exportar")


class ExportacaoTests(TestCase):
    def setUp(self):
        Ciclo.objects.create(nome="2027", inicio=date(2027, 1, 1), fim=date(2027, 12, 31))
        self.tema = Tema.objects.create(nome="Kerigma", tipo="apostila", rotulo="1")
        self.formador = Formador.objects.create(nome="Ana", inicio_servico=date(2020, 1, 1), capacitado=True)

    def formacao(self, dia, situacao="prevista", mes=3, tema="padrao", formador="padrao"):
        return Formacao.objects.create(
            data=date(2027, mes, dia),
            tema=self.tema if tema == "padrao" else tema,
            formador=self.formador if formador == "padrao" else formador,
            situacao=situacao,
        )

    def test_uma_linha_por_formacao_com_data_tema_e_formador(self):
        self.formacao(10)
        texto = services.exportar_cronograma_do_mes(2027, 3)
        self.assertIn("10/03 - Kerigma - Ana", texto)

    def test_cabecalho_com_o_mes(self):
        self.assertIn("Cronograma de março de 2027", services.exportar_cronograma_do_mes(2027, 3))

    def test_canceladas_ficam_fora(self):
        self.formacao(10)
        self.formacao(17, situacao="cancelada")
        texto = services.exportar_cronograma_do_mes(2027, 3)
        self.assertIn("10/03", texto)
        self.assertNotIn("17/03", texto)

    def test_formacoes_de_outro_mes_ficam_fora(self):
        self.formacao(10, mes=4)
        self.assertNotIn("10/04", services.exportar_cronograma_do_mes(2027, 3))

    def test_ordem_cronologica(self):
        self.formacao(24)
        self.formacao(10)
        texto = services.exportar_cronograma_do_mes(2027, 3)
        self.assertLess(texto.index("10/03"), texto.index("24/03"))

    def test_sem_tema_e_sem_formador(self):
        self.formacao(10, tema=None, formador=None)
        self.assertIn("10/03 - Sem tema - a definir", services.exportar_cronograma_do_mes(2027, 3))

    def test_mes_sem_formacoes(self):
        self.assertIn("Nenhuma formação neste mês.", services.exportar_cronograma_do_mes(2027, 5))

    def test_mes_invalido_usa_o_mes_de_hoje(self):
        self.assertEqual(len(services.mes_da_exportacao("lixo")), 2)
        self.assertEqual(services.mes_da_exportacao("2027-03"), (2027, 3))

    def test_exportador_e_template_method(self):
        self.formacao(10)
        texto = ExportadorTexto().exportar("março de 2027", Formacao.objects.all())
        self.assertTrue(texto.startswith("Cronograma de março de 2027"))


class TelaExportacaoTests(TestCase):
    def test_anonimo_vai_para_o_login(self):
        self.assertEqual(self.client.get(URL).status_code, 302)

    def test_formador_recebe_403(self):
        formador = Usuario.objects.create_user(username="f", password="x", perfil=Usuario.Perfil.FORMADOR)
        self.client.force_login(formador)
        self.assertEqual(self.client.get(URL).status_code, 403)

    def test_coordenador_ve_o_texto_e_o_botao_copiar(self):
        coord = Usuario.objects.create_user(username="c", password="x", perfil=Usuario.Perfil.COORDENADOR)
        self.client.force_login(coord)
        resposta = self.client.get(URL, {"mes": "2027-03"})
        self.assertContains(resposta, "Cronograma de março de 2027")
        self.assertContains(resposta, "Copiar")