"""Avisos de qualidade da escala (US008, RN001).

Padrão Strategy: cada regra é uma classe com o mesmo método `verificar`, e o
serviço roda todas da lista REGRAS sem saber qual é qual. Para criar um aviso
novo, basta escrever outra classe e colocá-la em REGRAS.

RN001: aviso nunca bloqueia. As regras não lançam exceção nem consultam o
banco: recebem os dados prontos do serviço e só devolvem avisos.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Aviso:
    codigo: str
    mensagem: str


class RegraDeAviso:
    """Interface das regras. Cada regra tem um código próprio."""

    codigo = ""

    def verificar(self, formacao, formador, historico):
        """historico: formações realizadas pelo formador, da mais recente para a mais antiga.

        Devolve um Aviso, ou None quando a regra não se aplica.
        """
        raise NotImplementedError


class FormadorJaMinistrouTema(RegraDeAviso):
    codigo = "formador_ja_ministrou_tema"

    def verificar(self, formacao, formador, historico):
        if formacao.tema_id is None:
            return None
        for anterior in historico:
            if anterior.tema_id == formacao.tema_id:
                # O histórico vem do mais recente para o mais antigo: a primeira é a última vez.
                return Aviso(
                    self.codigo,
                    f"{formador.nome} já ministrou “{formacao.tema.nome}” em {anterior.data:%d/%m/%Y}.",
                )
        return None


REGRAS = [FormadorJaMinistrouTema()]


def codigos_de_aviso():
    """Lista exaustiva dos avisos possíveis (RN001)."""
    return [regra.codigo for regra in REGRAS]


def verificar_avisos(formacao, formador, historico):
    avisos = (regra.verificar(formacao, formador, historico) for regra in REGRAS)
    return [aviso for aviso in avisos if aviso is not None]
