    import os
    import sys
    import django
    from django.core.management.base import BaseCommand
    from lobiko.models import ProduitPharmaceutique, ActeMedical

    class Command(BaseCommand):
        help = 'Charge les données de test pour les produits pharmaceutiques et actes médicaux'

        def handle(self, *args, **options):
            self.stdout.write('Chargement des produits pharmaceutiques...')
            self.charger_produits_pharmaceutiques()
            
            self.stdout.write('Chargement des actes médicaux...')
            self.charger_actes_medicaux()
            
            self.stdout.write(self.style.SUCCESS('✅ Données de test chargées avec succès !'))

        def creer_produits_pharmaceutiques():
        """Créer des produits pharmaceutiques de test"""
        
        produits = [
            # Antibiotiques
            {
                'nom_commercial': 'Amoxicilline',
                'nom_generique': 'Amoxicilline',
                'dosage': '500mg',
                'forme': 'Gélule',
                'laboratoire': 'Biogaran',
                'posologie_adulte': '1 gélule 3 fois par jour',
                'duree_traitement_standard': '7 jours',
                'prescription_obligatoire': True
            },
            {
                'nom_commercial': 'Augmentin',
                'nom_generique': 'Amoxicilline + Acide clavulanique',
                'dosage': '1g/125mg',
                'forme': 'Comprimé pelliculé',
                'laboratoire': 'GSK',
                'posologie_adulte': '1 comprimé 2 fois par jour',
                'duree_traitement_standard': '7 jours',
                'prescription_obligatoire': True
            },
            {
                'nom_commercial': 'Azithromycine',
                'nom_generique': 'Azithromycine',
                'dosage': '250mg',
                'forme': 'Comprimé',
                'laboratoire': 'Sandoz',
                'posologie_adulte': '1 comprimé par jour',
                'duree_traitement_standard': '3 jours',
                'prescription_obligatoire': True
            },
            
            # Anti-inflammatoires
            {
                'nom_commercial': 'Ibuprofène',
                'nom_generique': 'Ibuprofène',
                'dosage': '400mg',
                'forme': 'Comprimé pelliculé',
                'laboratoire': 'Biogaran',
                'posologie_adulte': '1 comprimé 3 fois par jour',
                'duree_traitement_standard': '5 jours',
                'prescription_obligatoire': False
            },
            {
                'nom_commercial': 'Voltarène',
                'nom_generique': 'Diclofénac',
                'dosage': '50mg',
                'forme': 'Comprimé gastro-résistant',
                'laboratoire': 'Novartis',
                'posologie_adulte': '1 comprimé 2 fois par jour',
                'duree_traitement_standard': '7 jours',
                'prescription_obligatoire': True
            },
            
            # Antalgiques
            {
                'nom_commercial': 'Paracétamol',
                'nom_generique': 'Paracétamol',
                'dosage': '1000mg',
                'forme': 'Comprimé effervescent',
                'laboratoire': 'Doliprane',
                'posologie_adulte': '1 comprimé 3 fois par jour',
                'duree_traitement_standard': 'Selon besoin',
                'prescription_obligatoire': False
            },
            {
                'nom_commercial': 'Tramadol',
                'nom_generique': 'Tramadol',
                'dosage': '50mg',
                'forme': 'Gélule',
                'laboratoire': 'Mylan',
                'posologie_adulte': '1 gélule 3 fois par jour',
                'duree_traitement_standard': '5 jours',
                'prescription_obligatoire': True
            },
            
            # Antispasmodiques
            {
                'nom_commercial': 'Spasfon',
                'nom_generique': 'Phloroglucinol',
                'dosage': '80mg',
                'forme': 'Comprimé pelliculé',
                'laboratoire': 'Teva',
                'posologie_adulte': '2 comprimés 3 fois par jour',
                'duree_traitement_standard': '3 jours',
                'prescription_obligatoire': False
            },
            
            # Antihistaminiques
            {
                'nom_commercial': 'Cétirizine',
                'nom_generique': 'Cétirizine',
                'dosage': '10mg',
                'forme': 'Comprimé pelliculé',
                'laboratoire': 'Biogaran',
                'posologie_adulte': '1 comprimé par jour',
                'duree_traitement_standard': '7 jours',
                'prescription_obligatoire': False
            },
            
            # Antitussifs
            {
                'nom_commercial': 'Toplexil',
                'nom_generique': 'Oxomémazine',
                'dosage': '0,33mg/ml',
                'forme': 'Sirop',
                'laboratoire': 'Sanofi',
                'posologie_adulte': '15ml 3 fois par jour',
                'duree_traitement_standard': '5 jours',
                'prescription_obligatoire': True
            },
            
            # Corticoïdes
            {
                'nom_commercial': 'Prednisolone',
                'nom_generique': 'Prednisolone',
                'dosage': '20mg',
                'forme': 'Comprimé orodispersible',
                'laboratoire': 'Mylan',
                'posologie_adulte': '1 comprimé par jour',
                'duree_traitement_standard': '5 jours',
                'prescription_obligatoire': True
            },
            
            # Antiacides
            {
                'nom_commercial': 'Maalox',
                'nom_generique': 'Hydroxyde d\'aluminium + Hydroxyde de magnésium',
                'dosage': '400mg/400mg',
                'forme': 'Comprimé à croquer',
                'laboratoire': 'Sanofi',
                'posologie_adulte': '1 à 2 comprimés après les repas',
                'duree_traitement_standard': 'Selon besoin',
                'prescription_obligatoire': False
            },
            
            # Vitamines
            {
                'nom_commercial': 'Vitamine D3',
                'nom_generique': 'Cholécalciférol',
                'dosage': '100000 UI',
                'forme': 'Solution buvable',
                'laboratoire': 'UPSA',
                'posologie_adulte': '1 ampoule tous les 3 mois',
                'duree_traitement_standard': 'Selon prescription',
                'prescription_obligatoire': True
            },
            
            # Antidiabétiques
            {
                'nom_commercial': 'Metformine',
                'nom_generique': 'Metformine',
                'dosage': '850mg',
                'forme': 'Comprimé pelliculé',
                'laboratoire': 'Biogaran',
                'posologie_adulte': '1 comprimé 2 fois par jour',
                'duree_traitement_standard': 'Traitement au long cours',
                'prescription_obligatoire': True
            },
            
            # Antihypertenseurs
            {
                'nom_commercial': 'Amlodipine',
                'nom_generique': 'Amlodipine',
                'dosage': '5mg',
                'forme': 'Comprimé',
                'laboratoire': 'Pfizer',
                'posologie_adulte': '1 comprimé par jour',
                'duree_traitement_standard': 'Traitement au long cours',
                'prescription_obligatoire': True
            }
        ]
        
        for produit_data in produits:
            produit, created = ProduitPharmaceutique.objects.get_or_create(
                nom_commercial=produit_data['nom_commercial'],
                dosage=produit_data['dosage'],
                defaults=produit_data
            )
            if created:
                print(f"Produit créé: {produit.nom_commercial} {produit.dosage}")

    def creer_actes_medicaux():
        """Créer des actes médicaux de test"""
        
        actes = [
            # Biologie
            {
                'nom': 'Numération Formule Sanguine (NFS)',
                'code': 'B0101',
                'categorie': 'BIOLOGIE',
                'description': 'Analyse complète des cellules sanguines',
                'preparation_requise': 'Aucune préparation particulière',
                'duree_estimee': '15 minutes'
            },
            {
                'nom': 'Bilan lipidique',
                'code': 'B0201',
                'categorie': 'BIOLOGIE',
                'description': 'Dosage du cholestérol total, HDL, LDL et triglycérides',
                'preparation_requise': 'Jeûne de 12 heures',
                'duree_estimee': '15 minutes'
            },
            {
                'nom': 'Glycémie à jeun',
                'code': 'B0301',
                'categorie': 'BIOLOGIE',
                'description': 'Dosage du glucose sanguin',
                'preparation_requise': 'Jeûne de 8 heures minimum',
                'duree_estimee': '10 minutes'
            },
            {
                'nom': 'Créatininémie',
                'code': 'B0401',
                'categorie': 'BIOLOGIE',
                'description': 'Évaluation de la fonction rénale',
                'preparation_requise': 'Aucune préparation particulière',
                'duree_estimee': '15 minutes'
            },
            {
                'nom': 'Transaminases (ALAT, ASAT)',
                'code': 'B0501',
                'categorie': 'BIOLOGIE',
                'description': 'Évaluation de la fonction hépatique',
                'preparation_requise': 'Aucune préparation particulière',
                'duree_estimee': '15 minutes'
            },
            {
                'nom': 'CRP (Protéine C-réactive)',
                'code': 'B0601',
                'categorie': 'BIOLOGIE',
                'description': 'Marqueur d\'inflammation',
                'preparation_requise': 'Aucune préparation particulière',
                'duree_estimee': '15 minutes'
            },
            {
                'nom': 'TSH (Hormone thyréostimulante)',
                'code': 'B0701',
                'categorie': 'ENDOCRINOLOGIE',
                'description': 'Évaluation de la fonction thyroïdienne',
                'preparation_requise': 'Aucune préparation particulière',
                'duree_estimee': '15 minutes'
            },
            
            # Imagerie
            {
                'nom': 'Radiographie thoracique',
                'code': 'I0101',
                'categorie': 'IMAGERIE',
                'description': 'Examen radiologique du thorax',
                'preparation_requise': 'Retirer bijoux et objets métalliques',
                'duree_estimee': '15 minutes'
            },
            {
                'nom': 'Échographie abdominale',
                'code': 'I0201',
                'categorie': 'IMAGERIE',
                'description': 'Examen échographique de l\'abdomen',
                'preparation_requise': 'Jeûne de 6 heures, vessie pleine',
                'duree_estimee': '30 minutes'
            },
            {
                'nom': 'Scanner thoracique',
                'code': 'I0301',
                'categorie': 'IMAGERIE',
                'description': 'Tomodensitométrie du thorax',
                'preparation_requise': 'Jeûne de 4 heures si injection de produit de contraste',
                'duree_estimee': '20 minutes'
            },
            {
                'nom': 'IRM cérébrale',
                'code': 'I0401',
                'categorie': 'NEUROLOGIE',
                'description': 'Imagerie par résonance magnétique du cerveau',
                'preparation_requise': 'Retirer tous objets métalliques, questionnaire de sécurité',
                'duree_estimee': '45 minutes'
            },
            {
                'nom': 'Mammographie',
                'code': 'I0501',
                'categorie': 'GYNECOLOGIE',
                'description': 'Radiographie des seins',
                'preparation_requise': 'Éviter déodorants et crèmes, prévoir entre J8 et J12 du cycle',
                'duree_estimee': '20 minutes'
            },
            
            # Cardiologie
            {
                'nom': 'Électrocardiogramme (ECG)',
                'code': 'C0101',
                'categorie': 'CARDIOLOGIE',
                'description': 'Enregistrement de l\'activité électrique du cœur',
                'preparation_requise': 'Aucune préparation particulière',
                'duree_estimee': '15 minutes'
            },
            {
                'nom': 'Échocardiographie',
                'code': 'C0201',
                'categorie': 'CARDIOLOGIE',
                'description': 'Échographie du cœur',
                'preparation_requise': 'Aucune préparation particulière',
                'duree_estimee': '30 minutes'
            },
            {
                'nom': 'Holter ECG 24h',
                'code': 'C0301',
                'categorie': 'CARDIOLOGIE',
                'description': 'Enregistrement continu de l\'ECG pendant 24 heures',
                'preparation_requise': 'Douche avant la pose, éviter les activités aquatiques',
                'duree_estimee': '24 heures'
            },
            
            # Pneumologie
            {
                'nom': 'Spirométrie',
                'code': 'P0101',
                'categorie': 'PNEUMOLOGIE',
                'description': 'Exploration fonctionnelle respiratoire',
                'preparation_requise': 'Éviter bronchodilatateurs 6h avant, repas léger',
                'duree_estimee': '30 minutes'
            },
            
            # Gastroentérologie
            {
                'nom': 'Fibroscopie gastrique',
                'code': 'G0101',
                'categorie': 'GASTROENTEROLOGIE',
                'description': 'Endoscopie de l\'estomac',
                'preparation_requise': 'Jeûne strict de 12 heures',
                'duree_estimee': '20 minutes'
            },
            {
                'nom': 'Coloscopie',
                'code': 'G0201',
                'categorie': 'GASTROENTEROLOGIE',
                'description': 'Endoscopie du côlon',
                'preparation_requise': 'Régime sans résidus 3 jours avant, préparation colique',
                'duree_estimee': '45 minutes'
            },
            
            # Urologie
            {
                'nom': 'Échographie vésico-prostatique',
                'code': 'U0101',
                'categorie': 'UROLOGIE',
                'description': 'Échographie de la vessie et de la prostate',
                'preparation_requise': 'Vessie pleine (boire 1L d\'eau 1h avant)',
                'duree_estimee': '20 minutes'
            },
            
            # Ophtalmologie
            {
                'nom': 'Fond d\'œil',
                'code': 'O0101',
                'categorie': 'OPHTALMOLOGIE',
                'description': 'Examen du fond de l\'œil',
                'preparation_requise': 'Dilatation pupillaire, prévoir accompagnant',
                'duree_estimee': '30 minutes'
            },
            
            # ORL
            {
                'nom': 'Audiométrie',
                'code': 'R0101',
                'categorie': 'ORL',
                'description': 'Test de l\'audition',
                'preparation_requise': 'Nettoyer les oreilles, éviter exposition au bruit',
                'duree_estimee': '30 minutes'
            },
            
            # Dermatologie
            {
                'nom': 'Dermoscopie',
                'code': 'D0101',
                'categorie': 'DERMATOLOGIE',
                'description': 'Examen dermatoscopique des lésions cutanées',
                'preparation_requise': 'Peau propre, éviter crèmes et maquillage',
                'duree_estimee': '20 minutes'
            }
        ]
        
        for acte_data in actes:
            acte, created = ActeMedical.objects.get_or_create(
                code=acte_data['code'],
                defaults=acte_data
            )
            if created:
                print(f"Acte créé: {acte.nom} ({acte.code})")

    def main():
        """Fonction principale pour créer toutes les données de test"""
        print("Création des produits pharmaceutiques...")
        creer_produits_pharmaceutiques()
        
        print("\nCréation des actes médicaux...")
        creer_actes_medicaux()
        
        print("\nDonnées de test créées avec succès!")

    if __name__ == "__main__":
        main()
