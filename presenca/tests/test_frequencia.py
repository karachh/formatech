from datetime import date

from django.test import TestCase
from django.urls import reverse

from acesso.models import Usuario
from cadastros.models import Ciclo, Perseverante
from cronograma.models import Formacao
from presenca import services
from presenca.models import Presenca

URL = reverse("presenca:frequencia")


class FrequenciaTests(TestCase):
    def setUp(self):
        self.ciclo = Ciclo.objects.create(nome="2027", inicio=date(2027, 1, 1), fim=date(2027, 12, 31))
        self.p = Perseverante.objects.create(nome="Davi", ciclo=self.ciclo)

    def lancar(self, dia, situacao, formacao="prevista", ano=2027):
        f = Formacao.objects.create(data=date(ano, 3, dia), situacao=formacao)
        Presenca.objects.create(formacao=f, perseverante=self.p, situacao=situacao)

    def freq(self):
        return services.frequencia_do_perseverante(self.p)

    def test_conta_por_situacao(self):
        self.lancar(3, "presente")
        self.lancar(10, "presente")
        self.lancar(17, "ausente")
        self.lancar(24, "justificado")
        self.assertEqual(self.freq(), {"presente": 2, "ausente": 1, "justificado": 1})

    def test_sem_presencas_tudo_zero(self):
        self.assertEqual(self.freq(), {"presente": 0, "ausente": 0, "justificado": 0})

    def test_formacao_cancelada_nao_conta(self):
        self.lancar(3, "presente", formacao="cancelada")
        self.assertEqual(self.freq()["presente"], 0)

    def test_presenca_fora_do_ciclo_nao_conta(self):
        self.lancar(3, "presente", ano=2030)
        self.assertEqual(self.freq()["presente"], 0)

    def test_tela_mostra_a_contagem_ao_coordenador(self):
        self.lancar(3, "presente")
        c = Usuario.objects.create_user(username="c", password="x", perfil=Usuario.Perfil.COORDENADOR)
        self.client.force_login(c)
        resposta = self.client.get(URL, {"ciclo": self.ciclo.pk})
        self.assertContains(resposta, "Davi")
        self.assertContains(resposta, "<td>1</td>", html=True)


    def test_formador_recebe_403(self):
        f = Usuario.objects.create_user(username="f", password="x", perfil=Usuario.Perfil.FORMADOR)
        self.client.force_login(f)
        self.assertEqual(self.client.get(URL).status_code, 403)

    def test_anonimo_vai_para_o_login(self):
        self.assertEqual(self.client.get(URL).status_code, 302)