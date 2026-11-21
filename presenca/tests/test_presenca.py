from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from acesso.models import Usuario
from cadastros.models import Ciclo, Perseverante, Tema
from cadastros.tests.test_tela_ciclos import ComoCoordenador
from cronograma.models import Formacao
from presenca import repositories, services
from presenca.models import Presenca


class ComTurma:
    """Uma formação num ciclo com três perseverantes ativos, um inativo e um de outro ciclo."""

    def setUp(self):
        super().setUp()
        self.ciclo = Ciclo.objects.create(nome="2027", inicio=date(2027, 2, 1), fim=date(2027, 12, 15))
        outro_ciclo = Ciclo.objects.create(nome="2028", inicio=date(2028, 2, 1), fim=date(2028, 12, 15))
        self.formacao = Formacao.objects.create(data=date(2027, 3, 6))
        self.ana, self.bia, self.caio = (
            Perseverante.objects.create(nome=nome, ciclo=self.ciclo) for nome in ("Ana", "Bia", "Caio")
        )
        self.inativo = Perseverante.objects.create(nome="Davi", ciclo=self.ciclo, ativo=False)
        self.de_fora = Perseverante.objects.create(nome="Eva", ciclo=outro_ciclo)
        self.url = reverse("presenca:lancar_presenca", args=[self.formacao.pk])

    def salvas(self):
        return repositories.situacoes_da_formacao(self.formacao.pk)


