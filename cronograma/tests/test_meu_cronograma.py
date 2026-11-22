"""US018: o formador consulta o cronograma, somente leitura."""

from datetime import date

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from acesso.models import Usuario
from cadastros.models import Formador
from cronograma import services
from cronograma.models import Formacao
from cronograma.tests.test_formacao import ComDados

URL = reverse("cronograma:meu_cronograma")


class ComFormadorLogado(ComDados):
    """Ana (de ComDados) ganha um login e entra no sistema."""

    def setUp(self):
        super().setUp()
        self.usuario = Usuario.objects.create_user(username="ana", password="x", perfil=Usuario.Perfil.FORMADOR)
        self.formador.usuario = self.usuario
        self.formador.save()
        self.outro = Formador.objects.create(nome="Bruno", inicio_servico=date(2020, 1, 10), capacitado=True)
        self.client.force_login(self.usuario)


class VinculoUsuarioFormadorTests(ComDados, TestCase):
    def test_banco_recusa_dois_formadores_no_mesmo_login(self):
        usuario = Usuario.objects.create_user(username="ana", password="x", perfil=Usuario.Perfil.FORMADOR)
        self.formador.usuario = usuario
        self.formador.save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Formador.objects.create(nome="Outra", inicio_servico=date(2020, 1, 10), capacitado=True, usuario=usuario)

    def test_varios_formadores_sem_login_sao_permitidos(self):
        Formador.objects.create(nome="Bruno", inicio_servico=date(2020, 1, 10), capacitado=True)
        self.assertEqual(Formador.objects.filter(usuario__isnull=True).count(), 2)

    def test_apagar_o_login_mantem_o_formador(self):
        usuario = Usuario.objects.create_user(username="ana", password="x", perfil=Usuario.Perfil.FORMADOR)
        self.formador.usuario = usuario
        self.formador.save()
        usuario.delete()
        self.formador.refresh_from_db()
        self.assertIsNone(self.formador.usuario)


class ServicoMeuCronogramaTests(ComFormadorLogado, TestCase):
    def test_encontra_o_formador_do_login(self):
        self.assertEqual(services.formador_do_usuario(self.usuario.pk), self.formador)

    def test_login_sem_vinculo_nao_tem_formador(self):
        sem_vinculo = Usuario.objects.create_user(username="carla", password="x", perfil=Usuario.Perfil.FORMADOR)
        self.assertIsNone(services.formador_do_usuario(sem_vinculo.pk))

    def test_datas_do_formador_so_traz_as_dele(self):
        minha = self.formacao(date(2027, 3, 6), formador=self.formador)
        self.formacao(date(2027, 3, 13), formador=self.outro)
        self.formacao(date(2027, 3, 20))
        formacoes = services.listar_formacoes_do_ciclo(self.ciclo)

        self.assertEqual(services.datas_do_formador(self.formador, formacoes), [minha])


class TelaMeuCronogramaTests(ComFormadorLogado, TestCase):
    """T018.1: visão somente leitura que destaca as datas do formador."""

    def setUp(self):
        super().setUp()
        self.minha = self.formacao(date(2027, 3, 6), tema=self.tema, formador=self.formador)
        self.de_outro = self.formacao(date(2027, 3, 13), formador=self.outro)

    def abrir(self):
        return self.client.get(URL, {"ciclo": self.ciclo.pk})

    def test_mostra_as_datas_em_que_esta_escalado(self):
        resposta = self.abrir()

        self.assertContains(resposta, "Minhas datas em Perseverança 2027")
        self.assertContains(resposta, "<li>06/03/2027 · Sagrada Tradição (Prevista)</li>", html=True)
        self.assertEqual(resposta.context["minhas"], [self.minha])

    def test_destaca_as_datas_dele_no_cronograma_completo(self):
        resposta = self.abrir()

        self.assertContains(resposta, '<tr class="minha">', count=1)
        self.assertContains(resposta, "<strong>Você</strong>", html=True)
        self.assertContains(resposta, "<td>Bruno</td>", html=True)

    def test_nao_oferece_nenhuma_acao_de_edicao(self):
        conteudo = self.abrir().content.decode()

        self.assertNotIn('method="post"', conteudo.split("<main>")[1])
        for url in (
            reverse("cronograma:editar_formacao", args=[self.minha.pk]),
            reverse("cronograma:escalar_formador", args=[self.de_outro.pk]),
            reverse("cronograma:alterar_situacao", args=[self.minha.pk]),
            reverse("presenca:lancar_presenca", args=[self.minha.pk]),
        ):
            self.assertNotIn(url, conteudo)

    def test_sem_formacoes_dele_avisa(self):
        self.minha.formador = None
        self.minha.save()

        self.assertContains(self.abrir(), "Você não está escalado em nenhuma formação deste ciclo.")

    def test_login_sem_vinculo_mostra_orientacao(self):
        self.client.force_login(
            Usuario.objects.create_user(username="carla", password="x", perfil=Usuario.Perfil.FORMADOR)
        )

        self.assertContains(self.abrir(), "Seu usuário ainda não está vinculado a um formador.")

    def test_home_do_formador_leva_ao_meu_cronograma(self):
        self.assertContains(self.client.get(reverse("acesso:home")), URL)

    def test_aceita_apenas_get(self):
        self.assertEqual(self.client.post(URL).status_code, 405)

    def test_coordenador_recebe_403(self):
        self.client.force_login(
            Usuario.objects.create_user(username="coord", password="x", perfil=Usuario.Perfil.COORDENADOR)
        )
        self.assertEqual(self.abrir().status_code, 403)

    def test_anonimo_vai_para_o_login(self):
        self.client.logout()
        self.assertEqual(self.abrir().status_code, 302)


class PermissaoDoFormadorTests(ComFormadorLogado, TestCase):
    """T018.2 (CA008): o formador não edita nada, nem digitando a URL direto."""

    def setUp(self):
        super().setUp()
        self.encontro = self.formacao(date(2027, 3, 6), tema=self.tema)

    def urls_do_coordenador(self):
        f = self.encontro.pk
        return [
            reverse("cronograma:cronograma"),
            reverse("cronograma:editar_formacao", args=[f]),
            reverse("cronograma:escalar_formador", args=[f]),
            reverse("cronograma:alterar_situacao", args=[f]),
            reverse("cronograma:exportar"),
            reverse("cronograma:carga"),
            reverse("presenca:lancar_presenca", args=[f]),
            reverse("cadastros:ciclos"),
            reverse("cadastros:formadores"),
            reverse("cadastros:editar_formador", args=[self.formador.pk]),
            reverse("cadastros:temas"),
            reverse("cadastros:perseverantes"),
        ]

    def test_get_nas_telas_do_coordenador_da_403(self):
        for url in self.urls_do_coordenador():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_post_nas_telas_do_coordenador_da_403_e_nao_altera_nada(self):
        for url in self.urls_do_coordenador():
            with self.subTest(url=url):
                resposta = self.client.post(
                    url, {"formador_id": self.formador.pk, "situacao": "realizada", "data": "2027-03-07"}
                )
                self.assertEqual(resposta.status_code, 403)

        self.encontro.refresh_from_db()
        self.assertIsNone(self.encontro.formador)
        self.assertEqual(self.encontro.situacao, Formacao.Situacao.PREVISTA)
        self.assertEqual(self.encontro.data, date(2027, 3, 6))
