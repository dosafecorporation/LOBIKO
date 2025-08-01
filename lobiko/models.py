from datetime import date
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import RegexValidator

from decimal import Decimal
from django.utils import timezone

# Définition des choix communs
class Choices:
    SEXE = [('H', 'Homme'), ('F', 'Femme')]
    COMMUNE = [
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
        ('Bandalungwa', 'Bandalungwa')
    ]
    ETAT_CIVIL = [
        ('Célibataire', 'Célibataire'),
        ('Marié(e)', 'Marié(e)'),
        ('Divorcé(e)', 'Divorcé(e)'),
        ('Veuf(ve)', 'Veuf(ve)'),
        ('Union libre', 'Union libre')
    ]
    SPECIALITE = [
        ('Médecine générale', 'Médecine générale'),
        ('Pédiatrie', 'Pédiatrie'),
        ('Gynécologie-obstétrique', 'Gynécologie-obstétrique'),
        ('Chirurgie générale', 'Chirurgie générale'),
        ('Cardiologie', 'Cardiologie'),
        ('Dermatologie', 'Dermatologie'),
        ('Neurologie', 'Neurologie'),
        ('Psychiatrie', 'Psychiatrie'),
        ('Ophtalmologie', 'Ophtalmologie'),
        ('ORL', 'ORL (Oto-rhino-laryngologie)'),
        ('Urologie', 'Urologie'),
        ('Orthopédie', 'Orthopédie'),
        ('Gastro-entérologie', 'Gastro-entérologie'),
        ('Endocrinologie', 'Endocrinologie'),
        ('Hématologie', 'Hématologie'),
        ('Néphrologie', 'Néphrologie'),
        ('Oncologie', 'Oncologie'),
        ('Rhumatologie', 'Rhumatologie'),
        ('Médecine interne', 'Médecine interne'),
        ('Médecine d\'urgence', 'Médecine d\'urgence'),
        ('Anesthésie-Réanimation', 'Anesthésie-Réanimation'),
        ('Radiologie', 'Radiologie'),
        ('Médecine tropicale', 'Médecine tropicale'),
        ('Santé publique', 'Santé publique'),
        ('Médecine du travail', 'Médecine du travail'),
        ('Médecine légale', 'Médecine légale'),
        ('Autre', 'Autre'),
    ]
    LANGUES = [
        ('fr', 'Français'),
        ('ln', 'Lingala'),
        ('sw', 'Swahili'),
        ('en', 'Anglais'),
        ('kg', 'Kikongo'),
        ('ts', 'Tshiluba'),
    ]

# Validateur pour les numéros de téléphone
phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Le numéro doit être au format: '+999999999'."
)

def validate_langues(value):
    """Valide que les langues sélectionnées sont parmi les choix disponibles"""
    if value is None:
        return
    valid_langues = [code for code, _ in Choices.LANGUES]
    for lang in value:
        if lang not in valid_langues:
            raise ValidationError(f"Langue non valide: {lang}")

class Patient(models.Model):
    whatsapp_id = models.CharField(max_length=100, unique=True)
    nom = models.CharField(max_length=100)
    postnom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=Choices.SEXE)
    date_naissance = models.DateField()
    etat_civil = models.CharField(max_length=20, choices=Choices.ETAT_CIVIL)
    telephone = models.CharField(max_length=20, unique=True)
    commune = models.CharField(max_length=100, choices=Choices.COMMUNE, null=True)
    quartier = models.CharField(max_length=100, null=True)
    avenue = models.CharField(max_length=100, null=True)
    langue_preferee = models.JSONField(
        null=True,
        blank=True,
        default=list,
        validators=[validate_langues]
    )

    def clean(self):
        """Validation supplémentaire au niveau du modèle"""
        super().clean()
        if self.langue_preferee:
            validate_langues(self.langue_preferee)

    def nom_complet(self):
        return f"{self.nom} {self.postnom} {self.prenom}".strip()
    
    @property
    def age(self):
        today = date.today()
        return today.year - self.date_naissance.year - (
            (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
        )
    
    def langues_display(self):
        if not self.langue_preferee:
            return "Non spécifié"
        return ", ".join([dict(Choices.LANGUES).get(lang, lang) for lang in self.langue_preferee])
    
    def __str__(self):
        return f"{self.nom_complet()} ({self.telephone})"

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

class Assureur(models.Model):
    nom = models.CharField(max_length=100)
    contact = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nom} ({self.contact})"

    class Meta:
        verbose_name = "Assureur"
        verbose_name_plural = "Assureurs"

class Assurance(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    assureur = models.ForeignKey(Assureur, on_delete=models.CASCADE)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.patient} - {self.assureur} ({self.date_debut} à {self.date_fin or '...'})"

    def clean(self):
        if self.date_fin and self.date_fin < self.date_debut:
            raise ValidationError("La date de fin doit être postérieure à la date de début.")

    class Meta:
        verbose_name = "Assurance"
        verbose_name_plural = "Assurances"

