from datetime import date

from django.db import IntegrityError
from django.test import TestCase

from cadastros import repositories
from cadastros.models import Ciclo


class RepositorioCicloTests(TestCase):
    def test_lista_do_ciclo_mais_recente_para_o_mais_antigo(self):
        antigo = Ciclo.objects.create(nome="2025", inicio=date(2025, 2, 1), fim=date(2025, 12, 15))
        recente = Ciclo.objects.create(nome="2026", inicio=date(2026, 2, 1), fim=date(2026, 12, 15))
        self.assertEqual(repositories.listar_ciclos(), [recente, antigo])

    def test_salva_e_devolve_o_ciclo(self):
        ciclo = repositories.salvar_ciclo(Ciclo(nome="2026", inicio=date(2026, 2, 1), fim=date(2026, 12, 15)))
        self.assertIsNotNone(ciclo.pk)

    def test_sobreposicao_vira_periodo_ocupado(self):
        Ciclo.objects.create(nome="2026", inicio=date(2026, 2, 1), fim=date(2026, 12, 15))
        with self.assertRaises(repositories.PeriodoOcupado):
            repositories.salvar_ciclo(Ciclo(nome="Outro", inicio=date(2026, 11, 1), fim=date(2027, 3, 1)))
        # O atomic() do repositório deixou a transação do teste utilizável.
        self.assertEqual(Ciclo.objects.count(), 1)

    def test_outras_recusas_do_banco_continuam_integrity_error(self):
        with self.assertRaisesMessage(IntegrityError, "ciclo_fim_depois_inicio"):
            repositories.salvar_ciclo(Ciclo(nome="Invertido", inicio=date(2027, 12, 1), fim=date(2027, 2, 1)))
