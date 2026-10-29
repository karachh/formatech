from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from acesso.models import Usuario
from cadastros import services
from cadastros.models import Tema
from cadastros.tests.test_tela_ciclos import ComoCoordenador

URL = reverse("cadastros:temas")


class ServicoTemasTests(TestCase):
    def test_cadastra_tema_de_apostila_com_rotulo(self):
        tema = services.cadastrar_tema("  Kerigma  ", "apostila", "1")
        self.assertEqual((tema.nome, tema.tipo, tema.rotulo), ("Kerigma", "apostila", "1"))

    def test_cadastra_tema_opcional_sem_rotulo(self):
        tema = services.cadastrar_tema("Convidado", "opcional")
        self.assertEqual((tema.tipo, tema.rotulo), ("opcional", ""))

    def test_tipo_invalido_e_recusado(self):
        with self.assertRaises(ValidationError):
            services.cadastrar_tema("X", "inexistente")

    def test_nome_repetido_e_recusado(self):
        services.cadastrar_tema("Kerigma", "apostila")
        with self.assertRaises(ValidationError) as erro:
            services.cadastrar_tema("Kerigma", "opcional")
        self.assertIn("Já existe um tema com esse nome.", erro.exception.messages)

    def test_editar_altera_a_classificacao(self):
        tema = services.cadastrar_tema("Kerigma", "apostila", "1")
        services.editar_tema(tema.pk, "Kerigma", "opcional", "")
        tema.refresh_from_db()
        self.assertEqual(tema.tipo, "opcional")

    def test_carga_nao_duplica(self):
        linhas = [{"nome": "A", "tipo": "apostila", "rotulo": "1"}, {"nome": "B", "tipo": "opcional", "rotulo": ""}]
        self.assertEqual(services.carregar_temas(linhas), 2)
        self.assertEqual(services.carregar_temas(linhas), 0)
        self.assertEqual(Tema.objects.count(), 2)


class TelaTemasTests(ComoCoordenador, TestCase):
    def postar(self, nome="Kerigma", tipo="apostila", rotulo="1"):
        return self.client.post(URL, {"nome": nome, "tipo": tipo, "rotulo": rotulo}, follow=True)

    def test_lista_vazia(self):
        self.assertContains(self.client.get(URL), "Nenhum tema cadastrado.")

    # Critério da US005: o tema cadastrado com a classificação aparece na lista

    def test_cadastrar_mostra_o_tema_na_lista(self):
        resposta = self.postar()
        self.assertRedirects(resposta, URL)
        self.assertContains(resposta, "Tema “Kerigma” cadastrado.")
        self.assertContains(resposta, "<td>Kerigma</td><td>Apostila</td><td>1</td>", html=True)

    def test_tema_opcional_aparece_como_opcional(self):
        resposta = self.postar(nome="Convidado", tipo="opcional", rotulo="")
        self.assertContains(resposta, "<td>Opcional</td>", html=True)

    def test_nome_repetido_mostra_erro(self):
        self.postar()
        resposta = self.postar()
        self.assertContains(resposta, "Já existe um tema com esse nome.")
        self.assertEqual(Tema.objects.count(), 1)

    def test_editar_salva_e_volta_para_a_lista(self):
        tema = services.cadastrar_tema("Kerigma", "apostila", "1")
        url = reverse("cadastros:editar_tema", args=[tema.pk])
        resposta = self.client.post(url, {"nome": "Kerigma", "tipo": "opcional", "rotulo": ""}, follow=True)
        self.assertRedirects(resposta, URL)
        tema.refresh_from_db()
        self.assertEqual(tema.tipo, "opcional")

    def test_tema_inexistente_da_404(self):
        self.assertEqual(self.client.get(reverse("cadastros:editar_tema", args=[999_999])).status_code, 404)


class PermissaoTemasTests(TestCase):
    def test_anonimo_vai_para_o_login(self):
        self.assertEqual(self.client.get(URL).status_code, 302)

    def test_formador_recebe_403(self):
        formador = Usuario.objects.create_user(username="form", password="x", perfil=Usuario.Perfil.FORMADOR)
        self.client.force_login(formador)
        self.assertEqual(self.client.get(URL).status_code, 403)