from datetime import date

from django.test import TestCase

from cadastros import repositories
from cadastros.models import Ciclo, Formador


class ConsultasParaCronogramaTests(TestCase):
    def test_ciclo_da_data_inclui_o_primeiro_e_o_ultimo_dia(self):
        ciclo = Ciclo.objects.create(nome="2027", inicio=date(2027, 2, 1), fim=date(2027, 12, 15))

        for data in (date(2027, 2, 1), date(2027, 7, 1), date(2027, 12, 15)):
            with self.subTest(data=data):
                self.assertEqual(repositories.buscar_ciclo_da_data(data), ciclo)
        self.assertIsNone(repositories.buscar_ciclo_da_data(date(2027, 1, 31)))
        self.assertIsNone(repositories.buscar_ciclo_da_data(date(2027, 12, 16)))

    def test_lista_so_formadores_ativos(self):
        ana = Formador.objects.create(nome="Ana", inicio_servico=date(2020, 1, 10), capacitado=True)
        Formador.objects.create(
            nome="Bruno", inicio_servico=date(2020, 1, 10), capacitado=True, ativo=False
        )

        self.assertEqual(repositories.listar_formadores_ativos(), [ana])
