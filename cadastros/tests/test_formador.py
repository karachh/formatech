from datetime import date
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from acesso.models import Usuario
from cadastros import repositories, services
from cadastros.models import Formador
from cadastros.tests.test_tela_ciclos import ComoCoordenador

URL = reverse("cadastros:formadores")


class RepositorioFormadorTests(TestCase):
    def setUp(self):
        self.ativo = Formador.objects.create(
            nome="Ana", inicio_servico=date(2025, 1, 10), capacitado=True
        )
        self.inativo = Formador.objects.create(
            nome="Bruno", inicio_servico=date(2024, 5, 2), capacitado=False, ativo=False
        )

    def test_lista_formadores_ativos_e_inativos_por_nome(self):
        self.assertEqual(repositories.listar_formadores(), [self.ativo, self.inativo])

    def test_busca_formador_pelo_id(self):
        self.assertEqual(repositories.buscar_formador(self.ativo.pk), self.ativo)

    def test_buscar_formador_inexistente_levanta_does_not_exist(self):
        with self.assertRaises(Formador.DoesNotExist):
            repositories.buscar_formador(999_999)

    def test_salva_formador(self):
        formador = Formador(nome="Carla", inicio_servico=date(2026, 2, 1), capacitado=False)
        repositories.salvar_formador(formador)
        self.assertIsNotNone(formador.pk)
        self.assertTrue(formador.ativo)

    def test_inativa_sem_apagar_o_registro(self):
        repositories.inativar_formador(self.ativo)
        self.ativo.refresh_from_db()
        self.assertFalse(self.ativo.ativo)
        self.assertTrue(Formador.objects.filter(pk=self.ativo.pk).exists())


class ServicoFormadorTests(SimpleTestCase):
    @mock.patch("cadastros.services.repositories.salvar_formador", side_effect=lambda formador: formador)
    def test_cadastra_formador_ativo(self, salvar):
        formador = services.cadastrar_formador("  Ana  ", date(2025, 1, 10), True)
        salvar.assert_called_once_with(formador)
        self.assertEqual(formador.nome, "Ana")
        self.assertTrue(formador.ativo)

    @mock.patch("cadastros.services.repositories.salvar_formador")
    def test_data_de_inicio_e_obrigatoria(self, salvar):
        with self.assertRaises(ValidationError) as erro:
            services.cadastrar_formador("Ana", None, False)
        self.assertIn("inicio_servico", erro.exception.message_dict)
        salvar.assert_not_called()

    @mock.patch("cadastros.services.repositories.salvar_formador", side_effect=lambda formador: formador)
    @mock.patch("cadastros.services.repositories.buscar_formador")
    def test_edita_dados_sem_reativar_formador(self, buscar, salvar):
        formador = Formador(
            pk=1,
            nome="Ana",
            inicio_servico=date(2025, 1, 10),
            capacitado=False,
            ativo=False,
        )
        buscar.return_value = formador

        editado = services.editar_formador(1, "Ana Silva", date(2025, 2, 1), True)

        salvar.assert_called_once_with(formador)
        self.assertEqual(editado.nome, "Ana Silva")
        self.assertTrue(editado.capacitado)
        self.assertFalse(editado.ativo)

    @mock.patch(
        "cadastros.services.repositories.inativar_formador",
        side_effect=lambda formador: setattr(formador, "ativo", False) or formador,
    )
    @mock.patch("cadastros.services.repositories.buscar_formador")
    def test_inativa_formador(self, buscar, inativar):
        formador = Formador(
            pk=1,
            nome="Ana",
            inicio_servico=date(2025, 1, 10),
            capacitado=True,
        )
        buscar.return_value = formador

        resultado = services.inativar_formador(1)

        inativar.assert_called_once_with(formador)
        self.assertFalse(resultado.ativo)

    @mock.patch("cadastros.services.repositories.inativar_formador")
    @mock.patch("cadastros.services.repositories.buscar_formador")
    def test_nao_inativa_novamente(self, buscar, inativar):
        formador = Formador(
            pk=1,
            nome="Ana",
            inicio_servico=date(2025, 1, 10),
            capacitado=True,
            ativo=False,
        )
        buscar.return_value = formador

        with self.assertRaises(ValidationError):
            services.inativar_formador(1)

        inativar.assert_not_called()


