"""
Modèles de télémédecine intégrés pour l'application Lobiko
Adaptation du modèle de télémédecine pour s'intégrer avec les modèles existants
"""

import os
import uuid
import hashlib
import qrcode
from datetime import datetime, timedelta
from io import BytesIO
from django.db import models
from django.core.files.base import ContentFile
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

# Import des modèles existants
from .models import Patient, Medecin, SessionDiscussion


class DocumentMedical(models.Model):
    """Classe abstraite pour les documents médicaux (ordonnances et bons d'examens)"""
    
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('utilise', 'Utilisé'),
        ('annule', 'Annulé'),
        ('expire', 'Expiré'),
    ]
    
    numero_unique = models.CharField(max_length=50, unique=True, editable=False)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    session_discussion = models.ForeignKey(SessionDiscussion, on_delete=models.CASCADE, null=True, blank=True)
    date_prescription = models.DateTimeField(auto_now_add=True)
    date_validite = models.DateField(help_text="Date limite de validité")
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='actif')
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)
    hash_verification = models.CharField(max_length=64, editable=False)
    notes = models.TextField(blank=True, help_text="Notes additionnelles")
    date_modification = models.DateTimeField(auto_now=True)
    
    # Champs pour l'intégration WhatsApp
    envoye_whatsapp = models.BooleanField(default=False)
    date_envoi_whatsapp = models.DateTimeField(null=True, blank=True)
    message_whatsapp_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        if not self.numero_unique:
            self.numero_unique = self.generer_numero_unique()
        
        if not self.date_validite:
            self.date_validite = (datetime.now() + timedelta(days=30)).date()
        
        # Générer le hash de vérification
        self.hash_verification = self.generer_hash_verification()
        
        super().save(*args, **kwargs)
        
        # Générer le QR code après la sauvegarde
        if not self.qr_code:
            self.generer_qr_code()
    
    def generer_numero_unique(self):
        """Génère un numéro unique pour le document"""
        date_str = datetime.now().strftime('%Y%m%d')
        type_doc = self.__class__.__name__[:3].upper()
        
        # Compter les documents du même type créés aujourd'hui
        count = self.__class__.objects.filter(
            date_prescription__date=datetime.now().date()
        ).count() + 1
        
        return f"{date_str}-{type_doc}-{count:06d}"
    
    def generer_hash_verification(self):
        """Génère un hash de vérification pour le document"""
        data = f"{self.numero_unique}{self.medecin.cnom}{self.patient.whatsapp_id}{self.date_prescription}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def generer_qr_code(self):
        """Génère le QR code pour le document"""
        qr_data = {
            'numero': self.numero_unique,
            'hash': self.hash_verification,
            'type': self.__class__.__name__,
            'medecin': self.medecin.cnom,
            'patient': self.patient.whatsapp_id
        }
        
        qr_string = f"{qr_data['numero']}|{qr_data['hash']}|{qr_data['type']}|{qr_data['medecin']}|{qr_data['patient']}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Sauvegarder l'image
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        filename = f"qr_{self.numero_unique}.png"
        self.qr_code.save(filename, ContentFile(buffer.read()), save=False)
        
        # Sauvegarder sans déclencher une nouvelle génération
        super().save(update_fields=['qr_code'])
    
    @classmethod
    def verifier_document(cls, numero_unique, hash_verification=None):
        """Vérifie l'authenticité d'un document"""
        try:
            document = cls.objects.get(numero_unique=numero_unique)
            if hash_verification and document.hash_verification != hash_verification:
                return False, "Hash de vérification invalide"
            
            if document.statut == 'annule':
                return False, "Document annulé"
            
            if document.date_validite < datetime.now().date():
                return False, "Document expiré"
            
            return True, document
        except cls.DoesNotExist:
            return False, "Document non trouvé"
    
    @classmethod
    def verifier_qr_code(cls, qr_data):
        """Vérifie un document à partir des données du QR code"""
        try:
            parts = qr_data.split('|')
            if len(parts) != 5:
                return False, "Format QR code invalide"
            
            numero, hash_verif, type_doc, medecin_cnom, patient_whatsapp = parts
            
            if type_doc != cls.__name__:
                return False, "Type de document incorrect"
            
            return cls.verifier_document(numero, hash_verif)
        except Exception as e:
            return False, f"Erreur lors de la vérification: {str(e)}"


