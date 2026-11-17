from datetime import date

from django.test import TestCase
from django.urls import reverse

from acesso.models import Usuario
from cadastros.models import Formador, Tema
from cronograma import services
from cronograma.models import Formacao

URL = reverse("cronograma:historico")


class HistoricoConsultasTests(TestCase):
    def setUp(self):
        self.formador = Formador.objects.create(
            nome="Ana", inicio_servico=date(2020, 1, 1), capacitado=True
        )
        self.formador_inativo = Formador.objects.create(
            nome="Bruna", inicio_servico=date(2021, 1, 1), capacitado=True, ativo=False
        )
        self.formador_sem_historico = Formador.objects.create(
            nome="Carla", inicio_servico=date(2022, 1, 1), capacitado=True
        )
        self.tema = Tema.objects.create(nome="Kerigma", tipo=Tema.Tipo.APOSTILA)
        self.outro_tema = Tema.objects.create(nome="Oração", tipo=Tema.Tipo.APOSTILA)
        self.tema_sem_historico = Tema.objects.create(nome="Missão", tipo=Tema.Tipo.OPCIONAL)

    def criar_formacao(self, data, **campos):
        return Formacao.objects.create(data=data, **campos)

    def test_historico_do_formador_lista_ocorrencias_realizadas_por_data(self):
        self.criar_formacao(
            date(2026, 3, 10), formador=self.formador, tema=self.tema,
            situacao=Formacao.Situacao.REALIZADA,
        )
        self.criar_formacao(
            date(2026, 4, 12), formador=self.formador, tema=self.tema,
            situacao=Formacao.Situacao.REALIZADA,
        )
        self.criar_formacao(
            date(2026, 5, 14), formador=self.formador, tema=self.outro_tema,
            situacao=Formacao.Situacao.REALIZADA,
        )
        self.criar_formacao(
            date(2026, 6, 16), formador=self.formador, tema=self.tema,
            situacao=Formacao.Situacao.PREVISTA,
        )
        self.criar_formacao(
            date(2026, 7, 18), formador=self.formador, tema=self.outro_tema,
            situacao=Formacao.Situacao.CANCELADA,
        )
        self.criar_formacao(
            date(2026, 8, 20), formador=self.formador, tema=None,
            situacao=Formacao.Situacao.REALIZADA,
        )

        historico = services.historico_temas_por_formador(self.formador.pk)

        self.assertEqual(
            [(formacao.tema.nome, formacao.data) for formacao in historico],
            [
                ("Oração", date(2026, 5, 14)),
                ("Kerigma", date(2026, 4, 12)),
                ("Kerigma", date(2026, 3, 10)),
            ],
        )

    def test_historico_do_tema_inclui_formador_inativo_e_somente_realizados(self):
        self.criar_formacao(
            date(2026, 3, 10), formador=self.formador, tema=self.tema,
            situacao=Formacao.Situacao.REALIZADA,
        )
        self.criar_formacao(
            date(2026, 4, 12), formador=self.formador_inativo, tema=self.tema,
            situacao=Formacao.Situacao.REALIZADA,
        )
        self.criar_formacao(
            date(2026, 5, 14), formador=self.formador_inativo, tema=self.tema,
            situacao=Formacao.Situacao.PREVISTA,
        )
        self.criar_formacao(
            date(2026, 6, 16), formador=self.formador, tema=self.tema,
            situacao=Formacao.Situacao.CANCELADA,
        )
        self.criar_formacao(
            date(2026, 7, 18), formador=None, tema=self.tema,
            situacao=Formacao.Situacao.REALIZADA,
        )

        historico = services.historico_formadores_por_tema(self.tema.pk)

        self.assertEqual(
            [(formacao.formador.nome, formacao.data) for formacao in historico],
            [("Bruna", date(2026, 4, 12)), ("Ana", date(2026, 3, 10))],
        )

    def test_formador_e_tema_sem_historico_retorna_listas_vazias(self):
        self.assertEqual(
            services.historico_temas_por_formador(self.formador_sem_historico.pk),
            [],
        )
        self.assertEqual(
            services.historico_formadores_por_tema(self.tema_sem_historico.pk),
            [],
        )


