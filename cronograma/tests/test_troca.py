from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from acesso.models import Usuario
from cadastros.models import Ciclo, Formador
from cronograma import services
from cronograma.models import Formacao, TrocaFormador


class TrocaServicoTests(TestCase):
    def setUp(self):
        self.ciclo = Ciclo.objects.create(nome="2027", inicio=date(2027, 1, 1), fim=date(2027, 12, 31))
        mk = lambda n: Formador.objects.create(nome=n, inicio_servico=date(2020, 1, 1), capacitado=True)
        self.ana, self.bia, self.caio = mk("Ana"), mk("Bia"), mk("Caio")
        self.f = Formacao.objects.create(data=date(2027, 3, 10), formador=self.ana)

    def test_troca_gera_registro_com_anterior_e_novo(self):
        formacao, _ = services.trocar_formador(self.f.pk, self.bia.pk)
        troca = TrocaFormador.objects.get()
        self.assertEqual((troca.formador_anterior, troca.formador_novo), (self.ana, self.bia))
        self.assertEqual(formacao.formador, self.bia)

    def test_duas_trocas_geram_dois_registros(self):
        services.trocar_formador(self.f.pk, self.bia.pk)
        services.trocar_formador(self.f.pk, self.caio.pk)
        self.assertEqual(TrocaFormador.objects.count(), 2)
        self.assertEqual(len(services.trocas_da_formacao(self.f.pk)), 2)

    def test_mesmo_formador_nao_gera_registro(self):
        with self.assertRaises(ValidationError):
            services.trocar_formador(self.f.pk, self.ana.pk)
        self.assertEqual(TrocaFormador.objects.count(), 0)

    def test_formacao_sem_formador_nao_e_troca(self):
        sem = Formacao.objects.create(data=date(2027, 4, 10))
        with self.assertRaises(ValidationError):
            services.trocar_formador(sem.pk, self.bia.pk)
        self.assertEqual(TrocaFormador.objects.count(), 0)

    def test_cancelamento_nao_e_troca(self):
        services.alterar_situacao(self.f.pk, "cancelada")
        self.assertEqual(TrocaFormador.objects.count(), 0)
        self.f.refresh_from_db()
        self.assertEqual(self.f.formador, self.ana)

    def test_formador_inativo_e_recusado(self):
        Formador.objects.filter(pk=self.bia.pk).update(ativo=False)
        with self.assertRaises(ValidationError):
            services.trocar_formador(self.f.pk, self.bia.pk)
        self.assertEqual(TrocaFormador.objects.count(), 0)

    def test_numero_de_trocas_do_ciclo(self):
        services.trocar_formador(self.f.pk, self.bia.pk)
        services.trocar_formador(self.f.pk, self.caio.pk)
        self.assertEqual(services.numero_de_trocas_do_ciclo(self.ciclo), 2)


class TrocaTelaTests(TestCase):
    def setUp(self):
        Ciclo.objects.create(nome="2027", inicio=date(2027, 1, 1), fim=date(2027, 12, 31))
        self.ana = Formador.objects.create(nome="Ana", inicio_servico=date(2020, 1, 1), capacitado=True)
        self.bia = Formador.objects.create(nome="Bia", inicio_servico=date(2020, 1, 1), capacitado=True)
        self.f = Formacao.objects.create(data=date(2027, 3, 10), formador=self.ana)
        self.url = reverse("cronograma:trocar_formador", args=[self.f.pk])

    def test_coordenador_troca_e_ve_o_historico(self):
        c = Usuario.objects.create_user(username="c", password="x", perfil=Usuario.Perfil.COORDENADOR)
        self.client.force_login(c)
        self.client.post(self.url, {"formador_id": self.bia.pk})
        resposta = self.client.get(self.url)
        self.assertContains(resposta, "Ana")
        self.assertContains(resposta, "Bia")
        self.assertEqual(TrocaFormador.objects.count(), 1)

    def test_formador_recebe_403(self):
        u = Usuario.objects.create_user(username="f", password="x", perfil=Usuario.Perfil.FORMADOR)
        self.client.force_login(u)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_anonimo_vai_para_o_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)