class ProduitPharmaceutique(models.Model):
    """Modèle pour les produits pharmaceutiques disponibles"""
    
    FORME_CHOICES = [
        ('comprime', 'Comprimé'),
        ('gelule', 'Gélule'),
        ('sirop', 'Sirop'),
        ('injection', 'Injection'),
        ('pommade', 'Pommade'),
        ('gouttes', 'Gouttes'),
        ('suppositoire', 'Suppositoire'),
        ('autre', 'Autre'),
    ]
    
    nom_commercial = models.CharField(max_length=200)
    principe_actif = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    forme = models.CharField(max_length=20, choices=FORME_CHOICES)
    laboratoire = models.CharField(max_length=200, blank=True)
    posologie_adulte = models.TextField(blank=True)
    posologie_enfant = models.TextField(blank=True)
    duree_traitement_standard = models.CharField(max_length=100, blank=True)
    contre_indications = models.TextField(blank=True)
    effets_secondaires = models.TextField(blank=True)
    interactions = models.TextField(blank=True)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    disponible = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Produit pharmaceutique"
        verbose_name_plural = "Produits pharmaceutiques"
        ordering = ['nom_commercial']
    
    def __str__(self):
        return f"{self.nom_commercial} {self.dosage} ({self.forme})"


class ActeMedical(models.Model):
    """Modèle pour les actes médicaux disponibles"""
    
    CATEGORIE_CHOICES = [
        ('BIOLOGIE', 'Analyses biologiques'),
        ('IMAGERIE', 'Imagerie médicale'),
        ('CARDIOLOGIE', 'Examens cardiologiques'),
        ('PNEUMOLOGIE', 'Examens pneumologiques'),
        ('NEUROLOGIE', 'Examens neurologiques'),
        ('GYNECOLOGIE', 'Examens gynécologiques'),
        ('UROLOGIE', 'Examens urologiques'),
        ('DERMATOLOGIE', 'Examens dermatologiques'),
        ('OPHTALMOLOGIE', 'Examens ophtalmologiques'),
        ('ORL', 'Examens ORL'),
        ('AUTRE', 'Autre'),
    ]
    
    nom = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES)
    description = models.TextField(blank=True)
    preparation_requise = models.TextField(blank=True)
    duree_estimee = models.CharField(max_length=100, blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    disponible = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Acte médical"
        verbose_name_plural = "Actes médicaux"
        ordering = ['categorie', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.code})"


class Ordonnance(DocumentMedical):
    """Modèle pour les ordonnances médicales"""
    
    diagnostic = models.TextField(help_text="Diagnostic principal")
    motif_prescription = models.TextField(blank=True, help_text="Motif de la prescription")
    instructions_generales = models.TextField(blank=True, help_text="Instructions générales pour le patient")
    instructions_pharmacien = models.TextField(blank=True, help_text="Instructions spéciales pour le pharmacien")
    renouvellement_autorise = models.BooleanField(default=False)
    nombre_renouvellements = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Ordonnance"
        verbose_name_plural = "Ordonnances"
    
    def __str__(self):
        return f"Ordonnance {self.numero_unique} - {self.patient.nom_complet()}"
    
    @property
    def nombre_medicaments(self):
        return self.prescriptions.count()


class PrescriptionMedicament(models.Model):
    """Modèle pour les médicaments prescrits dans une ordonnance"""
    
    ordonnance = models.ForeignKey(Ordonnance, on_delete=models.CASCADE, related_name='prescriptions')
    produit = models.ForeignKey(ProduitPharmaceutique, on_delete=models.CASCADE)
    quantite = models.CharField(max_length=100, help_text="Quantité prescrite (ex: 1 boîte, 30 comprimés)")
    posologie = models.TextField(help_text="Posologie détaillée")
    duree_traitement = models.CharField(max_length=100, help_text="Durée du traitement")
    instructions_specifiques = models.TextField(blank=True, help_text="Instructions spécifiques pour ce médicament")
    
    # Modalités de prise
    avant_repas = models.BooleanField(default=False)
    avec_repas = models.BooleanField(default=False)
    apres_repas = models.BooleanField(default=False)
    
    # Options
    substitution_autorisee = models.BooleanField(default=True, help_text="Substitution par un générique autorisée")
    
    class Meta:
        verbose_name = "Prescription de médicament"
        verbose_name_plural = "Prescriptions de médicaments"
    
    def __str__(self):
        return f"{self.produit.nom_commercial} - {self.posologie}"