class ModeloPresencaTests(ComTurma, TestCase):
    def test_banco_recusa_duas_linhas_do_mesmo_perseverante_na_formacao(self):
        Presenca.objects.create(formacao=self.formacao, perseverante=self.ana, situacao="presente")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Presenca.objects.create(formacao=self.formacao, perseverante=self.ana, situacao="ausente")

    def test_banco_recusa_situacao_invalida(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Presenca.objects.create(formacao=self.formacao, perseverante=self.ana, situacao="faltou")

    def test_excluir_perseverante_apaga_as_presencas_dele(self):
        # NFC002: exclusão a pedido do titular.
        Presenca.objects.create(formacao=self.formacao, perseverante=self.ana, situacao="presente")
        self.ana.delete()
        self.assertFalse(Presenca.objects.exists())


class GravacaoEmLoteTests(ComTurma, TestCase):
    def test_grava_uma_linha_por_perseverante(self):
        repositories.salvar_presencas(
            self.formacao.pk, {self.ana.pk: "presente", self.bia.pk: "ausente", self.caio.pk: "justificado"}
        )
        self.assertEqual(Presenca.objects.count(), 3)
        self.assertEqual(self.salvas(), {self.ana.pk: "presente", self.bia.pk: "ausente", self.caio.pk: "justificado"})

    def test_regravar_corrige_sem_duplicar(self):
        repositories.salvar_presencas(self.formacao.pk, {self.ana.pk: "presente", self.bia.pk: "presente"})
        repositories.salvar_presencas(self.formacao.pk, {self.ana.pk: "ausente", self.bia.pk: "presente"})
        self.assertEqual(Presenca.objects.count(), 2)
        self.assertEqual(self.salvas(), {self.ana.pk: "ausente", self.bia.pk: "presente"})

    def test_falha_numa_linha_nao_grava_nenhuma(self):
        # NFR001: Ana seria gravada antes de Bia falhar; o atomic() desfaz Ana também.
        with self.assertRaises(IntegrityError):
            repositories.salvar_presencas(
                self.formacao.pk, {self.ana.pk: "presente", self.bia.pk: "faltou", self.caio.pk: "presente"}
            )
        self.assertFalse(Presenca.objects.exists())

    def test_falha_na_correcao_mantem_o_que_estava_salvo(self):
        repositories.salvar_presencas(self.formacao.pk, {self.ana.pk: "presente", self.bia.pk: "presente"})
        with self.assertRaises(IntegrityError):
            repositories.salvar_presencas(self.formacao.pk, {self.ana.pk: "ausente", self.bia.pk: "faltou"})
        self.assertEqual(self.salvas(), {self.ana.pk: "presente", self.bia.pk: "presente"})


class ServicoPresencaTests(ComTurma, TestCase):
    def test_grade_tem_so_os_ativos_do_ciclo_marcados_presente(self):
        self.assertEqual(
            services.grade_de_presenca(self.formacao),
            [(self.ana, "presente"), (self.bia, "presente"), (self.caio, "presente")],
        )

    def test_grade_reaberta_traz_as_marcacoes_salvas(self):
        repositories.salvar_presencas(self.formacao.pk, {self.bia.pk: "ausente"})
        self.assertEqual(
            services.grade_de_presenca(self.formacao),
            [(self.ana, "presente"), (self.bia, "ausente"), (self.caio, "presente")],
        )

    def test_formacao_sem_ciclo_e_recusada(self):
        sem_ciclo = Formacao.objects.create(data=date(2027, 12, 30))
        with self.assertRaises(ValidationError):
            services.grade_de_presenca(sem_ciclo)

    def test_recusa_perseverante_fora_da_grade_sem_gravar(self):
        for de_fora in (self.inativo, self.de_fora):
            with self.assertRaises(ValidationError):
                services.lancar_presencas(self.formacao.pk, {self.ana.pk: "presente", de_fora.pk: "presente"})
        self.assertFalse(Presenca.objects.exists())

    def test_recusa_situacao_invalida_sem_gravar(self):
        with self.assertRaises(ValidationError):
            services.lancar_presencas(self.formacao.pk, {self.ana.pk: "presente", self.bia.pk: "faltou"})
        self.assertFalse(Presenca.objects.exists())


class TelaPresencaTests(ComoCoordenador, ComTurma, TestCase):
    def postar(self, **situacoes):
        dados = {f"perseverante_{p.pk}": "presente" for p in (self.ana, self.bia, self.caio)}
        dados.update(situacoes)
        return self.client.post(self.url, dados, follow=True)

    def marcadas(self, resposta):
        """{perseverante_id: situacao} que a tela mostra marcada."""
        form = resposta.context["form"]
        return {int(campo.name.removeprefix("perseverante_")): campo.value() for campo in form}

    def test_lista_os_ativos_do_ciclo_com_presente_marcado(self):
        resposta = self.client.get(self.url)
        for nome in ("Ana", "Bia", "Caio"):
            self.assertContains(resposta, nome)
        self.assertNotContains(resposta, "Davi")
        self.assertNotContains(resposta, "Eva")
        self.assertEqual(self.marcadas(resposta), {self.ana.pk: "presente", self.bia.pk: "presente", self.caio.pk: "presente"})

    def test_confirmar_grava_o_encontro_inteiro(self):
        resposta = self.postar(**{f"perseverante_{self.bia.pk}": "ausente"})
        self.assertContains(resposta, "Presença da formação de 06/03/2027 gravada.")
        self.assertEqual(self.salvas(), {self.ana.pk: "presente", self.bia.pk: "ausente", self.caio.pk: "presente"})

    def test_reabrir_mostra_o_salvo_e_permite_corrigir(self):
        self.postar(**{f"perseverante_{self.bia.pk}": "ausente"})
        resposta = self.client.get(self.url)
        self.assertEqual(self.marcadas(resposta)[self.bia.pk], "ausente")

        self.postar(**{f"perseverante_{self.bia.pk}": "justificado"})
        self.assertEqual(self.salvas()[self.bia.pk], "justificado")
        self.assertEqual(Presenca.objects.count(), 3)

    def test_situacao_invalida_mostra_erro_e_nao_grava(self):
        resposta = self.postar(**{f"perseverante_{self.bia.pk}": "faltou"})
        self.assertContains(resposta, "Faça uma escolha válida")
        self.assertFalse(Presenca.objects.exists())

    def test_cronograma_oferece_o_link_de_presenca(self):
        resposta = self.client.get(reverse("cronograma:cronograma"), {"ciclo": self.ciclo.pk})
        self.assertContains(resposta, self.url)

    def test_formacao_inexistente_da_404(self):
        self.assertEqual(self.client.get(reverse("presenca:lancar_presenca", args=[999])).status_code, 404)

    def test_formador_recebe_403(self):
        formador = Usuario.objects.create_user(username="form", password="x", perfil=Usuario.Perfil.FORMADOR)
        self.client.force_login(formador)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_anonimo_vai_para_o_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)


class PresencaEmEncontroSemTemaTests(ComoCoordenador, ComTurma, TestCase):
    """US017 (T017.2): encontro sem tema da apostila também recebe presença."""

    def gravar(self):
        dados = {f"perseverante_{p.pk}": "presente" for p in (self.ana, self.bia, self.caio)}
        dados[f"perseverante_{self.bia.pk}"] = "ausente"
        return self.client.post(self.url, dados, follow=True)

    def test_encontro_sem_tema_identificado_pela_descricao(self):
        self.formacao.descricao = "Oração"
        self.formacao.save()

        self.assertContains(self.client.get(self.url), "06/03/2027 · Oração")
        self.gravar()
        self.assertEqual(self.salvas(), {self.ana.pk: "presente", self.bia.pk: "ausente", self.caio.pk: "presente"})

    def test_encontro_com_tema_opcional(self):
        self.formacao.tema = Tema.objects.create(nome="Retiro de Carnaval", tipo=Tema.Tipo.OPCIONAL)
        self.formacao.save()

        self.assertContains(self.client.get(self.url), "06/03/2027 · Retiro de Carnaval")
        self.gravar()
        self.assertEqual(Presenca.objects.count(), 3)
