from datetime import date
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from acesso.models import Usuario
from cadastros import repositories, services
from cadastros.models import Ciclo, Perseverante
from cadastros.tests.test_tela_ciclos import ComoCoordenador

URL = reverse("cadastros:perseverantes")


class ModeloPerseveranteTests(TestCase):
    def setUp(self):
        self.ciclo = Ciclo.objects.create(
            nome="Perseverança 2025",
            inicio=date(2025, 2, 1),
            fim=date(2025, 12, 15),
        )

    def test_perseverante_pertence_ao_ciclo_e_comeca_ativo(self):
        participante = Perseverante.objects.create(nome="Ana", ciclo=self.ciclo)

        self.assertEqual(participante.ciclo, self.ciclo)
        self.assertTrue(participante.ativo)
        self.assertIsNotNone(participante.criado_em)
        self.assertIsNotNone(participante.atualizado_em)


class RepositorioPerseveranteTests(TestCase):
    def setUp(self):
        self.ciclo_a = Ciclo.objects.create(
            nome="Perseverança 2025",
            inicio=date(2025, 2, 1),
            fim=date(2025, 12, 15),
        )
        self.ciclo_b = Ciclo.objects.create(
            nome="Perseverança 2026",
            inicio=date(2026, 2, 1),
            fim=date(2026, 12, 15),
        )
        self.ativo = Perseverante.objects.create(nome="Ana", ciclo=self.ciclo_a)
        self.inativo = Perseverante.objects.create(
            nome="Bruna", ciclo=self.ciclo_a, ativo=False
        )
        self.outro_ciclo = Perseverante.objects.create(nome="Carla", ciclo=self.ciclo_b)

    def test_lista_por_ciclo_inclui_ativos_e_inativos(self):
        self.assertEqual(
            repositories.listar_perseverantes(self.ciclo_a.pk),
            [self.ativo, self.inativo],
        )

    def test_lista_nao_inclui_outros_ciclos(self):
        self.assertEqual(
            repositories.listar_perseverantes(self.ciclo_a.pk),
            [self.ativo, self.inativo],
        )
        self.assertEqual(
            repositories.listar_perseverantes(self.ciclo_b.pk),
            [self.outro_ciclo],
        )

    def test_lista_somente_ativos_do_ciclo(self):
        self.assertEqual(
            repositories.listar_perseverantes_ativos(self.ciclo_a.pk),
            [self.ativo],
        )

    def test_busca_por_id_e_levanta_quando_nao_existe(self):
        self.assertEqual(repositories.buscar_perseverante(self.ativo.pk), self.ativo)
        with self.assertRaises(Perseverante.DoesNotExist):
            repositories.buscar_perseverante(999_999)

    def test_salva_perseverante(self):
        participante = Perseverante(nome="Dani", ciclo=self.ciclo_a)
        repositories.salvar_perseverante(participante)
        self.assertIsNotNone(participante.pk)

    def test_inativa_sem_apagar_o_registro(self):
        repositories.inativar_perseverante(self.ativo)
        self.ativo.refresh_from_db()
        self.assertFalse(self.ativo.ativo)
        self.assertTrue(Perseverante.objects.filter(pk=self.ativo.pk).exists())


class ServicoPerseveranteTests(SimpleTestCase):
    @mock.patch(
        "cadastros.services.repositories.salvar_perseverante",
        side_effect=lambda participante: participante,
    )
    @mock.patch("cadastros.services.repositories.buscar_ciclo")
    def test_cadastra_com_ciclo_e_ativo(self, buscar_ciclo, salvar):
        ciclo = Ciclo(pk=1, nome="2025", inicio=date(2025, 2, 1), fim=date(2025, 12, 15))
        buscar_ciclo.return_value = ciclo

        participante = services.cadastrar_perseverante("  Ana  ", "1")

        buscar_ciclo.assert_called_once_with("1")
        salvar.assert_called_once_with(participante)
        self.assertEqual(participante.nome, "Ana")
        self.assertEqual(participante.ciclo, ciclo)
        self.assertTrue(participante.ativo)

    @mock.patch("cadastros.services.repositories.buscar_ciclo")
    def test_ciclo_inexistente_e_convertido_em_validacao(self, buscar_ciclo):
        buscar_ciclo.side_effect = Ciclo.DoesNotExist

        with self.assertRaises(ValidationError) as erro:
            services.cadastrar_perseverante("Ana", "99")

        self.assertIn("ciclo_id", erro.exception.message_dict)

    @mock.patch("cadastros.services.repositories.salvar_perseverante")
    @mock.patch("cadastros.services.repositories.buscar_ciclo")
    def test_nome_vazio_nao_e_salvo(self, buscar_ciclo, salvar):
        buscar_ciclo.return_value = Ciclo(
            pk=1,
            nome="2025",
            inicio=date(2025, 2, 1),
            fim=date(2025, 12, 15),
        )

        with self.assertRaises(ValidationError) as erro:
            services.cadastrar_perseverante("  ", "1")

        self.assertIn("nome", erro.exception.message_dict)
        salvar.assert_not_called()

    @mock.patch(
        "cadastros.services.repositories.salvar_perseverante",
        side_effect=lambda participante: participante,
    )
    @mock.patch("cadastros.services.repositories.buscar_ciclo")
    @mock.patch("cadastros.services.repositories.buscar_perseverante")
    def test_edita_nome_e_ciclo_sem_reativar(self, buscar, buscar_ciclo, salvar):
        ciclo_atual = Ciclo(pk=1, nome="2025", inicio=date(2025, 2, 1), fim=date(2025, 12, 15))
        novo_ciclo = Ciclo(pk=2, nome="2026", inicio=date(2026, 2, 1), fim=date(2026, 12, 15))
        participante = Perseverante(pk=3, nome="Ana", ciclo=ciclo_atual, ativo=False)
        buscar.return_value = participante
        buscar_ciclo.return_value = novo_ciclo

        editado = services.editar_perseverante(3, "Ana Silva", "2")

        salvar.assert_called_once_with(participante)
        self.assertEqual(editado.nome, "Ana Silva")
        self.assertEqual(editado.ciclo, novo_ciclo)
        self.assertFalse(editado.ativo)

    @mock.patch(
        "cadastros.services.repositories.inativar_perseverante",
        side_effect=lambda participante: setattr(participante, "ativo", False) or participante,
    )
    @mock.patch("cadastros.services.repositories.buscar_perseverante")
    def test_inativa(self, buscar, inativar):
        participante = Perseverante(
            pk=3,
            nome="Ana",
            ciclo_id=1,
            ativo=True,
        )
        buscar.return_value = participante

        resultado = services.inativar_perseverante(3)

        inativar.assert_called_once_with(participante)
        self.assertFalse(resultado.ativo)

    @mock.patch("cadastros.services.repositories.inativar_perseverante")
    @mock.patch("cadastros.services.repositories.buscar_perseverante")
    def test_nao_inativa_novamente(self, buscar, inativar):
        buscar.return_value = Perseverante(
            pk=3,
            nome="Ana",
            ciclo_id=1,
            ativo=False,
        )

        with self.assertRaises(ValidationError):
            services.inativar_perseverante(3)

        inativar.assert_not_called()


