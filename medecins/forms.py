from django import forms
from lobiko.models import Medecin

LANGUE_CHOICES = [
    ('fr', 'Français'),
    ('en', 'Anglais'),
    ('sw', 'Swahili'),
    ('ln', 'Lingala'),
    ('kg', 'Kikongo'),
]

class MedecinLoginForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur", max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': "Nom d'utilisateur"
    }))
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Mot de passe'
    }))

class MedecinInscriptionForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirmez le mot de passe")

    date_naissance = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Date de naissance"
    )

    langues = forms.MultipleChoiceField(
        choices=LANGUE_CHOICES,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control select2',
            'multiple': 'multiple'
        }),
        label="Langues parlées",
        required=False
    )

    class Meta:
        model = Medecin
        fields = [
            'username', 'password', 'confirm_password',
            'nom', 'postnom', 'prenom', 'sexe',
            'date_naissance', 'etat_civil', 'telephone',
            'commune', 'quartier', 'avenue', 'cnom', 'langues', 'specialite'
        ]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if password and confirm and password != confirm:
            self.add_error('confirm_password', "Les mots de passe ne correspondent pas.")

        return cleaned_data

    def save(self, commit=True):
        medecin = super().save(commit=False)
        medecin.set_password(self.cleaned_data["password"])
        # Convertir en liste JSON (utile si l'utilisateur n’a rien sélectionné)
        medecin.langues = self.cleaned_data.get('langues', [])
        if commit:
            medecin.save()
        return medecin

class MessageForm(forms.Form):
    message = forms.CharField(
        label="Message",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': "Écrivez votre message ici..."
        }),
        required=True
    )
