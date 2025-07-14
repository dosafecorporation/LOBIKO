from django import forms
from lobiko.models import Medecin, Choices
from django.contrib.auth.password_validation import validate_password

class MedecinLoginForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur", max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': "Nom d'utilisateur"
    }))
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Mot de passe'
    }))

class MedecinInscriptionForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum 8 caractères',
            'autocomplete': 'new-password'
        }),
        label="Mot de passe",
        help_text="Le mot de passe doit contenir au moins 8 caractères.",
        validators=[validate_password]
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Retapez votre mot de passe',
            'autocomplete': 'new-password'
        }),
        label="Confirmation du mot de passe"
    )

    date_naissance = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
                'max': '2100-01-01'  # Empêche des dates trop dans le futur
            },
            format='%Y-%m-%d'
        ),
        label="Date de naissance"
    )

    telephone = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+243XXXXXXXXX'
        }),
        help_text="Format: +243 suivi de 9 chiffres"
    )

    langues = forms.MultipleChoiceField(
        choices=Choices.LANGUES,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control select2',
            'multiple': 'multiple',
            'data-placeholder': 'Sélectionnez les langues parlées...'
        }),
        label="Langues parlées",
        required=False,
        help_text="Maintenez Ctrl/Cmd pour sélectionner plusieurs langues"
    )

    class Meta:
        model = Medecin
        fields = [
            'username', 'password', 'confirm_password',
            'nom', 'postnom', 'prenom', 'sexe',
            'date_naissance', 'etat_civil', 'telephone',
            'commune', 'quartier', 'avenue', 'cnom', 'langues', 'specialite'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom d\'utilisateur unique'
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre nom de famille'
            }),
            'postnom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre postnom'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre prénom'
            }),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'etat_civil': forms.Select(attrs={'class': 'form-control'}),
            'commune': forms.Select(attrs={'class': 'form-control'}),
            'quartier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quartier de résidence'
            }),
            'avenue': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Avenue/Rue'
            }),
            'cnom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre numéro d\'enregistrement CNOM'
            }),
            'specialite': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'cnom': "Numéro CNOM",
            'specialite': "Spécialité médicale"
        }
        help_texts = {
            'username': "Ce sera votre identifiant de connexion",
            'cnom': "Numéro d'enregistrement au Conseil National de l'Ordre des Médecins"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialiser les langues si instance existante
        if self.instance and self.instance.langues:
            self.initial['langues'] = self.instance.langues

    def clean(self):
        cleaned_data = super().clean()
        
        # Validation des mots de passe
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Les mots de passe ne correspondent pas.")
        
        # Validation du téléphone
        telephone = cleaned_data.get("telephone")
        if telephone and Medecin.objects.filter(telephone=telephone).exists():
            if not self.instance or self.instance.telephone != telephone:
                self.add_error('telephone', "Ce numéro de téléphone est déjà utilisé.")
        
        return cleaned_data

    def save(self, commit=True):
        medecin = super().save(commit=False)
        
        # Hashage du mot de passe
        medecin.set_password(self.cleaned_data["password"])
        
        # Conversion des langues en format JSON
        langues = self.cleaned_data.get('langues', [])
        medecin.langues = langues if langues else None  # Stocke None si liste vide
        
        if commit:
            medecin.save()
            self.save_m2m()  # Important pour les relations many-to-many si ajoutées plus tard
        
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
