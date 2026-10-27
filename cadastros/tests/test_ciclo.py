from datetime import date, timedelta
from unittest import mock

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from cadastros.models import Ciclo


class CicloTests(TestCase):
    def setUp(self):
        self.ciclo = Ciclo.objects.create(
            nome="Perseverança 2026", inicio=date(2026, 2, 1), fim=date(2026, 12, 15)
        )

    def criar(self, inicio, fim):
        return Ciclo.objects.create(nome="Outro ciclo", inicio=inicio, fim=fim)

    # RN008: campos de auditoria herdados da RegistroBase (T002.1)

    def test_preenche_criado_em_e_atualizado_em(self):
        self.assertIsNotNone(self.ciclo.criado_em)
        self.assertIsNotNone(self.ciclo.atualizado_em)

    def test_salvar_de_novo_muda_atualizado_em_e_mantem_criado_em(self):
        criado_em = self.ciclo.criado_em
        depois = criado_em + timedelta(hours=1)
        # Fixa o relógio para o teste não depender de quanto tempo passou entre os dois save().
        with mock.patch("django.utils.timezone.now", return_value=depois):
            self.ciclo.nome = "Perseverança 2026 (turma A)"
            self.ciclo.save()
        self.ciclo.refresh_from_db()
        self.assertEqual(self.ciclo.criado_em, criado_em)
        self.assertEqual(self.ciclo.atualizado_em, depois)

    # Restrições no banco (T002.2). O atomic() isola o erro para o teste continuar usando o banco.

    def test_banco_recusa_fim_antes_do_inicio(self):
        with self.assertRaisesMessage(IntegrityError, "ciclo_fim_depois_inicio"), transaction.atomic():
            self.criar(date(2027, 12, 1), date(2027, 2, 1))

    def test_banco_recusa_fim_igual_ao_inicio(self):
        with self.assertRaisesMessage(IntegrityError, "ciclo_fim_depois_inicio"), transaction.atomic():
            self.criar(date(2027, 2, 1), date(2027, 2, 1))

    def test_banco_recusa_ciclo_sobreposto(self):
        with self.assertRaisesMessage(IntegrityError, "ciclo_sem_sobreposicao"), transaction.atomic():
            self.criar(date(2026, 11, 1), date(2027, 3, 1))

    def test_banco_recusa_ciclo_que_comeca_no_dia_em_que_outro_termina(self):
        with self.assertRaisesMessage(IntegrityError, "ciclo_sem_sobreposicao"), transaction.atomic():
            self.criar(date(2026, 12, 15), date(2027, 12, 1))

    def test_aceita_ciclo_que_comeca_no_dia_seguinte(self):
        self.criar(date(2026, 12, 16), date(2027, 12, 15))
        self.assertEqual(Ciclo.objects.count(), 2)

    def test_editar_um_ciclo_nao_conflita_com_ele_mesmo(self):
        self.ciclo.fim = date(2026, 12, 20)
        self.ciclo.full_clean()
        self.ciclo.save()
        self.ciclo.refresh_from_db()
        self.assertEqual(self.ciclo.fim, date(2026, 12, 20))

    def test_banco_recusa_editar_ciclo_para_sobrepor_outro(self):
        outro = self.criar(date(2027, 2, 1), date(2027, 12, 15))
        outro.inicio = date(2026, 12, 1)
        with self.assertRaisesMessage(IntegrityError, "ciclo_sem_sobreposicao"), transaction.atomic():
            outro.save()

    # Situação do ciclo (T002.7)

    def test_ciclo_nasce_aberto(self):
        self.assertEqual(self.ciclo.situacao, Ciclo.Situacao.ABERTO)

    def test_banco_recusa_situacao_fora_da_lista(self):
        with self.assertRaisesMessage(IntegrityError, "ciclo_situacao_valida"), transaction.atomic():
            Ciclo.objects.filter(pk=self.ciclo.pk).update(situacao="pausado")

    # Validação do Django (full_clean), a mesma que os formulários e o admin usam

    def test_validacao_aponta_fim_antes_do_inicio_sem_quebrar(self):
        ciclo = Ciclo(nome="Invertido", inicio=date(2027, 12, 1), fim=date(2027, 2, 1))
        with self.assertRaises(ValidationError) as erro:
            ciclo.full_clean()
        self.assertEqual(erro.exception.message_dict, {"fim": ["O fim do ciclo deve ser depois do início."]})

    def test_validacao_aponta_fim_igual_ao_inicio(self):
        ciclo = Ciclo(nome="Um dia só", inicio=date(2027, 2, 1), fim=date(2027, 2, 1))
        with self.assertRaises(ValidationError) as erro:
            ciclo.full_clean()
        self.assertEqual(erro.exception.message_dict, {"fim": ["O fim do ciclo deve ser depois do início."]})

    def test_validacao_avisa_sobreposicao(self):
        ciclo = Ciclo(nome="Sobreposto", inicio=date(2026, 11, 1), fim=date(2027, 3, 1))
        with self.assertRaises(ValidationError) as erro:
            ciclo.full_clean()
        self.assertEqual(erro.exception.messages, ["Já existe um ciclo nesse período."])
