from datetime import date

from django.test import TestCase
from django.urls import reverse

from acesso.models import Usuario
from cadastros.models import Ciclo, Formador
from cronograma import services
from cronograma.models import Formacao

URL = reverse("cronograma:carga")


class CargaServicoTests(TestCase):
    def setUp(self):
        self.ciclo = Ciclo.objects.create(nome="2027", inicio=date(2027, 1, 1), fim=date(2027, 12, 31))
        self.ana = Formador.objects.create(nome="Ana", inicio_servico=date(2020, 1, 1), capacitado=True)
        self.bia = Formador.objects.create(nome="Bia", inicio_servico=date(2020, 1, 1), capacitado=True)

    def formacao(self, formador, situacao="realizada", dia=10, ano=2027):
        return Formacao.objects.create(data=date(ano, 3, dia), formador=formador, situacao=situacao)

    def carga(self):
        return {f.nome: total for f, total in services.carga_por_formador(self.ciclo)}

    def test_conta_formacoes_realizadas_por_formador(self):
        self.formacao(self.ana, dia=10)
        self.formacao(self.ana, dia=17)
        self.formacao(self.bia, dia=24)
        self.assertEqual(self.carga(), {"Ana": 2, "Bia": 1})

    def test_canceladas_e_previstas_nao_contam(self):
        self.formacao(self.ana, "cancelada")
        self.formacao(self.ana, "prevista", 17)
        self.assertEqual(self.carga()["Ana"], 0)

    def test_formador_sem_formacao_aparece_com_zero(self):
        self.formacao(self.ana)
        self.assertEqual(self.carga()["Bia"], 0)

    def test_formacao_de_outro_ciclo_nao_conta(self):
        self.formacao(self.ana, ano=2030)
        self.assertEqual(self.carga()["Ana"], 0)

    def test_ordena_do_maior_para_o_menor(self):
        self.formacao(self.bia, dia=10)
        self.formacao(self.bia, dia=17)
        self.formacao(self.ana, dia=24)
        nomes = [f.nome for f, _ in services.carga_por_formador(self.ciclo)]
        self.assertEqual(nomes, ["Bia", "Ana"])

    def test_formador_inativo_fica_fora(self):
        self.formacao(self.ana)
        Formador.objects.filter(pk=self.ana.pk).update(ativo=False)
        self.assertNotIn("Ana", self.carga())


class CargaTelaTests(TestCase):
    def test_anonimo_vai_para_o_login(self):
        self.assertEqual(self.client.get(URL).status_code, 302)

    def test_formador_recebe_403(self):
        f = Usuario.objects.create_user(username="f", password="x", perfil=Usuario.Perfil.FORMADOR)
        self.client.force_login(f)
        self.assertEqual(self.client.get(URL).status_code, 403)

    def test_coordenador_ve_a_carga_do_ciclo(self):
        ciclo = Ciclo.objects.create(nome="2027", inicio=date(2027, 1, 1), fim=date(2027, 12, 31))
        Formador.objects.create(nome="Ana", inicio_servico=date(2020, 1, 1), capacitado=True)
        c = Usuario.objects.create_user(username="c", password="x", perfil=Usuario.Perfil.COORDENADOR)
        self.client.force_login(c)
        resposta = self.client.get(URL, {"ciclo": ciclo.pk})
        self.assertContains(resposta, "Ana")