class TelaFormadoresTests(ComoCoordenador, TestCase):
    def postar(self, nome="Ana", inicio_servico="2025-01-10", capacitado="on"):
        return self.client.post(
            URL,
            {"nome": nome, "inicio_servico": inicio_servico, "capacitado": capacitado},
            follow=True,
        )

    def test_lista_vazia(self):
        self.assertContains(self.client.get(URL), "Nenhum formador cadastrado.")

    def test_cadastrar_mostra_formador_ativo_na_lista(self):
        resposta = self.postar()

        self.assertRedirects(resposta, URL)
        self.assertContains(resposta, 'Formador "Ana" cadastrado.')
        self.assertContains(resposta, "Ativo")
        formador = Formador.objects.get(nome="Ana")
        self.assertTrue(formador.ativo)
        self.assertTrue(formador.capacitado)

    def test_cadastro_com_capacitacao_desmarcada_salva_false(self):
        resposta = self.postar(capacitado="")

        self.assertRedirects(resposta, URL)
        self.assertFalse(Formador.objects.get(nome="Ana").capacitado)

    def test_data_de_inicio_obrigatoria_na_tela(self):
        resposta = self.postar(inicio_servico="")

        self.assertFormError(resposta.context["form"], "inicio_servico", "Este campo é obrigatório.")
        self.assertFalse(Formador.objects.exists())

    def test_listagem_mostra_ativos_e_inativos_com_situacao(self):
        self.postar(nome="Ana")
        inativo = Formador.objects.create(
            nome="Bruno",
            inicio_servico=date(2024, 5, 2),
            capacitado=False,
            ativo=False,
        )

        resposta = self.client.get(URL)

        self.assertContains(resposta, "Ana")
        self.assertContains(resposta, "Bruno")
        self.assertContains(resposta, "Ativo")
        self.assertContains(resposta, "Inativo")
        self.assertNotContains(resposta, reverse("cadastros:inativar_formador", args=[inativo.pk]))

    def test_editar_altera_campos_e_preserva_inativo(self):
        formador = Formador.objects.create(
            nome="Ana",
            inicio_servico=date(2025, 1, 10),
            capacitado=False,
            ativo=False,
        )
        url = reverse("cadastros:editar_formador", args=[formador.pk])

        resposta = self.client.post(
            url,
            {"nome": "Ana Silva", "inicio_servico": "2025-02-01", "capacitado": "on"},
            follow=True,
        )

        self.assertRedirects(resposta, URL)
        formador.refresh_from_db()
        self.assertEqual(formador.nome, "Ana Silva")
        self.assertEqual(formador.inicio_servico, date(2025, 2, 1))
        self.assertTrue(formador.capacitado)
        self.assertFalse(formador.ativo)

    def test_inativar_por_post_preserva_registro(self):
        formador = Formador.objects.create(
            nome="Ana",
            inicio_servico=date(2025, 1, 10),
            capacitado=True,
        )
        url = reverse("cadastros:inativar_formador", args=[formador.pk])

        resposta = self.client.post(url, follow=True)

        self.assertRedirects(resposta, URL)
        self.assertContains(resposta, 'Formador "Ana" inativado.')
        formador.refresh_from_db()
        self.assertFalse(formador.ativo)
        self.assertTrue(Formador.objects.filter(pk=formador.pk).exists())

    def test_get_nao_inativa_formador(self):
        formador = Formador.objects.create(
            nome="Ana",
            inicio_servico=date(2025, 1, 10),
            capacitado=True,
        )
        url = reverse("cadastros:inativar_formador", args=[formador.pk])

        resposta = self.client.get(url)

        self.assertEqual(resposta.status_code, 405)
        formador.refresh_from_db()
        self.assertTrue(formador.ativo)

    def test_formador_nao_pode_operar_cadastro(self):
        formador_usuario = Usuario.objects.create_user(
            username="form",
            password="x",
            perfil=Usuario.Perfil.FORMADOR,
        )
        self.client.force_login(formador_usuario)
        formador = Formador.objects.create(
            nome="Ana",
            inicio_servico=date(2025, 1, 10),
            capacitado=True,
        )

        self.assertEqual(self.client.get(URL).status_code, 403)
        self.assertEqual(
            self.client.post(URL, {"nome": "Bruno", "inicio_servico": "2025-02-01"}).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(reverse("cadastros:editar_formador", args=[formador.pk])).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(reverse("cadastros:inativar_formador", args=[formador.pk])).status_code,
            403,
        )

    def test_anonimo_e_redirecionado_em_todas_as_operacoes(self):
        formador = Formador.objects.create(
            nome="Ana",
            inicio_servico=date(2025, 1, 10),
            capacitado=True,
        )
        self.client.logout()

        self.assertEqual(self.client.get(URL).status_code, 302)
        self.assertEqual(
            self.client.post(URL, {"nome": "Bruno", "inicio_servico": "2025-02-01"}).status_code,
            302,
        )
        self.assertEqual(
            self.client.get(reverse("cadastros:editar_formador", args=[formador.pk])).status_code,
            302,
        )
        self.assertEqual(
            self.client.post(reverse("cadastros:inativar_formador", args=[formador.pk])).status_code,
            302,
        )
        formador.refresh_from_db()
        self.assertTrue(formador.ativo)

    def test_formador_inexistente_na_edicao_da_404(self):
        resposta = self.client.get(reverse("cadastros:editar_formador", args=[999_999]))
        self.assertEqual(resposta.status_code, 404)