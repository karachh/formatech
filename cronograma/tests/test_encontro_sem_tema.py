"""US017: encontro sem tema da apostila (oração, dinâmica) ou com tema opcional."""

from datetime import date

from django.test import TestCase
from django.urls import reverse

from cadastros.models import Ciclo, Tema
from cadastros.tests.test_tela_ciclos import ComoCoordenador
from cronograma import services
from cronograma.models import Formacao

URL = reverse("cronograma:cronograma")


class ComCiclo:
    def setUp(self):
        super().setUp()
        self.ciclo = Ciclo.objects.create(nome="2027", inicio=date(2027, 2, 1), fim=date(2027, 12, 15))
        self.apostila = Tema.objects.create(nome="Kerigma", tipo=Tema.Tipo.APOSTILA, rotulo="1")
        self.opcional = Tema.objects.create(nome="Retiro de Carnaval", tipo=Tema.Tipo.OPCIONAL)


class TituloDoEncontroTests(TestCase):
    """O título é calculado (RN006): tema, senão descrição, senão "Sem tema"."""

    def test_com_tema_mostra_o_tema(self):
        tema = Tema(nome="Kerigma")
        self.assertEqual(Formacao(tema=tema, descricao="Abertura").titulo, "Kerigma")

    def test_sem_tema_mostra_a_descricao(self):
        self.assertEqual(Formacao(descricao="Oração").titulo, "Oração")

    def test_sem_tema_e_sem_descricao(self):
        self.assertEqual(Formacao().titulo, "Sem tema")


class AgendarEncontroSemTemaTests(ComoCoordenador, ComCiclo, TestCase):
    """T017.1: o formulário aceita tema em branco ou opcional."""

    def agendar(self, tema_id="", descricao=""):
        dados = {"data": "2027-03-06", "tema_id": tema_id, "formador_id": "", "descricao": descricao}
        return self.client.post(URL, dados, follow=True)

    def test_sem_tema_aparece_no_cronograma_pela_descricao(self):
        resposta = self.agendar(descricao="Oração")

        formacao = Formacao.objects.get()
        self.assertIsNone(formacao.tema)
        self.assertEqual(formacao.situacao, Formacao.Situacao.PREVISTA)
        self.assertContains(resposta, "Formação de 06/03/2027 agendada.")
        self.assertContains(resposta, "<td>Oração</td>", html=True)

    def test_sem_tema_e_sem_descricao_aparece_como_sem_tema(self):
        resposta = self.agendar()

        self.assertEqual(Formacao.objects.count(), 1)
        self.assertContains(resposta, "<td>Sem tema</td>", html=True)

    def test_com_tema_opcional_aparece_no_cronograma(self):
        resposta = self.agendar(tema_id=self.opcional.pk)

        self.assertEqual(Formacao.objects.get().tema, self.opcional)
        self.assertContains(resposta, "<td>Retiro de Carnaval</td>", html=True)

    def test_cronograma_oferece_presenca_no_encontro_sem_tema(self):
        self.agendar(descricao="Dinâmica")
        formacao = Formacao.objects.get()

        resposta = self.client.get(URL, {"ciclo": self.ciclo.pk})

        self.assertContains(resposta, reverse("presenca:lancar_presenca", args=[formacao.pk]))

    def test_exportacao_mostra_a_descricao(self):
        Formacao.objects.create(data=date(2027, 3, 10), descricao="Oração")

        self.assertIn("10/03 - Oração - a definir", services.exportar_cronograma_do_mes(2027, 3))


class CoberturaSemEncontrosLivresTests(ComoCoordenador, ComCiclo, TestCase):
    """T017.2: encontro sem tema ou com tema opcional fica fora da cobertura da apostila."""

    def temas_na_cobertura(self):
        cobertura = services.classificar_cobertura(self.ciclo)
        return [tema.nome for lista in cobertura.values() for tema in lista]

    def test_encontro_sem_tema_nao_entra_na_cobertura(self):
        Formacao.objects.create(data=date(2027, 3, 6), descricao="Oração", situacao="realizada")

        cobertura = services.classificar_cobertura(self.ciclo)

        self.assertEqual([t.nome for t in cobertura["nao_alocados"]], ["Kerigma"])
        self.assertEqual((cobertura["agendados"], cobertura["realizados"]), ([], []))

    def test_encontro_com_tema_opcional_nao_entra_na_cobertura(self):
        Formacao.objects.create(data=date(2027, 3, 6), tema=self.opcional, situacao="realizada")

        self.assertNotIn("Retiro de Carnaval", self.temas_na_cobertura())

    def test_tela_de_cobertura_nao_mostra_o_encontro(self):
        Formacao.objects.create(data=date(2027, 3, 6), descricao="Oração", situacao="realizada")

        resposta = self.client.get(reverse("cronograma:cobertura"), {"ciclo": self.ciclo.pk})

        self.assertContains(resposta, "Kerigma")
        self.assertNotContains(resposta, "Oração")