class HistoricoTelaTests(TestCase):
    def setUp(self):
        self.formador = Formador.objects.create(
            nome="Ana", inicio_servico=date(2020, 1, 1), capacitado=True
        )
        self.formador_inativo = Formador.objects.create(
            nome="Bruna", inicio_servico=date(2021, 1, 1), capacitado=True, ativo=False
        )
        self.tema = Tema.objects.create(nome="Kerigma", tipo=Tema.Tipo.APOSTILA)
        self.outro_tema = Tema.objects.create(nome="Oração", tipo=Tema.Tipo.APOSTILA)
        self.coordenador = Usuario.objects.create_user(
            username="coord", password="x", perfil=Usuario.Perfil.COORDENADOR
        )
        self.usuario_formador = Usuario.objects.create_user(
            username="form", password="x", perfil=Usuario.Perfil.FORMADOR
        )

    def criar_formacao(self, data, **campos):
        return Formacao.objects.create(data=data, **campos)

    def test_busca_por_formador_exibe_temas_e_datas_em_ordem(self):
        self.criar_formacao(
            date(2026, 3, 10), formador=self.formador, tema=self.tema,
            situacao=Formacao.Situacao.REALIZADA,
        )
        self.criar_formacao(
            date(2026, 4, 12), formador=self.formador, tema=self.outro_tema,
            situacao=Formacao.Situacao.REALIZADA,
        )
        self.criar_formacao(
            date(2026, 5, 14), formador=self.formador, tema=self.tema,
            situacao=Formacao.Situacao.PREVISTA,
        )
        self.client.force_login(self.coordenador)

        resposta = self.client.get(URL, {"formador_id": self.formador.pk})

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["formador"], self.formador)
        self.assertEqual(len(resposta.context["historico_temas"]), 2)
        conteudo = resposta.content.decode()
        self.assertLess(conteudo.index("12/04/2026"), conteudo.index("10/03/2026"))
        self.assertContains(resposta, "Oração")
        self.assertContains(resposta, "Kerigma")
        self.assertNotContains(resposta, "14/05/2026")

    def test_busca_por_tema_exibe_formadores_inativos_e_datas(self):
        self.criar_formacao(
            date(2026, 3, 10), formador=self.formador, tema=self.tema,
            situacao=Formacao.Situacao.REALIZADA,
        )
        self.criar_formacao(
            date(2026, 4, 12), formador=self.formador_inativo, tema=self.tema,
            situacao=Formacao.Situacao.REALIZADA,
        )
        self.client.force_login(self.usuario_formador)

        resposta = self.client.get(URL, {"tema_id": self.tema.pk})

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["tema"], self.tema)
        self.assertEqual(len(resposta.context["historico_formadores"]), 2)
        self.assertContains(resposta, "Bruna")
        self.assertContains(resposta, "(inativo)")
        self.assertContains(resposta, "12/04/2026")
        self.assertContains(resposta, "10/03/2026")

    def test_buscas_sem_historico_exibem_mensagens_claras(self):
        self.client.force_login(self.coordenador)

        resposta_formador = self.client.get(URL, {"formador_id": self.formador.pk})
        self.assertContains(resposta_formador, "ainda não ministrou temas")

        resposta_tema = self.client.get(URL, {"tema_id": self.tema.pk})
        self.assertContains(resposta_tema, "Nenhum formador ministrou este tema")

    def test_tela_so_aceita_get(self):
        self.client.force_login(self.coordenador)
        self.assertEqual(self.client.post(URL).status_code, 405)

    def test_tela_exige_login_e_aceita_ambos_os_perfis(self):
        self.assertEqual(self.client.get(URL).status_code, 302)

        for usuario in (self.coordenador, self.usuario_formador):
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(URL).status_code, 200)

    def test_menu_dos_dois_perfis_aponta_para_o_historico(self):
        home = reverse("acesso:home")
        for usuario in (self.coordenador, self.usuario_formador):
            self.client.force_login(usuario)
            self.assertContains(self.client.get(home), f'href="{URL}"')