class TelaPerseverantesTests(ComoCoordenador, TestCase):
    def setUp(self):
        super().setUp()
        self.ciclo = Ciclo.objects.create(
            nome="Perseverança 2025",
            inicio=date(2025, 2, 1),
            fim=date(2025, 12, 15),
        )
        self.outro_ciclo = Ciclo.objects.create(
            nome="Perseverança 2026",
            inicio=date(2026, 2, 1),
            fim=date(2026, 12, 15),
        )

    def postar(self, nome="Ana", ciclo_id=None):
        return self.client.post(
            URL,
            {"nome": nome, "ciclo_id": ciclo_id or self.ciclo.pk},
            follow=True,
        )

    def test_cadastro_cria_ativo_e_volta_filtrado_no_ciclo(self):
        resposta = self.postar()

        self.assertRedirects(resposta, f"{URL}?ciclo={self.ciclo.pk}")
        self.assertContains(resposta, "Perseverante “Ana” cadastrado.")
        participante = Perseverante.objects.get(nome="Ana")
        self.assertEqual(participante.ciclo, self.ciclo)
        self.assertTrue(participante.ativo)

    def test_lista_filtra_por_ciclo_e_mostra_situacao(self):
        ativo = Perseverante.objects.create(nome="Ana", ciclo=self.ciclo)
        inativo = Perseverante.objects.create(nome="Bia", ciclo=self.ciclo, ativo=False)
        outro = Perseverante.objects.create(nome="Clara", ciclo=self.outro_ciclo)

        resposta = self.client.get(URL, {"ciclo": self.ciclo.pk})

        self.assertContains(resposta, ativo.nome)
        self.assertContains(resposta, inativo.nome)
        self.assertContains(resposta, "Ativo")
        self.assertContains(resposta, "Inativo")
        self.assertNotContains(resposta, outro.nome)

    def test_edicao_altera_nome_e_ciclo(self):
        participante = Perseverante.objects.create(nome="Ana", ciclo=self.ciclo)
        url = reverse("cadastros:editar_perseverante", args=[participante.pk])

        resposta = self.client.post(
            url,
            {"nome": "Ana Silva", "ciclo_id": self.outro_ciclo.pk},
            follow=True,
        )

        self.assertRedirects(resposta, f"{URL}?ciclo={self.outro_ciclo.pk}")
        participante.refresh_from_db()
        self.assertEqual(participante.nome, "Ana Silva")
        self.assertEqual(participante.ciclo, self.outro_ciclo)

    def test_inativacao_post_preserva_registro(self):
        participante = Perseverante.objects.create(nome="Ana", ciclo=self.ciclo)
        url = reverse("cadastros:inativar_perseverante", args=[participante.pk])

        resposta = self.client.post(url, follow=True)

        self.assertRedirects(resposta, f"{URL}?ciclo={self.ciclo.pk}")
        self.assertContains(resposta, "Perseverante “Ana” inativado.")
        participante.refresh_from_db()
        self.assertFalse(participante.ativo)
        self.assertTrue(Perseverante.objects.filter(pk=participante.pk).exists())

    def test_get_nao_inativa(self):
        participante = Perseverante.objects.create(nome="Ana", ciclo=self.ciclo)
        url = reverse("cadastros:inativar_perseverante", args=[participante.pk])

        self.assertEqual(self.client.get(url).status_code, 405)
        participante.refresh_from_db()
        self.assertTrue(participante.ativo)

    def test_formador_nao_pode_operar_perseverantes(self):
        usuario = Usuario.objects.create_user(
            username="form",
            password="x",
            perfil=Usuario.Perfil.FORMADOR,
        )
        self.client.force_login(usuario)
        participante = Perseverante.objects.create(nome="Ana", ciclo=self.ciclo)

        self.assertEqual(self.client.get(URL).status_code, 403)
        self.assertEqual(self.postar().status_code, 403)
        self.assertEqual(
            self.client.get(reverse("cadastros:editar_perseverante", args=[participante.pk])).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(reverse("cadastros:inativar_perseverante", args=[participante.pk])).status_code,
            403,
        )

    def test_anonimo_e_redirecionado(self):
        self.client.logout()
        self.assertEqual(self.client.get(URL).status_code, 302)
        self.assertEqual(self.client.post(URL, {}).status_code, 302)