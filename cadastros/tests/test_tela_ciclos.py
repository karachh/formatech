from datetime import date

from django.test import TestCase
from django.urls import reverse

from cadastros.models import Ciclo

URL = reverse("cadastros:ciclos")


class TelaCiclosTests(TestCase):
    def postar(self, nome="Perseverança 2027", inicio="2027-02-01", fim="2027-12-15"):
        return self.client.post(URL, {"nome": nome, "inicio": inicio, "fim": fim}, follow=True)

    def test_lista_vazia(self):
        self.assertContains(self.client.get(URL), "Nenhum ciclo cadastrado.")

    # Critério 1 da US002: o ciclo cadastrado aparece na lista

    def test_cadastrar_mostra_o_ciclo_na_lista(self):
        resposta = self.postar()
        self.assertRedirects(resposta, URL)
        self.assertContains(resposta, "Ciclo “Perseverança 2027” cadastrado.")
        self.assertContains(resposta, "<td>Perseverança 2027</td><td>01/02/2027</td><td>15/12/2027</td>", html=True)

    # Critério 2: ciclo sobreposto mostra erro e não salva

    def test_ciclo_sobreposto_mostra_erro_e_nao_salva(self):
        Ciclo.objects.create(nome="2027", inicio=date(2027, 1, 1), fim=date(2027, 12, 31))
        resposta = self.postar(nome="Sobreposto")
        self.assertContains(resposta, "Já existe um ciclo nesse período.")
        self.assertEqual(Ciclo.objects.count(), 1)

    def test_fim_antes_do_inicio_mostra_erro_no_campo(self):
        resposta = self.postar(inicio="2027-12-15", fim="2027-02-01")
        self.assertFormError(resposta.context["form"], "fim", "O fim do ciclo deve ser depois do início.")
        self.assertFalse(Ciclo.objects.exists())

    def test_nome_so_com_espacos_mostra_erro(self):
        resposta = self.postar(nome="   ")
        self.assertTrue(resposta.context["form"].errors["nome"])
        self.assertFalse(Ciclo.objects.exists())