class Medecin(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    nom = models.CharField(max_length=100)
    postnom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=Choices.SEXE)
    date_naissance = models.DateField()
    etat_civil = models.CharField(max_length=20, choices=Choices.ETAT_CIVIL)
    telephone = models.CharField(
        max_length=20, 
        unique=True,
        validators=[phone_regex],
        db_index=True
    )
    commune = models.CharField(max_length=100, choices=Choices.COMMUNE, null=True)
    quartier = models.CharField(max_length=100, null=True)
    avenue = models.CharField(max_length=100, null=True)
    cnom = models.CharField(max_length=100, verbose_name="Numéro CNOM")
    langues = models.JSONField(
        default=list,
        blank=True,
        null=True,
        validators=[validate_langues]
    )
    specialite = models.CharField(max_length=100, choices=Choices.SPECIALITE)

    def clean(self):
        """Validation supplémentaire au niveau du modèle"""
        super().clean()
        if self.langues:
            validate_langues(self.langues)

    def nom_complet(self):
        return f"{self.nom} {self.postnom} {self.prenom}".strip()
    
    @property
    def langues_display(self):
        if not self.langues:
            return "Non spécifié"
        return ", ".join([dict(Choices.LANGUES).get(lang, lang) for lang in self.langues])
    
    def __str__(self):
        return f"Dr. {self.nom_complet()} ({self.specialite})"

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    class Meta:
        verbose_name = "Médecin"
        verbose_name_plural = "Médecins"

class SessionDiscussion(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('EN_COURS', 'En cours'),
        ('TERMINEE', 'Terminée'),
        ('ANNULEE', 'Annulée'),
    ]

    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    medecin = models.ForeignKey('Medecin', on_delete=models.SET_NULL, null=True, blank=True)
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')

    def __str__(self):
        medecin = f"avec Dr. {self.medecin}" if self.medecin else "sans médecin"
        return f"Session {self.id} - {self.patient} {medecin} ({self.date_debut})"

    def update_statut(self):
        """Met à jour automatiquement le statut de la session."""
        if self.date_fin:
            self.statut = 'TERMINEE'
        elif not self.medecin:
            self.statut = 'EN_ATTENTE'
        else:
            self.statut = 'EN_COURS'
        self.save(update_fields=['statut'])

    def save(self, *args, **kwargs):
        """Appliquer automatiquement la logique de statut."""
        if self.date_fin:
            self.statut = 'TERMINEE'
        elif not self.medecin:
            self.statut = 'EN_ATTENTE'
        else:
            self.statut = 'EN_COURS'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Session de discussion"
        verbose_name_plural = "Sessions de discussion"

class Message(models.Model):
    EMETTEUR_TYPE_CHOICES = [
        ('PATIENT', 'Patient'),
        ('MEDECIN', 'Médecin'),
        ('BOT', 'Bot'),
    ]
    
    session = models.ForeignKey(SessionDiscussion, on_delete=models.CASCADE, related_name='messages')
    contenu = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    emetteur_type = models.CharField(max_length=10, choices=EMETTEUR_TYPE_CHOICES)
    emetteur_id = models.PositiveIntegerField()

    @property
    def emetteur(self):
        if self.emetteur_type == 'PATIENT':
            return Patient.objects.get(id=self.emetteur_id)
        elif self.emetteur_type == 'MEDECIN':
            return Medecin.objects.get(id=self.emetteur_id)
        return None

    def __str__(self):
        emetteur = self.emetteur
        prefix = f"{self.get_emetteur_type_display()}"
        if emetteur:
            if hasattr(emetteur, 'nom_complet'):
                return f"{prefix}: {emetteur.nom_complet} - {self.timestamp}"
            return f"{prefix}: {emetteur} - {self.timestamp}"
        return f"{prefix}: Message - {self.timestamp}"

    class Meta:
        ordering = ['timestamp']
        verbose_name = "Message"
        verbose_name_plural = "Messages"

class MediaMessage(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('document', 'Document'),
        ('other', 'Autre'),
    ]
    
    session = models.ForeignKey(SessionDiscussion, on_delete=models.CASCADE, related_name='media_files')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file_url = models.URLField(max_length=500)
    file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    emetteur_type = models.CharField(max_length=10, choices=Message.EMETTEUR_TYPE_CHOICES)
    emetteur_id = models.PositiveIntegerField()
    s3_key = models.CharField(max_length=500)

    def __str__(self):
        return f"{self.get_media_type_display()} - {self.file_name}"

    class Meta:
        verbose_name = "Fichier média"
        verbose_name_plural = "Fichiers médias"

class TarifConsultation(models.Model):
    medecin = models.ForeignKey('Medecin', on_delete=models.CASCADE, related_name='tarifs')
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_debut = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-date_debut']
        verbose_name = "Tarif de consultation"
        verbose_name_plural = "Tarifs de consultation"

    def __str__(self):
        return f"{self.montant} $ (depuis {self.date_debut})"

from .telemedicine_models import (
    ProduitPharmaceutique, ActeMedical, Ordonnance, PrescriptionMedicament,
    BonExamen, ExamenPrescrit, MessagePrescription, HistoriqueVerification
)