from django import forms


class LoginForm(forms.Form):
    """Só converte o que veio da tela. Quem valida a regra é o services."""

    username = forms.CharField(label="Usuário", max_length=150)
    senha = forms.CharField(widget=forms.PasswordInput)