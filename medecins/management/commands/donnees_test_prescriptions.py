# donnees_test_prescriptions.py - Données de test pour les produits pharmaceutiques et actes médicaux
import django
import os


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lobikohealth.settings')
django.setup()

from django.core.management.base import BaseCommand
from lobiko.models import ProduitPharmaceutique, ActeMedical


class Command(BaseCommand):
    help = 'Charge les données de test pour les produits pharmaceutiques et actes médicaux'

    def handle(self, *args, **options):
        self.stdout.write('Chargement des produits pharmaceutiques...')
        self.charger_produits_pharmaceutiques()
        
        self.stdout.write('Chargement des actes médicaux...')
        self.charger_actes_medicaux()
        
        self.stdout.write(self.style.SUCCESS('Données de test chargées avec succès'))

    def charger_produits_pharmaceutiques(self):
        """Charger les produits pharmaceutiques de test"""
        produits = [
            {
                'nom_commercial': 'Paracétamol Biogaran',
                'nom_generique': 'Paracétamol',
                'principe_actif': 'Paracétamol',
                'dosage': '500mg',
                'forme': 'Comprimé',
                'categorie': 'ANALGESIQUE',
                'posologie_adulte': '1 à 2 comprimés, 1 à 3 fois par jour',
                'posologie_enfant': '1/2 comprimé, 2 à 3 fois par jour (enfants > 6 ans)',
                'duree_traitement_standard': '3 à 5 jours',
                'contre_indications': 'Hypersensibilité au paracétamol, insuffisance hépatique sévère',
                'precautions': 'Ne pas dépasser 3g par jour chez l\'adulte',
                'interactions': 'Warfarine (surveillance INR)',
                'conservation': 'Température ambiante, à l\'abri de l\'humidité',
                'prescription_requise': False,
                'remboursable': True,
                'actif': True
            },
            {
                'nom_commercial': 'Amoxicilline Sandoz',
                'nom_generique': 'Amoxicilline',
                'principe_actif': 'Amoxicilline trihydrate',
                'dosage': '1g',
                'forme': 'Comprimé pelliculé',
                'categorie': 'ANTIBIOTIQUE',
                'posologie_adulte': '1g matin et soir',
                'posologie_enfant': '50mg/kg/jour en 2 prises',
                'duree_traitement_standard': '7 à 10 jours',
                'contre_indications': 'Allergie aux pénicillines, mononucléose infectieuse',
                'precautions': 'Surveillance en cas d\'insuffisance rénale',
                'interactions': 'Méthotrexate, anticoagulants oraux',
                'conservation': 'Température ambiante, à l\'abri de la lumière',
                'prescription_requise': True,
                'remboursable': True,
                'actif': True
            },
            {
                'nom_commercial': 'Doliprane',
                'nom_generique': 'Paracétamol',
                'principe_actif': 'Paracétamol',
                'dosage': '1000mg',
                'forme': 'Comprimé effervescent',
                'categorie': 'ANALGESIQUE',
                'posologie_adulte': '1 comprimé, 1 à 3 fois par jour',
                'posologie_enfant': 'Non recommandé < 15 ans',
                'duree_traitement_standard': '3 jours',
                'contre_indications': 'Hypersensibilité au paracétamol, phénylcétonurie',
                'precautions': 'Contient de l\'aspartam',
                'interactions': 'Warfarine (surveillance INR)',
                'conservation': 'Température ambiante, tube bien fermé',
                'prescription_requise': False,
                'remboursable': True,
                'actif': True
            },
            {
                'nom_commercial': 'Ventoline',
                'nom_generique': 'Salbutamol',
                'principe_actif': 'Sulfate de salbutamol',
                'dosage': '100µg/dose',
                'forme': 'Aérosol doseur',
                'categorie': 'BRONCHODILATATEUR',
                'posologie_adulte': '1 à 2 bouffées, 4 fois par jour maximum',
                'posologie_enfant': '1 bouffée, 3 fois par jour maximum',
                'duree_traitement_standard': 'Selon besoin',
                'contre_indications': 'Hypersensibilité au salbutamol',
                'precautions': 'Surveillance cardiaque si cardiopathie',
                'interactions': 'Bêta-bloquants (antagonisme)',
                'conservation': 'Température ambiante, protéger du gel',
                'prescription_requise': True,
                'remboursable': True,
                'actif': True
            },
            {
                'nom_commercial': 'Inexium',
                'nom_generique': 'Ésoméprazole',
                'principe_actif': 'Ésoméprazole magnésium',
                'dosage': '20mg',
                'forme': 'Gélule gastro-résistante',
                'categorie': 'ANTIULCEREUX',
                'posologie_adulte': '1 gélule par jour, le matin à jeun',
                'posologie_enfant': 'Selon poids corporel',
                'duree_traitement_standard': '4 à 8 semaines',
                'contre_indications': 'Hypersensibilité aux IPP',
                'precautions': 'Surveillance si traitement prolongé',
                'interactions': 'Clopidogrel, atazanavir',
                'conservation': 'Température ambiante, à l\'abri de l\'humidité',
                'prescription_requise': True,
                'remboursable': True,
                'actif': True
            },
            {
                'nom_commercial': 'Spasfon',
                'nom_generique': 'Phloroglucinol',
                'principe_actif': 'Phloroglucinol hydraté',
                'dosage': '80mg',
                'forme': 'Comprimé pelliculé',
                'categorie': 'ANTISPASMODIQUE',
                'posologie_adulte': '2 comprimés, 3 fois par jour',
                'posologie_enfant': '1 comprimé, 3 fois par jour (> 6 ans)',
                'duree_traitement_standard': '2 à 3 jours',
                'contre_indications': 'Hypersensibilité au phloroglucinol',
                'precautions': 'Arrêter si pas d\'amélioration après 2 jours',
                'interactions': 'Aucune interaction connue',
                'conservation': 'Température ambiante',
                'prescription_requise': False,
                'remboursable': True,
                'actif': True
            },
            {
                'nom_commercial': 'Augmentin',
                'nom_generique': 'Amoxicilline/Acide clavulanique',
                'principe_actif': 'Amoxicilline + Acide clavulanique',
                'dosage': '1g/125mg',
                'forme': 'Comprimé pelliculé',
                'categorie': 'ANTIBIOTIQUE',
                'posologie_adulte': '1 comprimé matin et soir',
                'posologie_enfant': 'Selon poids corporel',
                'duree_traitement_standard': '7 jours',
                'contre_indications': 'Allergie aux pénicillines, antécédent d\'ictère',
                'precautions': 'Surveillance hépatique si traitement prolongé',
                'interactions': 'Méthotrexate, warfarine',
                'conservation': 'Température ambiante',
                'prescription_requise': True,
                'remboursable': True,
                'actif': True
            },
            {
                'nom_commercial': 'Seretide',
                'nom_generique': 'Salmétérol/Fluticasone',
                'principe_actif': 'Salmétérol + Propionate de fluticasone',
                'dosage': '25µg/125µg',
                'forme': 'Aérosol doseur',
                'categorie': 'CORTICOIDE_BRONCHODILATATEUR',
                'posologie_adulte': '2 bouffées matin et soir',
                'posologie_enfant': '1 bouffée matin et soir (> 4 ans)',
                'duree_traitement_standard': 'Traitement de fond',
                'contre_indications': 'Hypersensibilité aux composants',
                'precautions': 'Rincer la bouche après utilisation',
                'interactions': 'Kétoconazole (augmentation exposition)',
                'conservation': 'Température ambiante, protéger du gel',
                'prescription_requise': True,
                'remboursable': True,
                'actif': True
            }
        ]

        for produit_data in produits:
            produit, created = ProduitPharmaceutique.objects.get_or_create(
                nom_commercial=produit_data['nom_commercial'],
                dosage=produit_data['dosage'],
                defaults=produit_data
            )
            if created:
                self.stdout.write(f'  Créé: {produit.nom_commercial} {produit.dosage}')

    def charger_actes_medicaux(self):
        """Charger les actes médicaux de test"""
        actes = [
            {
                'nom': 'Numération Formule Sanguine',
                'code': 'B020',
                'categorie': 'BIOLOGIE',
                'type_acte': 'ANALYSE',
                'description': 'Analyse complète des cellules sanguines',
                'preparation_requise': 'Aucune préparation particulière',
                'duree_estimee': '15 minutes',
                'jeune_requis': False,
                'duree_jeune': 0,
                'urgence_possible': True,
                'delai_resultat': '2 heures',
                'prix_indicatif': 15.50,
                'remboursable': True,
                'actif': True
            },
            {
                'nom': 'Glycémie à jeun',
                'code': 'B035',
                'categorie': 'BIOLOGIE',
                'type_acte': 'ANALYSE',
                'description': 'Dosage du glucose sanguin à jeun',
                'preparation_requise': 'Jeûne de 12 heures minimum',
                'duree_estimee': '10 minutes',
                'jeune_requis': True,
                'duree_jeune': 12,
                'urgence_possible': False,
                'delai_resultat': '1 heure',
                'prix_indicatif': 8.20,
                'remboursable': True,
                'actif': True
            },
            {
                'nom': 'Radiographie thoracique face',
                'code': 'ZBQK001',
                'categorie': 'IMAGERIE',
                'type_acte': 'RADIOLOGIE',
                'description': 'Radiographie du thorax de face',
                'preparation_requise': 'Retirer bijoux et vêtements métalliques',
                'duree_estimee': '20 minutes',
                'jeune_requis': False,
                'duree_jeune': 0,
                'urgence_possible': True,
                'delai_resultat': '1 heure',
                'prix_indicatif': 35.00,
                'remboursable': True,
                'actif': True
            },
            {
                'nom': 'Échographie abdominale',
                'code': 'ZCQH001',
                'categorie': 'IMAGERIE',
                'type_acte': 'ECHOGRAPHIE',
                'description': 'Échographie de l\'abdomen complet',
                'preparation_requise': 'Jeûne de 6 heures, vessie pleine',
                'duree_estimee': '30 minutes',
                'jeune_requis': True,
                'duree_jeune': 6,
                'urgence_possible': False,
                'delai_resultat': '30 minutes',
                'prix_indicatif': 75.00,
                'remboursable': True,
                'actif': True
            },
            {
                'nom': 'Électrocardiogramme',
                'code': 'DEQP003',
                'categorie': 'CARDIOLOGIE',
                'type_acte': 'EXPLORATION',
                'description': 'Enregistrement de l\'activité électrique du cœur',
                'preparation_requise': 'Aucune préparation particulière',
                'duree_estimee': '15 minutes',
                'jeune_requis': False,
                'duree_jeune': 0,
                'urgence_possible': True,
                'delai_resultat': 'Immédiat',
                'prix_indicatif': 25.00,
                'remboursable': True,
                'actif': True
            },
            {
                'nom': 'Créatininémie',
                'code': 'B045',
                'categorie': 'BIOLOGIE',
                'type_acte': 'ANALYSE',
                'description': 'Dosage de la créatinine sérique',
                'preparation_requise': 'Aucune préparation particulière',
                'duree_estimee': '10 minutes',
                'jeune_requis': False,
                'duree_jeune': 0,
                'urgence_possible': True,
                'delai_resultat': '1 heure',
                'prix_indicatif': 6.80,
                'remboursable': True,
                'actif': True
            },
            {
                'nom': 'Scanner thoracique sans injection',
                'code': 'ZBQH001',
                'categorie': 'IMAGERIE',
                'type_acte': 'SCANNER',
                'description': 'Tomodensitométrie du thorax sans produit de contraste',
                'preparation_requise': 'Retirer objets métalliques',
                'duree_estimee': '20 minutes',
                'jeune_requis': False,
                'duree_jeune': 0,
                'urgence_possible': True,
                'delai_resultat': '2 heures',
                'prix_indicatif': 120.00,
                'remboursable': True,
                'actif': True
            },
            {
                'nom': 'Bilan lipidique complet',
                'code': 'B055',
                'categorie': 'BIOLOGIE',
                'type_acte': 'ANALYSE',
                'description': 'Cholestérol total, HDL, LDL, triglycérides',
                'preparation_requise': 'Jeûne de 12 heures minimum',
                'duree_estimee': '15 minutes',
                'jeune_requis': True,
                'duree_jeune': 12,
                'urgence_possible': False,
                'delai_resultat': '2 heures',
                'prix_indicatif': 25.60,
                'remboursable': True,
                'actif': True
            },
            {
                'nom': 'IRM cérébrale sans injection',
                'code': 'AAQM001',
                'categorie': 'IMAGERIE',
                'type_acte': 'IRM',
                'description': 'Imagerie par résonance magnétique du cerveau',
                'preparation_requise': 'Questionnaire de sécurité IRM, retirer objets métalliques',
                'duree_estimee': '45 minutes',
                'jeune_requis': False,
                'duree_jeune': 0,
                'urgence_possible': False,
                'delai_resultat': '24 heures',
                'prix_indicatif': 350.00,
                'remboursable': True,
                'actif': True
            },
            {
                'nom': 'Spirométrie',
                'code': 'GLQP002',
                'categorie': 'PNEUMOLOGIE',
                'type_acte': 'EXPLORATION',
                'description': 'Exploration fonctionnelle respiratoire',
                'preparation_requise': 'Arrêt bronchodilatateurs selon prescription',
                'duree_estimee': '30 minutes',
                'jeune_requis': False,
                'duree_jeune': 0,
                'urgence_possible': False,
                'delai_resultat': 'Immédiat',
                'prix_indicatif': 45.00,
                'remboursable': True,
                'actif': True
            }
        ]

        for acte_data in actes:
            acte, created = ActeMedical.objects.get_or_create(
                code=acte_data['code'],
                defaults=acte_data
            )
            if created:
                self.stdout.write(f'  Créé: {acte.nom} ({acte.code})')

# Script d'initialisation rapide
def initialiser_donnees_test():
    """Fonction utilitaire pour initialiser rapidement les données de test"""
    from django.core.management import call_command
    call_command('charger_donnees_test')

# Données JSON pour import via API
PRODUITS_JSON = [
    {
        "nom_commercial": "Paracétamol Biogaran",
        "nom_generique": "Paracétamol",
        "dosage": "500mg",
        "forme": "Comprimé",
        "categorie": "ANALGESIQUE"
    },
    {
        "nom_commercial": "Amoxicilline Sandoz",
        "nom_generique": "Amoxicilline",
        "dosage": "1g",
        "forme": "Comprimé pelliculé",
        "categorie": "ANTIBIOTIQUE"
    }
]

ACTES_JSON = [
    {
        "nom": "Numération Formule Sanguine",
        "code": "B020",
        "categorie": "BIOLOGIE",
        "type_acte": "ANALYSE"
    },
    {
        "nom": "Radiographie thoracique face",
        "code": "ZBQK001",
        "categorie": "IMAGERIE",
        "type_acte": "RADIOLOGIE"
    }
]

