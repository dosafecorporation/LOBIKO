from django.db import models
from django.contrib.auth.models import User

class Patient(models.Model):
    whatsapp_id = models.CharField(max_length=100, unique=True)
    nom = models.CharField(max_length=100)
    postnom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    SEXE_CHOICES = [('Homme', 'Homme'), ('Femme', 'Femme')]
    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES)
    date_naissance = models.DateField()
    etat_civil = models.CharField(max_length=50)
    telephone = models.CharField(max_length=20, unique=True)
    adresse = models.TextField()
    LANGUE_CHOICES = [
        ('Français', 'Français'),
        ('Anglais', 'Anglais'),
        ('Lingala', 'Lingala'),
        ('Swahili', 'Swahili'),
        ('Kikongo', 'Kikongo'),
        ('Tshiluba', 'Tshiluba')
    ]
    langue_preferee = models.CharField(max_length=50, choices=LANGUE_CHOICES)

class Assureur(models.Model):
    nom = models.CharField(max_length=100)
    contact = models.CharField(max_length=100)

class Assurance(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    assureur = models.ForeignKey(Assureur, on_delete=models.CASCADE)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)

class Medecin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    postnom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    SEXE_CHOICES = [('Homme', 'Homme'), ('Femme', 'Femme')]
    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES)
    date_naissance = models.DateField()
    etat_civil = models.CharField(max_length=50)
    telephone = models.CharField(max_length=20, unique=True)
    adresse = models.TextField()
    cnom = models.CharField(max_length=100)  # numéro d'enregistrement CNOM
    langues = models.CharField(max_length=200)
    specialite = models.CharField(max_length=100)  # ou 'Généraliste'

class SessionDiscussion(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.SET_NULL, null=True, blank=True)
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)

class Message(models.Model):
    session = models.ForeignKey(SessionDiscussion, on_delete=models.CASCADE)
    emetteur = models.CharField(max_length=20)  # "patient", "bot", "medecin"
    contenu = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)