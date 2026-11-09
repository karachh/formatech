from datetime import date

from django.test import TestCase
from django.urls import reverse

from acesso.models import Usuario
from cadastros.models import Ciclo, Tema
from cronograma import services
from cronograma.models import Formacao

URL = reverse("cronograma:cobertura")


class CoberturaServicoTests(TestCase):
    def setUp(self):
        self.ciclo = Ciclo.objects.create(nome="2027", inicio=date(2027, 2, 1), fim=date(2027, 12, 15))
        self.a = Tema.objects.create(nome="A", tipo="apostila", rotulo="1")
        self.b = Tema.objects.create(nome="B", tipo="apostila", rotulo="1")
        self.c = Tema.objects.create(nome="C", tipo="apostila", rotulo="2")
        self.opcional = Tema.objects.create(nome="Convidado", tipo="opcional")

    def formacao(self, tema, situacao, dia=10):
        return Formacao.objects.create(data=date(2027, 3, dia), tema=tema, situacao=situacao)

    def nomes(self, lista):
        return [t.nome for t in lista]

    def test_sem_formacoes_tudo_nao_alocado(self):
        c = services.classificar_cobertura(self.ciclo)
        self.assertEqual(self.nomes(c["nao_alocados"]), ["A", "B", "C"])
        self.assertEqual((c["agendados"], c["realizados"]), ([], []))

    def test_classifica_agendado_e_realizado(self):
        self.formacao(self.a, "prevista")
        self.formacao(self.b, "realizada", 11)
        c = services.classificar_cobertura(self.ciclo)
        self.assertEqual(self.nomes(c["agendados"]), ["A"])
        self.assertEqual(self.nomes(c["realizados"]), ["B"])
        self.assertEqual(self.nomes(c["nao_alocados"]), ["C"])

    def test_cancelada_volta_a_nao_alocado(self):
        self.formacao(self.a, "cancelada")
        c = services.classificar_cobertura(self.ciclo)
        self.assertIn("A", self.nomes(c["nao_alocados"]))

    def test_realizada_vence_prevista_no_mesmo_tema(self):
        self.formacao(self.a, "prevista")
        self.formacao(self.a, "realizada", 11)
        c = services.classificar_cobertura(self.ciclo)
        self.assertEqual(self.nomes(c["realizados"]), ["A"])
        self.assertEqual(c["agendados"], [])

    def test_opcionais_ficam_fora(self):
        self.formacao(self.opcional, "realizada")
        c = services.classificar_cobertura(self.ciclo)
        todos = c["nao_alocados"] + c["agendados"] + c["realizados"]
        self.assertNotIn("Convidado", self.nomes(todos))

    def test_formacao_de_outro_ciclo_nao_conta(self):
        Formacao.objects.create(data=date(2030, 3, 10), tema=self.a, situacao="realizada")
        c = services.classificar_cobertura(self.ciclo)
        self.assertIn("A", self.nomes(c["nao_alocados"]))

    # CA004: a soma das três listas é o total de temas da apostila

    def test_soma_das_listas_e_o_total_de_temas(self):
        self.formacao(self.a, "prevista")
        self.formacao(self.b, "realizada", 11)
        c = services.classificar_cobertura(self.ciclo)
        total = len(c["nao_alocados"]) + len(c["agendados"]) + len(c["realizados"])
        self.assertEqual(total, Tema.objects.filter(tipo="apostila").count())


class CoberturaTelaTests(TestCase):
    def setUp(self):
        self.ciclo = Ciclo.objects.create(nome="2027", inicio=date(2027, 2, 1), fim=date(2027, 12, 15))
        Tema.objects.create(nome="Kerigma", tipo="apostila", rotulo="1")

    def entrar(self, perfil):
        self.client.force_login(Usuario.objects.create_user(username=perfil, password="x", perfil=perfil))

    def test_anonimo_vai_para_o_login(self):
        self.assertEqual(self.client.get(URL).status_code, 302)

    def test_coordenador_e_formador_veem_a_tela(self):
        for perfil in (Usuario.Perfil.COORDENADOR, Usuario.Perfil.FORMADOR):
            self.entrar(perfil)
            resposta = self.client.get(URL, {"ciclo": self.ciclo.pk})
            self.assertContains(resposta, "Não alocados (1)")
            self.assertContains(resposta, "Kerigma")