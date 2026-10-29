from django.contrib.auth import authenticate


def autenticar_usuario(username, senha):
    """Devolve o Usuario se as credenciais forem válidas; senão, None."""
    return authenticate(username=username, password=senha)