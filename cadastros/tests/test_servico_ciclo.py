from datetime import date
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from cadastros import services
from cadastros.models import Ciclo
from cadastros.repositories import PeriodoOcupado

INICIO = date(2026, 2, 1)
FIM = date(2026, 12, 15)


# SimpleTestCase proíbe consultas ao banco: se o serviço consultar, o teste falha (NFM001).
# O repositório é trocado por um dublê (mock), que só registra a chamada.
@mock.patch("cadastros.services.repositories.salvar_ciclo", side_effect=lambda ciclo: ciclo)
class AbrirCicloTests(SimpleTestCase):
    def test_salva_ciclo_valido(self, salvar):
        ciclo = services.abrir_ciclo("Perseverança 2026", INICIO, FIM)
        salvar.assert_called_once_with(ciclo)
        self.assertEqual((ciclo.nome, ciclo.inicio, ciclo.fim), ("Perseverança 2026", INICIO, FIM))

    def test_tira_espacos_do_nome(self, salvar):
        ciclo = services.abrir_ciclo("  Perseverança 2026  ", INICIO, FIM)
        self.assertEqual(ciclo.nome, "Perseverança 2026")

    # CA001: nome, início e fim são obrigatórios

    def test_recusa_nome_vazio(self, salvar):
        for nome in ("", "   ", None):
            with self.subTest(nome=nome), self.assertRaises(ValidationError) as erro:
                services.abrir_ciclo(nome, INICIO, FIM)
            self.assertIn("nome", erro.exception.message_dict)
        salvar.assert_not_called()

    def test_recusa_datas_vazias(self, salvar):
        with self.assertRaises(ValidationError) as erro:
            services.abrir_ciclo("2026", None, None)
        self.assertEqual(set(erro.exception.message_dict), {"inicio", "fim"})
        salvar.assert_not_called()

    def test_recusa_fim_antes_do_inicio(self, salvar):
        with self.assertRaises(ValidationError) as erro:
            services.abrir_ciclo("2026", FIM, INICIO)
        self.assertEqual(erro.exception.message_dict, {"fim": ["O fim do ciclo deve ser depois do início."]})
        salvar.assert_not_called()

    # RN002: a recusa do banco vira mensagem (CA001: "mensagem explicativa")

    def test_traduz_sobreposicao_em_mensagem(self, salvar):
        salvar.side_effect = PeriodoOcupado
        with self.assertRaises(ValidationError) as erro:
            services.abrir_ciclo("2026", INICIO, FIM)
        self.assertEqual(erro.exception.messages, ["Já existe um ciclo nesse período."])


@mock.patch("cadastros.services.repositories.salvar_ciclo", side_effect=lambda ciclo: ciclo)
@mock.patch("cadastros.services.repositories.buscar_ciclo")
class EncerrarCicloTests(SimpleTestCase):
    def test_encerra_ciclo_aberto(self, buscar, salvar):
        buscar.return_value = Ciclo(pk=1, nome="2026", inicio=INICIO, fim=FIM)
        ciclo = services.encerrar_ciclo(1)
        buscar.assert_called_once_with(1)
        salvar.assert_called_once_with(ciclo)
        self.assertEqual(ciclo.situacao, Ciclo.Situacao.ENCERRADO)

    def test_recusa_ciclo_ja_encerrado(self, buscar, salvar):
        buscar.return_value = Ciclo(pk=1, nome="2026", inicio=INICIO, fim=FIM, situacao=Ciclo.Situacao.ENCERRADO)
        with self.assertRaises(ValidationError) as erro:
            services.encerrar_ciclo(1)
        self.assertEqual(erro.exception.messages, ["O ciclo “2026” já está encerrado."])
        salvar.assert_not_called()

    def test_ciclo_inexistente_propaga_does_not_exist(self, buscar, salvar):
        buscar.side_effect = Ciclo.DoesNotExist
        with self.assertRaises(Ciclo.DoesNotExist):
            services.encerrar_ciclo(1)
        salvar.assert_not_called()


@mock.patch("cadastros.services.repositories.salvar_ciclo", side_effect=lambda ciclo: ciclo)
@mock.patch("cadastros.services.repositories.buscar_ciclo")
class EditarCicloTests(SimpleTestCase):
    NOVO_INICIO = date(2026, 3, 1)

    def ciclo(self, situacao=Ciclo.Situacao.ABERTO):
        return Ciclo(pk=1, nome="2026", inicio=INICIO, fim=FIM, situacao=situacao)

    def test_altera_nome_e_datas_de_ciclo_aberto(self, buscar, salvar):
        buscar.return_value = self.ciclo()
        ciclo = services.editar_ciclo(1, "  Perseverança 2026  ", self.NOVO_INICIO, FIM)
        salvar.assert_called_once_with(ciclo)
        self.assertEqual((ciclo.nome, ciclo.inicio), ("Perseverança 2026", self.NOVO_INICIO))

    def test_ciclo_encerrado_aceita_mudar_so_o_nome(self, buscar, salvar):
        buscar.return_value = self.ciclo(Ciclo.Situacao.ENCERRADO)
        ciclo = services.editar_ciclo(1, "Perseverança 2026", INICIO, FIM)
        self.assertEqual(ciclo.nome, "Perseverança 2026")
        salvar.assert_called_once()

    def test_ciclo_encerrado_recusa_mudar_datas(self, buscar, salvar):
        buscar.return_value = self.ciclo(Ciclo.Situacao.ENCERRADO)
        with self.assertRaises(ValidationError) as erro:
            services.editar_ciclo(1, "2026", self.NOVO_INICIO, FIM)
        self.assertEqual(erro.exception.messages, ["Ciclo encerrado: as datas não podem ser alteradas."])
        salvar.assert_not_called()

    def test_recusa_fim_antes_do_inicio(self, buscar, salvar):
        buscar.return_value = self.ciclo()
        with self.assertRaises(ValidationError) as erro:
            services.editar_ciclo(1, "2026", FIM, INICIO)
        self.assertIn("fim", erro.exception.message_dict)
        salvar.assert_not_called()

    def test_traduz_sobreposicao_em_mensagem(self, buscar, salvar):
        buscar.return_value = self.ciclo()
        salvar.side_effect = PeriodoOcupado
        with self.assertRaises(ValidationError) as erro:
            services.editar_ciclo(1, "2026", self.NOVO_INICIO, FIM)
        self.assertEqual(erro.exception.messages, ["Já existe um ciclo nesse período."])

    def test_ciclo_inexistente_propaga_does_not_exist(self, buscar, salvar):
        buscar.side_effect = Ciclo.DoesNotExist
        with self.assertRaises(Ciclo.DoesNotExist):
            services.editar_ciclo(1, "2026", INICIO, FIM)
        salvar.assert_not_called()
