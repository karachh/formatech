import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from cadastros import services

ARQUIVO = Path(__file__).resolve().parents[2] / "dados" / "temas.csv"


class Command(BaseCommand):
    help = "Carrega os temas da apostila a partir de cadastros/dados/temas.csv (não duplica)."

    def handle(self, *args, **opcoes):
        with open(ARQUIVO, encoding="utf-8", newline="") as arquivo:
            linhas = list(csv.DictReader(arquivo, delimiter=";"))
        criados = services.carregar_temas(linhas)
        self.stdout.write(self.style.SUCCESS(f"{criados} tema(s) criado(s)."))