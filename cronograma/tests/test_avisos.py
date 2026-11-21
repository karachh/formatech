"""US008: avisos ao escalar um formador (RN001: aviso, nunca bloqueio)."""

from datetime import date

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from cadastros.models import Formador, Tema
from cadastros.tests.test_tela_ciclos import ComoCoordenador
from cronograma import avisos, services
from cronograma.models import Formacao
from cronograma.tests.test_formacao import ComDados


class RegraFormadorJaMinistrouTemaTests(SimpleTestCase):
    """Teste unitário da regra: objetos em memória, sem banco."""

    def setUp(self):
        self.tema = Tema(pk=1, nome="Kerigma")
        self.outro_tema = Tema(pk=2, nome="Sacramentos")
        self.formador = Formador(nome="Ana")
        self.regra = avisos.FormadorJaMinistrouTema()

    def test_avisa_com_a_data_da_ultima_vez(self):
        historico = [
            Formacao(data=date(2026, 9, 5), tema=self.tema),
            Formacao(data=date(2025, 3, 1), tema=self.tema),
        ]
        aviso = self.regra.verificar(Formacao(tema=self.tema), self.formador, historico)

        self.assertEqual(aviso.codigo, "formador_ja_ministrou_tema")
        self.assertEqual(aviso.mensagem, "Ana já ministrou “Kerigma” em 05/09/2026.")

    def test_nao_avisa_quando_o_tema_e_outro(self):
        historico = [Formacao(data=date(2026, 9, 5), tema=self.outro_tema)]
        self.assertIsNone(self.regra.verificar(Formacao(tema=self.tema), self.formador, historico))

    def test_nao_avisa_sem_historico(self):
        self.assertIsNone(self.regra.verificar(Formacao(tema=self.tema), self.formador, []))

    def test_nao_avisa_em_encontro_sem_tema(self):
        historico = [Formacao(data=date(2026, 9, 5), tema=None)]
        self.assertIsNone(self.regra.verificar(Formacao(), self.formador, historico))


class ListaDeAvisosTests(SimpleTestCase):
    """RN001: o conjunto de avisos possíveis pode ser listado exaustivamente."""

    def test_lista_todos_os_codigos(self):
        self.assertEqual(avisos.codigos_de_aviso(), ["formador_ja_ministrou_tema"])

    def test_toda_regra_segue_a_interface_e_tem_codigo_proprio(self):
        codigos = avisos.codigos_de_aviso()
        self.assertEqual(len(codigos), len(set(codigos)))
        for regra in avisos.REGRAS:
            self.assertIsInstance(regra, avisos.RegraDeAviso)
            self.assertTrue(regra.codigo)

    def test_interface_sozinha_nao_verifica_nada(self):
        with self.assertRaises(NotImplementedError):
            avisos.RegraDeAviso().verificar(Formacao(), Formador(), [])


class ServicoAvisosTests(ComDados, TestCase):
    def ja_ministrou(self, dia=date(2026, 9, 5), situacao=Formacao.Situacao.REALIZADA):
        self.formacao(dia, tema=self.tema, formador=self.formador, situacao=situacao)

    def test_escala_mesmo_com_aviso(self):
        self.ja_ministrou()
        nova = self.formacao(date(2027, 3, 6), tema=self.tema)

        formacao, lista = services.escalar_formador(nova.pk, self.formador.pk)

        nova.refresh_from_db()
        self.assertEqual(nova.formador, self.formador)
        self.assertEqual(formacao.formador, self.formador)
        self.assertEqual([aviso.codigo for aviso in lista], ["formador_ja_ministrou_tema"])
        self.assertIn("05/09/2026", lista[0].mensagem)

    def test_sem_aviso_quando_nunca_ministrou(self):
        nova = self.formacao(date(2027, 3, 6), tema=self.tema)

        _, lista = services.escalar_formador(nova.pk, self.formador.pk)

        self.assertEqual(lista, [])

    def test_formacao_cancelada_nao_conta_como_ministrada(self):
        self.ja_ministrou(situacao=Formacao.Situacao.CANCELADA)
        nova = self.formacao(date(2027, 3, 6), tema=self.tema)

        _, lista = services.escalar_formador(nova.pk, self.formador.pk)

        self.assertEqual(lista, [])

    def test_consulta_antes_de_escalar_traz_o_aviso(self):
        self.ja_ministrou()
        nova = self.formacao(date(2027, 3, 6), tema=self.tema)

        dados = services.dados_para_escalacao(nova.pk, self.formador.pk)

        self.assertEqual([aviso.codigo for aviso in dados["avisos"]], ["formador_ja_ministrou_tema"])


class TelaAvisosTests(ComoCoordenador, ComDados, TestCase):
    def setUp(self):
        super().setUp()
        self.formacao(date(2026, 9, 5), tema=self.tema, formador=self.formador, situacao=Formacao.Situacao.REALIZADA)
        self.nova = self.formacao(date(2027, 3, 6), tema=self.tema)
        self.url = reverse("cronograma:escalar_formador", args=[self.nova.pk])

    def test_consulta_mostra_o_aviso_e_o_botao_de_confirmar(self):
        resposta = self.client.get(self.url, {"formador_id": self.formador.pk})

        self.assertContains(resposta, "Aviso: Ana já ministrou “Sagrada Tradição” em 05/09/2026.")
        self.assertContains(resposta, '<button type="submit">Escalar formador</button>', html=True)

    def test_confirmar_grava_e_mostra_o_aviso(self):
        resposta = self.client.post(self.url, {"formador_id": self.formador.pk}, follow=True)

        self.assertContains(resposta, "Formador “Ana” escalado.")
        self.assertContains(resposta, "Aviso: Ana já ministrou “Sagrada Tradição” em 05/09/2026.")
        self.nova.refresh_from_db()
        self.assertEqual(self.nova.formador, self.formador)

    def test_sem_historico_nao_mostra_aviso(self):
        outro = Formador.objects.create(nome="Carla", inicio_servico=date(2021, 3, 1), capacitado=True)

        resposta = self.client.get(self.url, {"formador_id": outro.pk})

        self.assertNotContains(resposta, "Aviso:")
