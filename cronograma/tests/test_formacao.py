from datetime import date
from unittest import mock

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from acesso.models import Usuario
from cadastros.models import Ciclo, Formador, Tema
from cadastros.tests.test_tela_ciclos import ComoCoordenador
from cronograma import repositories, services
from cronograma.models import Formacao

URL = reverse("cronograma:cronograma")



class ComDados:
    """Um ciclo, um tema e um formador ativo para os testes que usam o banco."""

    def setUp(self):
        super().setUp()
        self.ciclo = Ciclo.objects.create(
            nome="Perseverança 2027", inicio=date(2027, 2, 1), fim=date(2027, 12, 15)
        )
        self.tema = Tema.objects.create(nome="Sagrada Tradição", tipo=Tema.Tipo.APOSTILA, rotulo="1")
        self.formador = Formador.objects.create(
            nome="Ana", inicio_servico=date(2020, 1, 10), capacitado=True
        )

    def formacao(self, data, **campos):
        return Formacao.objects.create(data=data, **campos)


class ModeloFormacaoTests(ComDados, TestCase):
    def test_comeca_prevista_sem_tema_e_sem_formador(self):
        formacao = self.formacao(date(2027, 3, 6))

        self.assertEqual(formacao.situacao, Formacao.Situacao.PREVISTA)
        self.assertIsNone(formacao.tema)
        self.assertIsNone(formacao.formador)
        self.assertIsNotNone(formacao.criado_em)
        self.assertIsNotNone(formacao.atualizado_em)

    def test_banco_recusa_situacao_invalida(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.formacao(date(2027, 3, 6), situacao="adiada")

    def test_ciclo_nao_e_campo_da_formacao(self):
        # RN002: o ciclo é derivado da data, não guardado.
        nomes = [campo.name for campo in Formacao._meta.get_fields()]
        self.assertNotIn("ciclo", nomes)


class RepositorioFormacaoTests(ComDados, TestCase):
    def test_lista_do_ciclo_em_ordem_cronologica_incluindo_os_extremos(self):
        meio = self.formacao(date(2027, 5, 10))
        ultimo_dia = self.formacao(date(2027, 12, 15))
        primeiro_dia = self.formacao(date(2027, 2, 1))
        self.formacao(date(2027, 1, 31))
        self.formacao(date(2027, 12, 16))

        self.assertEqual(
            repositories.listar_formacoes_do_ciclo(self.ciclo),
            [primeiro_dia, meio, ultimo_dia],
        )


CICLO = Ciclo(pk=1, nome="2027", inicio=date(2027, 2, 1), fim=date(2027, 12, 15))
TEMA = Tema(pk=2, nome="Sagrada Tradição", tipo=Tema.Tipo.APOSTILA, rotulo="1")
FORMADOR = Formador(pk=3, nome="Ana", inicio_servico=date(2020, 1, 10), capacitado=True, ativo=True)


class ServicoFormacaoTests(SimpleTestCase):
    """Regra de negócio sem banco: os repositórios e a app cadastros são simulados."""

    def setUp(self):
        self.salvar = self.simular(
            "cronograma.services.repositories.salvar_formacao",
            side_effect=lambda formacao: formacao,
        )
        self.ciclo_da_data = self.simular(
            "cronograma.services.cadastros.buscar_ciclo_da_data", return_value=CICLO
        )
        self.buscar_tema = self.simular("cronograma.services.cadastros.buscar_tema", return_value=TEMA)
        self.buscar_formador = self.simular(
            "cronograma.services.cadastros.buscar_formador", return_value=FORMADOR
        )

    def simular(self, alvo, **opcoes):
        simulacao = mock.patch(alvo, **opcoes)
        self.addCleanup(simulacao.stop)
        return simulacao.start()

    def test_agenda_com_situacao_inicial_prevista(self):
        formacao = services.agendar_formacao(date(2027, 3, 6), "2", "3", "  Encontro de março  ")

        self.salvar.assert_called_once_with(formacao)
        self.ciclo_da_data.assert_called_once_with(date(2027, 3, 6))
        self.assertEqual(formacao.situacao, Formacao.Situacao.PREVISTA)
        self.assertEqual(formacao.tema, TEMA)
        self.assertEqual(formacao.formador, FORMADOR)
        self.assertEqual(formacao.descricao, "Encontro de março")

    def test_tema_e_formador_podem_ficar_em_branco(self):
        formacao = services.agendar_formacao(date(2027, 3, 6), "", "")

        self.assertIsNone(formacao.tema)
        self.assertIsNone(formacao.formador)
        self.buscar_tema.assert_not_called()
        self.buscar_formador.assert_not_called()

    def test_data_fora_de_ciclo_e_recusada(self):
        self.ciclo_da_data.return_value = None

        with self.assertRaises(ValidationError) as erro:
            services.agendar_formacao(date(2030, 3, 6), "2", "3")

        self.assertEqual(erro.exception.message_dict["data"], [services.MENSAGEM_SEM_CICLO])
        self.salvar.assert_not_called()

    def test_formador_inativo_e_recusado(self):
        self.buscar_formador.return_value = Formador(
            pk=4, nome="Bruno", inicio_servico=date(2020, 1, 10), capacitado=True, ativo=False
        )

        with self.assertRaises(ValidationError) as erro:
            services.agendar_formacao(date(2027, 3, 6), "2", "4")

        self.assertIn("formador_id", erro.exception.message_dict)
        self.salvar.assert_not_called()

    def test_tema_inexistente_vira_erro_de_validacao(self):
        self.buscar_tema.side_effect = Tema.DoesNotExist

        with self.assertRaises(ValidationError) as erro:
            services.agendar_formacao(date(2027, 3, 6), "99", "")

        self.assertIn("tema_id", erro.exception.message_dict)
        self.salvar.assert_not_called()

    def test_edicao_nao_muda_formador_nem_situacao(self):
        existente = Formacao(
            pk=5,
            data=date(2027, 3, 6),
            tema=TEMA,
            formador=FORMADOR,
            situacao=Formacao.Situacao.REALIZADA,
        )
        with mock.patch("cronograma.services.repositories.buscar_formacao", return_value=existente):
            editada = services.editar_formacao(5, date(2027, 4, 10), "", "Retiro")

        self.assertEqual(editada.data, date(2027, 4, 10))
        self.assertIsNone(editada.tema)
        self.assertEqual(editada.descricao, "Retiro")
        self.assertEqual(editada.formador, FORMADOR)
        self.assertEqual(editada.situacao, Formacao.Situacao.REALIZADA)


class TelaCronogramaTests(ComoCoordenador, ComDados, TestCase):
    def agendar(self, **campos):
        dados = {
            "data": "2027-03-06",
            "tema_id": self.tema.pk,
            "formador_id": self.formador.pk,
            "descricao": "",
        }
        dados.update(campos)
        return self.client.post(URL, dados, follow=True)

    def test_agendada_aparece_no_cronograma_do_ciclo(self):
        resposta = self.agendar()

        self.assertRedirects(resposta, f"{URL}?ciclo={self.ciclo.pk}")
        self.assertContains(resposta, "Formação de 06/03/2027 agendada.")
        self.assertEqual(resposta.context["formacoes"], [Formacao.objects.get()])
        self.assertContains(resposta, "<td>06/03/2027</td>", html=True)
        self.assertContains(resposta, "<td>Sagrada Tradição</td>", html=True)
        self.assertContains(resposta, "<td>Ana</td>", html=True)
        self.assertContains(resposta, "<td>Prevista</td>", html=True)

    def test_cronograma_em_ordem_cronologica(self):
        depois = self.formacao(date(2027, 9, 4))
        antes = self.formacao(date(2027, 3, 6))

        resposta = self.client.get(URL, {"ciclo": self.ciclo.pk})

        self.assertEqual(resposta.context["formacoes"], [antes, depois])
        conteudo = resposta.content.decode()
        self.assertLess(conteudo.index("06/03/2027"), conteudo.index("04/09/2027"))

    def test_sem_escolha_mostra_o_ciclo_de_hoje(self):
        with mock.patch("cronograma.services.timezone.localdate", return_value=date(2027, 5, 1)):
            resposta = self.client.get(URL)

        self.assertEqual(resposta.context["ciclo"], self.ciclo)

    def test_formulario_nao_pede_o_ciclo(self):
        resposta = self.client.get(URL)

        self.assertEqual(
            list(resposta.context["form"].fields),
            ["data", "tema_id", "formador_id", "descricao"],
        )

    def test_data_sem_ciclo_mostra_erro_e_nao_grava(self):
        resposta = self.agendar(data="2030-03-06")

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, services.MENSAGEM_SEM_CICLO)
        self.assertFalse(Formacao.objects.exists())

    def test_formador_inativo_nao_aparece_na_escolha(self):
        Formador.objects.create(
            nome="Bruno", inicio_servico=date(2020, 1, 10), capacitado=False, ativo=False
        )

        self.assertNotContains(self.client.get(URL), "Bruno")

    def test_escolha_de_tema_separa_apostila_e_opcionais(self):
        Tema.objects.create(nome="Retiro de Carnaval", tipo=Tema.Tipo.OPCIONAL)

        resposta = self.client.get(URL)

        self.assertContains(resposta, "Sem tema")
        self.assertContains(resposta, "Temas da apostila")
        self.assertContains(resposta, "Temas opcionais")
        self.assertContains(resposta, "Retiro de Carnaval")

    def test_edicao_altera_data_tema_e_descricao_mas_nao_o_formador(self):
        outro = Formador.objects.create(nome="Carla", inicio_servico=date(2021, 3, 1), capacitado=True)
        formacao = self.formacao(date(2027, 3, 6), tema=self.tema, formador=self.formador)
        url = reverse("cronograma:editar_formacao", args=[formacao.pk])

        resposta = self.client.post(
            url,
            {"data": "2027-04-10", "tema_id": "", "descricao": "Retiro", "formador_id": outro.pk},
            follow=True,
        )

        self.assertRedirects(resposta, f"{URL}?ciclo={self.ciclo.pk}")
        formacao.refresh_from_db()
        self.assertEqual(formacao.data, date(2027, 4, 10))
        self.assertIsNone(formacao.tema)
        self.assertEqual(formacao.descricao, "Retiro")
        self.assertEqual(formacao.formador, self.formador)

    def test_editar_inexistente_da_404(self):
        url = reverse("cronograma:editar_formacao", args=[999_999])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_formador_recebe_403(self):
        usuario = Usuario.objects.create_user(
            username="form", password="x", perfil=Usuario.Perfil.FORMADOR
        )
        self.client.force_login(usuario)

        self.assertEqual(self.client.get(URL).status_code, 403)
        self.assertEqual(self.client.post(URL, {}).status_code, 403)

    def test_anonimo_vai_para_o_login(self):
        self.client.logout()

        self.assertEqual(self.client.get(URL).status_code, 302)
        self.assertEqual(self.client.post(URL, {"data": "2027-03-06"}).status_code, 302)
        self.assertFalse(Formacao.objects.exists())
