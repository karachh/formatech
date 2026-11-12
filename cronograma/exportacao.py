class ExportadorBase:
    """Template Method: o esqueleto é fixo, as subclasses definem os passos."""

    def exportar(self, titulo, formacoes):
        partes = [self.cabecalho(titulo)]
        partes += [self.linha(formacao) for formacao in formacoes]
        partes.append(self.rodape(formacoes))
        return "\n".join(partes)

    def cabecalho(self, titulo):
        raise NotImplementedError

    def linha(self, formacao):
        raise NotImplementedError

    def rodape(self, formacoes):
        return ""


class ExportadorTexto(ExportadorBase):
    """Texto simples para colar no grupo de mensagens."""

    def cabecalho(self, titulo):
        return f"Cronograma de {titulo}\n"

    def linha(self, formacao):
        tema = formacao.tema.nome if formacao.tema else "Sem tema"
        formador = formacao.formador.nome if formacao.formador else "a definir"
        return f"{formacao.data:%d/%m} - {tema} - {formador}"