class BonExamen(DocumentMedical):
    """Modèle pour les bons d'examens médicaux"""
    
    PRIORITE_CHOICES = [
        ('NORMAL', 'Normal'),
        ('URGENT', 'Urgent'),
        ('TRES_URGENT', 'Très urgent'),
    ]
    
    motif = models.TextField(help_text="Motif des examens demandés")
    diagnostic_provisoire = models.TextField(blank=True, help_text="Diagnostic provisoire")
    renseignements_cliniques = models.TextField(blank=True, help_text="Renseignements cliniques pertinents")
    instructions_preparation = models.TextField(blank=True, help_text="Instructions de préparation pour le patient")
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default='NORMAL')
    delai_realisation = models.CharField(max_length=100, blank=True, help_text="Délai souhaité pour la réalisation")
    
    class Meta:
        verbose_name = "Bon d'examen"
        verbose_name_plural = "Bons d'examens"
    
    def __str__(self):
        return f"Bon d'examen {self.numero_unique} - {self.patient.nom_complet()}"
    
    @property
    def nombre_examens(self):
        return self.examens.count()


class ExamenPrescrit(models.Model):
    """Modèle pour les examens prescrits dans un bon d'examen"""
    
    bon_examen = models.ForeignKey(BonExamen, on_delete=models.CASCADE, related_name='examens')
    acte = models.ForeignKey(ActeMedical, on_delete=models.CASCADE)
    localisation = models.CharField(max_length=200, blank=True, help_text="Localisation spécifique (ex: genou droit)")
    instructions_specifiques = models.TextField(blank=True, help_text="Instructions spécifiques pour cet examen")
    preparation_specifique = models.TextField(blank=True, help_text="Préparation spécifique requise")
    urgent = models.BooleanField(default=False, help_text="Examen urgent")
    
    class Meta:
        verbose_name = "Examen prescrit"
        verbose_name_plural = "Examens prescrits"
    
    def __str__(self):
        localisation = f" ({self.localisation})" if self.localisation else ""
        return f"{self.acte.nom}{localisation}"


class HistoriqueVerification(models.Model):
    """Historique des vérifications de documents"""
    
    numero_document = models.CharField(max_length=50)
    type_document = models.CharField(max_length=50)
    date_verification = models.DateTimeField(auto_now_add=True)
    resultat_verification = models.BooleanField()
    message = models.TextField()
    ip_verification = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Historique de vérification"
        verbose_name_plural = "Historiques de vérifications"
    
    def __str__(self):
        return f"Vérification {self.numero_document} - {self.date_verification}"


class MessagePrescription(models.Model):
    """Messages de prescription envoyés via WhatsApp"""
    
    TYPE_CHOICES = [
        ('ordonnance', 'Ordonnance'),
        ('bon_examen', 'Bon d\'examen'),
    ]
    
    session_discussion = models.ForeignKey(SessionDiscussion, on_delete=models.CASCADE)
    type_prescription = models.CharField(max_length=20, choices=TYPE_CHOICES)
    ordonnance = models.ForeignKey(Ordonnance, on_delete=models.CASCADE, null=True, blank=True)
    bon_examen = models.ForeignKey(BonExamen, on_delete=models.CASCADE, null=True, blank=True)
    message_whatsapp_id = models.CharField(max_length=100, blank=True)
    pdf_url = models.URLField(blank=True)
    date_envoi = models.DateTimeField(auto_now_add=True)
    envoye_avec_succes = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Message de prescription"
        verbose_name_plural = "Messages de prescriptions"
    
    def __str__(self):
        if self.ordonnance:
            return f"Ordonnance {self.ordonnance.numero_unique} - {self.date_envoi}"
        elif self.bon_examen:
            return f"Bon d'examen {self.bon_examen.numero_unique} - {self.date_envoi}"
        return f"Message prescription {self.id}"


# Signaux pour automatiser certaines actions
@receiver(post_save, sender=Ordonnance)
def ordonnance_created(sender, instance, created, **kwargs):
    """Signal déclenché à la création d'une ordonnance"""
    if created:
        # Enregistrer dans l'historique
        HistoriqueVerification.objects.create(
            numero_document=instance.numero_unique,
            type_document='Ordonnance',
            resultat_verification=True,
            message=f"Ordonnance créée par Dr {instance.medecin.nom_complet()}"
        )


@receiver(post_save, sender=BonExamen)
def bon_examen_created(sender, instance, created, **kwargs):
    """Signal déclenché à la création d'un bon d'examen"""
    if created:
        # Enregistrer dans l'historique
        HistoriqueVerification.objects.create(
            numero_document=instance.numero_unique,
            type_document='BonExamen',
            resultat_verification=True,
            message=f"Bon d'examen créé par Dr {instance.medecin.nom_complet()}"
        )

