from django.db import models
from django.contrib.auth.hashers import make_password, check_password

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
    COMMUNE_CHOICES = [
    ('Barumbu', 'Barumbu'),
    ('Bumbu', 'Bumbu'),
    ('Kalamu', 'Kalamu'),
    ('Kasa-Vubu', 'Kasa-Vubu'),
    ('Kinshasa', 'Kinshasa'),
    ('Kintambo', 'Kintambo'),
    ('Lingwala', 'Lingwala'),
    ('Gombe', 'Gombe'),
    ('Ngaliema', 'Ngaliema'),
    ('Mont Ngafula', 'Mont Ngafula'),
    ('Lemba', 'Lemba'),
    ('Ngaba', 'Ngaba'),
    ('Matete', 'Matete'),
    ('Kisenso', 'Kisenso'),
    ('Kimbanseke', 'Kimbanseke'),
    ('Nsele', 'Nsele'),
    ('Maluku', 'Maluku'),
    ('Masina', 'Masina'),
    ('Ndjili', 'Ndjili'),
    ('N’djili', 'N’djili'),
    ('Limete', 'Limete'),
    ('Selembao', 'Selembao'),
    ('Makala', 'Makala'),
    ('Kasavubu', 'Kasavubu'),
    ('Bandalungwa', 'Bandalungwa')]
    commune=models.CharField(max_length=100, choices=COMMUNE_CHOICES,null=True)
    quartier= models.CharField(max_length=100,null=True)
    avenue = models.CharField(max_length=100, null=True)
    
    langue_preferee = models.JSONField(null=True, blank=True, default=list)

class Assureur(models.Model):
    nom = models.CharField(max_length=100)
    contact = models.CharField(max_length=100)

class Assurance(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    assureur = models.ForeignKey(Assureur, on_delete=models.CASCADE)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)

class Medecin(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)  # mot de passe hashé
    nom = models.CharField(max_length=100)
    postnom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    SEXE_CHOICES = [('Homme', 'Homme'), ('Femme', 'Femme')]
    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES)
    date_naissance = models.DateField()
    ETAT_CIVIL_CHOICES = [
    ('Célibataire', 'Célibataire'),
    ('Marié(e)', 'Marié(e)'),
    ('Divorcé(e)', 'Divorcé(e)'),
    ('Veuf(ve)', 'Veuf(ve)'),
    ('Union libre', 'Union libre')]

    etat_civil=models.CharField(max_length=20, choices=ETAT_CIVIL_CHOICES)
    telephone = models.CharField(max_length=20, unique=True)
    COMMUNE_CHOICES = [
    ('Barumbu', 'Barumbu'),
    ('Bumbu', 'Bumbu'),
    ('Kalamu', 'Kalamu'),
    ('Kasa-Vubu', 'Kasa-Vubu'),
    ('Kinshasa', 'Kinshasa'),
    ('Kintambo', 'Kintambo'),
    ('Lingwala', 'Lingwala'),
    ('Gombe', 'Gombe'),
    ('Ngaliema', 'Ngaliema'),
    ('Mont Ngafula', 'Mont Ngafula'),
    ('Lemba', 'Lemba'),
    ('Ngaba', 'Ngaba'),
    ('Matete', 'Matete'),
    ('Kisenso', 'Kisenso'),
    ('Kimbanseke', 'Kimbanseke'),
    ('Nsele', 'Nsele'),
    ('Maluku', 'Maluku'),
    ('Masina', 'Masina'),
    ('Ndjili', 'Ndjili'),
    ('N’djili', 'N’djili'),
    ('Limete', 'Limete'),
    ('Selembao', 'Selembao'),
    ('Makala', 'Makala'),
    ('Kasavubu', 'Kasavubu'),
    ('Bandalungwa', 'Bandalungwa')]
    commune=models.CharField(max_length=100, choices=COMMUNE_CHOICES,null=True)
    quartier= models.CharField(max_length=100,null=True)
    avenue = models.CharField(max_length=100, null=True)
    cnom = models.CharField(max_length=100)
    langues = models.JSONField(default=list, blank=True, null=True)
    SPECIALITE_CHOICES = [
    ('Médecine générale', 'Médecine générale'),
    ('Pédiatrie', 'Pédiatrie'),
    ('Gynécologie-obstétrique', 'Gynécologie-obstétrique'),
    ('Chirurgie générale', 'Chirurgie générale'),
    ('Cardiologie', 'Cardiologie'),
    ('Dermatologie', 'Dermatologie'),
    ('Neurologie', 'Neurologie'),
    ('Psychiatrie', 'Psychiatrie'),
    ('Ophtalmologie', 'Ophtalmologie'),
    ('ORL (Oto-rhino-laryngologie)', 'ORL (Oto-rhino-laryngologie)'),
    ('Urologie', 'Urologie'),
    ('Orthopédie', 'Orthopédie'),
    ('Gastro-entérologie', 'Gastro-entérologie'),
    ('Endocrinologie', 'Endocrinologie'),
    ('Hématologie', 'Hématologie'),
    ('Néphrologie', 'Néphrologie'),
    ('Oncologie', 'Oncologie'),
    ('Rhumatologie', 'Rhumatologie'),
    ('Médecine interne', 'Médecine interne'),
    ('Médecine d’urgence', 'Médecine d’urgence'),
    ('Anesthésie-Réanimation', 'Anesthésie-Réanimation'),
    ('Radiologie', 'Radiologie'),
    ('Médecine tropicale', 'Médecine tropicale'),
    ('Santé publique', 'Santé publique'),
    ('Médecine du travail', 'Médecine du travail'),
    ('Médecine légale', 'Médecine légale'),
    ('Autre', 'Autre'),]
    specialite = models.CharField(max_length=100, choices=SPECIALITE_CHOICES)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.nom} {self.postnom} ({self.username})"

class SessionDiscussion(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.SET_NULL, null=True, blank=True)
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)

class Message(models.Model):
    session = models.ForeignKey(SessionDiscussion, on_delete=models.CASCADE)
    contenu = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # Émetteur (un seul des trois peut être non nul)
    emetteur_patient = models.ForeignKey(Patient, null=True, blank=True, on_delete=models.SET_NULL)
    emetteur_medecin = models.ForeignKey(Medecin, null=True, blank=True, on_delete=models.SET_NULL)
    emetteur_bot = models.BooleanField(default=False)

    def get_emetteur(self):
        if self.emetteur_patient:
            return f"Patient: {self.emetteur_patient.nom}"
        elif self.emetteur_medecin:
            return f"Médecin: {self.emetteur_medecin.nom}"
        elif self.emetteur_bot:
            return "Bot"
        else:
            return "Inconnu"