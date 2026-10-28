from django.test import TestCase
from django.urls import reverse

from acesso.models import Usuario

SENHA = "senha-teste-123"


class AutenticacaoTests(TestCase):
    def setUp(self):
        self.coordenador = Usuario.objects.create_user(
            username="coord", password=SENHA, perfil=Usuario.Perfil.COORDENADOR
        )
        self.formador = Usuario.objects.create_user(
            username="form", password=SENHA, perfil=Usuario.Perfil.FORMADOR
        )



    def test_anonimo_na_home_vai_para_o_login(self):
        home = reverse("acesso:home")
        resposta = self.client.get(home)
        self.assertRedirects(resposta, f"{reverse('acesso:login')}?next={home}")

    def test_anonimo_em_ciclos_vai_para_o_login(self):
        ciclos = reverse("cadastros:ciclos")
        resposta = self.client.get(ciclos)
        self.assertRedirects(resposta, f"{reverse('acesso:login')}?next={ciclos}")

    def test_tela_de_login_abre_sem_estar_logado(self):
        self.assertEqual(self.client.get(reverse("acesso:login")).status_code, 200)


    def test_login_valido_vai_para_a_home(self):
        resposta = self.client.post(
            reverse("acesso:login"), {"username": "coord", "senha": SENHA}
        )
        self.assertRedirects(resposta, reverse("acesso:home"))

    def test_login_com_senha_errada_mostra_erro(self):
        resposta = self.client.post(
            reverse("acesso:login"), {"username": "coord", "senha": "errada"}
        )
        self.assertContains(resposta, "Usuário ou senha inválidos.")

    def test_logout_encerra_a_sessao(self):
        self.client.force_login(self.coordenador)
        self.client.post(reverse("acesso:logout"))
        resposta = self.client.get(reverse("acesso:home"))
        self.assertEqual(resposta.status_code, 302)

    def test_menu_completo_para_coordenador(self):
        self.client.force_login(self.coordenador)
        resposta = self.client.get(reverse("acesso:home"))
        for item in ("Cronograma", "Ciclos", "Perseverantes", "Formadores", "Exportação"):
            self.assertContains(resposta, item)

    def test_menu_reduzido_para_formador(self):
        self.client.force_login(self.formador)
        resposta = self.client.get(reverse("acesso:home"))
        self.assertContains(resposta, "Cronograma")
        self.assertContains(resposta, "Temas que já ministrei")
        for item in ("Ciclos", "Perseverantes", "Formadores", "Exportação"):
            self.assertNotContains(resposta, item)


    def test_formador_recebe_403_em_ciclos(self):
        self.client.force_login(self.formador)
        resposta = self.client.get(reverse("cadastros:ciclos"))
        self.assertEqual(resposta.status_code, 403)

    def test_coordenador_abre_ciclos(self):
        self.client.force_login(self.coordenador)
        resposta = self.client.get(reverse("cadastros:ciclos"))
        self.assertEqual(resposta.status_code, 200)



    def test_senha_e_gravada_com_hash(self):
        self.assertNotEqual(self.coordenador.password, SENHA)
        self.assertTrue(self.coordenador.password.startswith("pbkdf2_"))
        self.assertTrue(self.coordenador.check_password(SENHA))