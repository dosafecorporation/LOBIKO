from django import forms

class LoginForm(forms.Form):
    telephone = forms.CharField(label="Téléphone", max_length=20)
