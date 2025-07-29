"""
Serializers pour l'API REST de télémédecine
"""

from rest_framework import serializers
from .telemedicine_models import (
    ProduitPharmaceutique, ActeMedical, Ordonnance, PrescriptionMedicament,
    BonExamen, ExamenPrescrit, MessagePrescription
)


class ProduitPharmaceutiqueSerializer(serializers.ModelSerializer):
    """Serializer pour les produits pharmaceutiques"""
    
    class Meta:
        model = ProduitPharmaceutique
        fields = [
            'id', 'nom_commercial', 'principe_actif', 'dosage', 'forme',
            'laboratoire', 'posologie_adulte', 'posologie_enfant',
            'duree_traitement_standard', 'prix_unitaire', 'disponible'
        ]


class ActeMedicalSerializer(serializers.ModelSerializer):
    """Serializer pour les actes médicaux"""
    
    class Meta:
        model = ActeMedical
        fields = [
            'id', 'nom', 'code', 'categorie', 'description',
            'preparation_requise', 'duree_estimee', 'prix', 'disponible'
        ]


class PrescriptionMedicamentSerializer(serializers.ModelSerializer):
    """Serializer pour les prescriptions de médicaments"""
    
    produit = ProduitPharmaceutiqueSerializer(read_only=True)
    
    class Meta:
        model = PrescriptionMedicament
        fields = [
            'id', 'produit', 'quantite', 'posologie', 'duree_traitement',
            'instructions_specifiques', 'avant_repas', 'avec_repas',
            'apres_repas', 'substitution_autorisee'
        ]


class ExamenPrescritSerializer(serializers.ModelSerializer):
    """Serializer pour les examens prescrits"""
    
    acte = ActeMedicalSerializer(read_only=True)
    
    class Meta:
        model = ExamenPrescrit
        fields = [
            'id', 'acte', 'localisation', 'instructions_specifiques',
            'preparation_specifique', 'urgent'
        ]


class OrdonnanceSerializer(serializers.ModelSerializer):
    """Serializer pour les ordonnances"""
    
    prescriptions = PrescriptionMedicamentSerializer(many=True, read_only=True)
    medecin_nom = serializers.CharField(source='medecin.nom_complet', read_only=True)
    patient_nom = serializers.CharField(source='patient.nom_complet', read_only=True)
    nombre_medicaments = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Ordonnance
        fields = [
            'id', 'numero_unique', 'medecin_nom', 'patient_nom',
            'date_prescription', 'date_validite', 'statut',
            'diagnostic', 'motif_prescription', 'instructions_generales',
            'instructions_pharmacien', 'renouvellement_autorise',
            'nombre_renouvellements', 'prescriptions', 'nombre_medicaments',
            'envoye_whatsapp', 'date_envoi_whatsapp'
        ]


class BonExamenSerializer(serializers.ModelSerializer):
    """Serializer pour les bons d'examens"""
    
    examens = ExamenPrescritSerializer(many=True, read_only=True)
    medecin_nom = serializers.CharField(source='medecin.nom_complet', read_only=True)
    patient_nom = serializers.CharField(source='patient.nom_complet', read_only=True)
    nombre_examens = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = BonExamen
        fields = [
            'id', 'numero_unique', 'medecin_nom', 'patient_nom',
            'date_prescription', 'date_validite', 'statut',
            'motif', 'diagnostic_provisoire', 'renseignements_cliniques',
            'instructions_preparation', 'priorite', 'delai_realisation',
            'examens', 'nombre_examens', 'envoye_whatsapp', 'date_envoi_whatsapp'
        ]


class MessagePrescriptionSerializer(serializers.ModelSerializer):
    """Serializer pour les messages de prescription"""
    
    ordonnance = OrdonnanceSerializer(read_only=True)
    bon_examen = BonExamenSerializer(read_only=True)
    
    class Meta:
        model = MessagePrescription
        fields = [
            'id', 'type_prescription', 'ordonnance', 'bon_examen',
            'message_whatsapp_id', 'pdf_url', 'date_envoi', 'envoye_avec_succes'
        ]


# Serializers pour la création de prescriptions
class CreerPrescriptionSerializer(serializers.Serializer):
    """Serializer pour créer une prescription"""
    
    session_id = serializers.IntegerField()
    medecin_id = serializers.IntegerField()
    diagnostic = serializers.CharField(max_length=1000)
    motif_prescription = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    instructions_generales = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    date_validite = serializers.DateField(required=False)
    renouvellement_autorise = serializers.BooleanField(default=False)
    
    medicaments = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )


class CreerBonExamenSerializer(serializers.Serializer):
    """Serializer pour créer un bon d'examen"""
    
    session_id = serializers.IntegerField()
    medecin_id = serializers.IntegerField()
    motif = serializers.CharField(max_length=1000)
    diagnostic_provisoire = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    renseignements_cliniques = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    instructions_preparation = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    priorite = serializers.ChoiceField(choices=BonExamen.PRIORITE_CHOICES, default='NORMAL')
    delai_realisation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    validite_jours = serializers.IntegerField(default=60, min_value=1, max_value=365)
    
    examens = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )

