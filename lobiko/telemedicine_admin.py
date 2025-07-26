"""
Configuration de l'interface d'administration Django pour les modèles de télémédecine
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .telemedicine_models import (
    ProduitPharmaceutique, ActeMedical, Ordonnance, PrescriptionMedicament,
    BonExamen, ExamenPrescrit, HistoriqueVerification, MessagePrescription
)


@admin.register(ProduitPharmaceutique)
class ProduitPharmaceutiqueAdmin(admin.ModelAdmin):
    list_display = ['nom_commercial', 'principe_actif', 'dosage', 'forme', 'laboratoire', 'disponible', 'prix_unitaire']
    list_filter = ['forme', 'disponible', 'laboratoire']
    search_fields = ['nom_commercial', 'principe_actif', 'laboratoire']
    readonly_fields = ['date_creation']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom_commercial', 'principe_actif', 'dosage', 'forme', 'laboratoire', 'prix_unitaire', 'disponible')
        }),
        ('Posologie', {
            'fields': ('posologie_adulte', 'posologie_enfant', 'duree_traitement_standard')
        }),
        ('Informations médicales', {
            'fields': ('contre_indications', 'effets_secondaires', 'interactions')
        }),
        ('Métadonnées', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        })
    )


@admin.register(ActeMedical)
class ActeMedicalAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'categorie', 'prix', 'disponible']
    list_filter = ['categorie', 'disponible']
    search_fields = ['nom', 'code', 'description']
    readonly_fields = ['date_creation']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'code', 'categorie', 'description', 'prix', 'disponible')
        }),
        ('Instructions', {
            'fields': ('preparation_requise', 'duree_estimee')
        }),
        ('Métadonnées', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        })
    )


class PrescriptionMedicamentInline(admin.TabularInline):
    model = PrescriptionMedicament
    extra = 0
    fields = ['produit', 'quantite', 'posologie', 'duree_traitement', 'avant_repas', 'avec_repas', 'apres_repas']


@admin.register(Ordonnance)
class OrdonnanceAdmin(admin.ModelAdmin):
    list_display = ['numero_unique', 'get_medecin', 'get_patient', 'date_prescription', 'statut', 'nombre_medicaments', 'afficher_qr_code']
    list_filter = ['statut', 'date_prescription', 'date_validite', 'renouvellement_autorise']
    search_fields = ['numero_unique', 'medecin__nom', 'patient__nom', 'diagnostic']
    readonly_fields = ['numero_unique', 'hash_verification', 'date_prescription', 'date_modification', 'afficher_qr_code']
    inlines = [PrescriptionMedicamentInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('numero_unique', 'medecin', 'patient', 'session_discussion', 'date_prescription', 'date_validite', 'statut')
        }),
        ('Prescription', {
            'fields': ('diagnostic', 'motif_prescription', 'instructions_generales', 'instructions_pharmacien')
        }),
        ('Renouvellement', {
            'fields': ('renouvellement_autorise', 'nombre_renouvellements')
        }),
        ('WhatsApp', {
            'fields': ('envoye_whatsapp', 'date_envoi_whatsapp', 'message_whatsapp_id'),
            'classes': ('collapse',)
        }),
        ('Sécurité', {
            'fields': ('hash_verification', 'afficher_qr_code'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Métadonnées', {
            'fields': ('date_modification',),
            'classes': ('collapse',)
        })
    )
    
    def get_medecin(self, obj):
        return f"Dr {obj.medecin.nom_complet()}"
    get_medecin.short_description = 'Médecin'
    
    def get_patient(self, obj):
        return obj.patient.nom_complet()
    get_patient.short_description = 'Patient'
    
    def afficher_qr_code(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" width="50" height="50" />',
                obj.qr_code.url
            )
        return "Pas de QR code"
    afficher_qr_code.short_description = 'QR Code'
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:  # Si l'objet existe déjà
            readonly.extend(['medecin', 'patient', 'session_discussion'])
        return readonly


class ExamenPrescritInline(admin.TabularInline):
    model = ExamenPrescrit
    extra = 0
    fields = ['acte', 'localisation', 'instructions_specifiques', 'urgent']


@admin.register(BonExamen)
class BonExamenAdmin(admin.ModelAdmin):
    list_display = ['numero_unique', 'get_medecin', 'get_patient', 'date_prescription', 'statut', 'priorite', 'nombre_examens', 'afficher_qr_code']
    list_filter = ['statut', 'priorite', 'date_prescription', 'date_validite']
    search_fields = ['numero_unique', 'medecin__nom', 'patient__nom', 'motif']
    readonly_fields = ['numero_unique', 'hash_verification', 'date_prescription', 'date_modification', 'afficher_qr_code']
    inlines = [ExamenPrescritInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('numero_unique', 'medecin', 'patient', 'session_discussion', 'date_prescription', 'date_validite', 'statut')
        }),
        ('Prescription', {
            'fields': ('motif', 'diagnostic_provisoire', 'renseignements_cliniques', 'instructions_preparation')
        }),
        ('Priorité et délais', {
            'fields': ('priorite', 'delai_realisation')
        }),
        ('WhatsApp', {
            'fields': ('envoye_whatsapp', 'date_envoi_whatsapp', 'message_whatsapp_id'),
            'classes': ('collapse',)
        }),
        ('Sécurité', {
            'fields': ('hash_verification', 'afficher_qr_code'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Métadonnées', {
            'fields': ('date_modification',),
            'classes': ('collapse',)
        })
    )
    
    def get_medecin(self, obj):
        return f"Dr {obj.medecin.nom_complet()}"
    get_medecin.short_description = 'Médecin'
    
    def get_patient(self, obj):
        return obj.patient.nom_complet()
    get_patient.short_description = 'Patient'
    
    def afficher_qr_code(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" width="50" height="50" />',
                obj.qr_code.url
            )
        return "Pas de QR code"
    afficher_qr_code.short_description = 'QR Code'
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:  # Si l'objet existe déjà
            readonly.extend(['medecin', 'patient', 'session_discussion'])
        return readonly


@admin.register(PrescriptionMedicament)
class PrescriptionMedicamentAdmin(admin.ModelAdmin):
    list_display = ['ordonnance', 'produit', 'quantite', 'posologie', 'duree_traitement']
    list_filter = ['avant_repas', 'avec_repas', 'apres_repas', 'substitution_autorisee']
    search_fields = ['ordonnance__numero_unique', 'produit__nom_commercial', 'posologie']


@admin.register(ExamenPrescrit)
class ExamenPrescritAdmin(admin.ModelAdmin):
    list_display = ['bon_examen', 'acte', 'localisation', 'urgent']
    list_filter = ['urgent', 'acte__categorie']
    search_fields = ['bon_examen__numero_unique', 'acte__nom', 'localisation']


@admin.register(MessagePrescription)
class MessagePrescriptionAdmin(admin.ModelAdmin):
    list_display = ['get_numero_document', 'type_prescription', 'session_discussion', 'date_envoi', 'envoye_avec_succes']
    list_filter = ['type_prescription', 'envoye_avec_succes', 'date_envoi']
    search_fields = ['ordonnance__numero_unique', 'bon_examen__numero_unique', 'message_whatsapp_id']
    readonly_fields = ['date_envoi']
    
    def get_numero_document(self, obj):
        if obj.ordonnance:
            return obj.ordonnance.numero_unique
        elif obj.bon_examen:
            return obj.bon_examen.numero_unique
        return "N/A"
    get_numero_document.short_description = 'Numéro de document'


@admin.register(HistoriqueVerification)
class HistoriqueVerificationAdmin(admin.ModelAdmin):
    list_display = ['numero_document', 'type_document', 'date_verification', 'resultat_verification', 'ip_verification']
    list_filter = ['type_document', 'resultat_verification', 'date_verification']
    search_fields = ['numero_document', 'message']
    readonly_fields = ['numero_document', 'type_document', 'date_verification', 'resultat_verification', 'message', 'ip_verification']
    
    def has_add_permission(self, request):
        return False  # Empêche l'ajout manuel d'historiques
    
    def has_change_permission(self, request, obj=None):
        return False  # Empêche la modification des historiques
    
    def has_delete_permission(self, request, obj=None):
        return False  # Empêche la suppression des historiques

