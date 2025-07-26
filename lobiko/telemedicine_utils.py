"""
Utilitaires pour la gestion de la télémédecine dans l'application Lobiko
"""
import os
import io
import logging
import qrcode
from datetime import datetime
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import hashlib
import uuid

logger = logging.getLogger(__name__)

class GenerateurPDFOrdonnance:
    """
    Générateur PDF robuste pour les ordonnances médicales
    Corrige les erreurs de génération et de stockage
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Configuration des styles personnalisés"""
        # Style pour le titre principal
        self.styles.add(ParagraphStyle(
            name='TitrePrincipal',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Style pour les sous-titres
        self.styles.add(ParagraphStyle(
            name='SousTitre',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkgreen
        ))
        
        # Style pour le contenu
        self.styles.add(ParagraphStyle(
            name='ContenuNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6
        ))

    def creer_dossiers_necessaires(self):
        """
        Créer tous les dossiers nécessaires pour le stockage
        Corrige le problème de dossiers manquants
        """
        dossiers_requis = [
            'prescriptions',
            'prescriptions/ordonnances',
            'prescriptions/bons_examens',
            'qr_codes'
        ]
        
        for dossier in dossiers_requis:
            chemin_complet = os.path.join(settings.MEDIA_ROOT, dossier)
            try:
                os.makedirs(chemin_complet, exist_ok=True)
                logger.info(f"✅ Dossier créé/vérifié: {chemin_complet}")
            except Exception as e:
                logger.error(f"❌ Erreur création dossier {chemin_complet}: {e}")
                raise

    def generer_qr_code(self, data, nom_fichier):
        """
        Génère un QR code et le sauvegarde
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Créer l'image QR
            img_qr = qr.make_image(fill_color="black", back_color="white")
            
            # Sauvegarder en mémoire d'abord
            buffer = io.BytesIO()
            img_qr.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Chemin de sauvegarde
            chemin_qr = os.path.join(settings.MEDIA_ROOT, 'qr_codes', f"{nom_fichier}.png")
            
            # Sauvegarder sur le disque
            with open(chemin_qr, 'wb') as f:
                f.write(buffer.getvalue())
            
            logger.info(f"✅ QR code généré: {chemin_qr}")
            return chemin_qr
            
        except Exception as e:
            logger.error(f"❌ Erreur génération QR code: {e}")
            return None

    def generer_pdf_ordonnance(self, donnees_ordonnance):
        """
        Génère un PDF d'ordonnance médicale
        Version corrigée qui gère tous les cas d'erreur
        """
        try:
            # 1. Créer les dossiers nécessaires
            self.creer_dossiers_necessaires()
            
            # 2. Préparer les données
            numero = donnees_ordonnance.get('numero', f'ORD_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            patient = donnees_ordonnance.get('patient', {})
            medecin = donnees_ordonnance.get('medecin', {})
            medicaments = donnees_ordonnance.get('medicaments', [])
            
            # 3. Chemin du fichier PDF
            nom_fichier = f"{numero}.pdf"
            chemin_pdf = os.path.join(settings.MEDIA_ROOT, 'prescriptions', 'ordonnances', nom_fichier)
            
            # 4. Générer le QR code
            donnees_qr = {
                'numero': numero,
                'patient': f"{patient.get('prenom', '')} {patient.get('nom', '')}",
                'medecin': f"Dr {medecin.get('nom', '')}",
                'date': datetime.now().isoformat(),
                'hash': hashlib.md5(f"{numero}{datetime.now()}".encode()).hexdigest()[:8]
            }
            
            chemin_qr = self.generer_qr_code(str(donnees_qr), f"qr_ord_{numero}")
            
            # 5. Créer le PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, 
                                  topMargin=2*cm, bottomMargin=2*cm)
            
            # Contenu du PDF
            story = []
            
            # En-tête
            story.append(Paragraph("ORDONNANCE MÉDICALE", self.styles['TitrePrincipal']))
            story.append(Spacer(1, 0.5*cm))
            
            # Informations de l'ordonnance
            info_table_data = [
                ['Numéro d\'ordonnance:', numero],
                ['Date d\'émission:', datetime.now().strftime('%d/%m/%Y à %H:%M')],
                ['Médecin prescripteur:', f"Dr {medecin.get('nom', '')} {medecin.get('prenom', '')}"],
                ['Patient:', f"{patient.get('prenom', '')} {patient.get('nom', '')}"],
                ['Date de naissance:', patient.get('date_naissance', 'Non renseignée')],
            ]
            
            info_table = Table(info_table_data, colWidths=[5*cm, 10*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 1*cm))
            
            # Médicaments prescrits
            story.append(Paragraph("MÉDICAMENTS PRESCRITS", self.styles['SousTitre']))
            
            for i, medicament in enumerate(medicaments, 1):
                story.append(Paragraph(f"<b>{i}. {medicament.get('nom', 'Médicament non spécifié')}</b>", 
                                     self.styles['ContenuNormal']))
                story.append(Paragraph(f"Posologie: {medicament.get('posologie', 'Non spécifiée')}", 
                                     self.styles['ContenuNormal']))
                story.append(Paragraph(f"Durée du traitement: {medicament.get('duree_traitement', 'Non spécifiée')}", 
                                     self.styles['ContenuNormal']))
                
                if medicament.get('instructions'):
                    story.append(Paragraph(f"Instructions: {medicament.get('instructions')}", 
                                         self.styles['ContenuNormal']))
                
                story.append(Spacer(1, 0.3*cm))
            
            # Instructions générales
            if donnees_ordonnance.get('instructions_generales'):
                story.append(Paragraph("INSTRUCTIONS GÉNÉRALES", self.styles['SousTitre']))
                story.append(Paragraph(donnees_ordonnance.get('instructions_generales'), 
                                     self.styles['ContenuNormal']))
                story.append(Spacer(1, 0.5*cm))
            
            # QR Code (si généré avec succès)
            if chemin_qr and os.path.exists(chemin_qr):
                try:
                    story.append(Paragraph("Code de vérification:", self.styles['SousTitre']))
                    qr_image = Image(chemin_qr, width=3*cm, height=3*cm)
                    story.append(qr_image)
                except Exception as e:
                    logger.warning(f"Impossible d'ajouter le QR code au PDF: {e}")
            
            # Signature
            story.append(Spacer(1, 1*cm))
            signature_data = [
                ['Date et signature du médecin:', ''],
                ['', ''],
                ['', f"Dr {medecin.get('nom', '')} {medecin.get('prenom', '')}"]
            ]
            
            signature_table = Table(signature_data, colWidths=[8*cm, 7*cm])
            signature_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            
            story.append(signature_table)
            
            # 6. Construire le PDF
            doc.build(story)
            
            # 7. Sauvegarder le fichier
            buffer.seek(0)
            with open(chemin_pdf, 'wb') as f:
                f.write(buffer.getvalue())
            
            logger.info(f"✅ PDF ordonnance généré avec succès: {chemin_pdf}")
            
            # 8. Retourner les informations
            return {
                'success': True,
                'chemin_pdf': chemin_pdf,
                'nom_fichier': nom_fichier,
                'numero': numero,
                'url_pdf': f"{settings.MEDIA_URL}prescriptions/ordonnances/{nom_fichier}",
                'chemin_qr': chemin_qr,
                'taille_fichier': os.path.getsize(chemin_pdf) if os.path.exists(chemin_pdf) else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur génération PDF ordonnance: {e}")
            return {
                'success': False,
                'error': str(e),
                'numero': donnees_ordonnance.get('numero', 'UNKNOWN')
            }

    def generer_pdf_bon_examen(self, donnees_bon):
        """
        Génère un PDF de bon d'examens médicaux
        """
        try:
            # Logique similaire à generer_pdf_ordonnance
            # mais adaptée pour les bons d'examens
            
            self.creer_dossiers_necessaires()
            
            numero = donnees_bon.get('numero', f'BON_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            patient = donnees_bon.get('patient', {})
            medecin = donnees_bon.get('medecin', {})
            examens = donnees_bon.get('examens', [])
            
            nom_fichier = f"{numero}.pdf"
            chemin_pdf = os.path.join(settings.MEDIA_ROOT, 'prescriptions', 'bons_examens', nom_fichier)
            
            # Générer QR code
            donnees_qr = {
                'numero': numero,
                'type': 'bon_examen',
                'patient': f"{patient.get('prenom', '')} {patient.get('nom', '')}",
                'medecin': f"Dr {medecin.get('nom', '')}",
                'date': datetime.now().isoformat(),
                'hash': hashlib.md5(f"{numero}{datetime.now()}".encode()).hexdigest()[:8]
            }
            
            chemin_qr = self.generer_qr_code(str(donnees_qr), f"qr_bon_{numero}")
            
            # Créer le PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, 
                                  topMargin=2*cm, bottomMargin=2*cm)
            
            story = []
            
            # En-tête
            story.append(Paragraph("BON D'EXAMENS MÉDICAUX", self.styles['TitrePrincipal']))
            story.append(Spacer(1, 0.5*cm))
            
            # Informations du bon
            info_table_data = [
                ['Numéro du bon:', numero],
                ['Date d\'émission:', datetime.now().strftime('%d/%m/%Y à %H:%M')],
                ['Médecin prescripteur:', f"Dr {medecin.get('nom', '')} {medecin.get('prenom', '')}"],
                ['Patient:', f"{patient.get('prenom', '')} {patient.get('nom', '')}"],
                ['Priorité:', donnees_bon.get('priorite', 'Normal')],
            ]
            
            info_table = Table(info_table_data, colWidths=[5*cm, 10*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 1*cm))
            
            # Examens prescrits
            story.append(Paragraph("EXAMENS PRESCRITS", self.styles['SousTitre']))
            
            for i, examen in enumerate(examens, 1):
                story.append(Paragraph(f"<b>{i}. {examen.get('nom', 'Examen non spécifié')}</b>", 
                                     self.styles['ContenuNormal']))
                if examen.get('localisation'):
                    story.append(Paragraph(f"Localisation: {examen.get('localisation')}", 
                                         self.styles['ContenuNormal']))
                if examen.get('instructions'):
                    story.append(Paragraph(f"Instructions: {examen.get('instructions')}", 
                                         self.styles['ContenuNormal']))
                story.append(Spacer(1, 0.3*cm))
            
            # QR Code
            if chemin_qr and os.path.exists(chemin_qr):
                try:
                    story.append(Paragraph("Code de vérification:", self.styles['SousTitre']))
                    qr_image = Image(chemin_qr, width=3*cm, height=3*cm)
                    story.append(qr_image)
                except Exception as e:
                    logger.warning(f"Impossible d'ajouter le QR code au PDF: {e}")
            
            # Construire et sauvegarder
            doc.build(story)
            buffer.seek(0)
            
            with open(chemin_pdf, 'wb') as f:
                f.write(buffer.getvalue())
            
            logger.info(f"✅ PDF bon d'examens généré avec succès: {chemin_pdf}")
            
            return {
                'success': True,
                'chemin_pdf': chemin_pdf,
                'nom_fichier': nom_fichier,
                'numero': numero,
                'url_pdf': f"{settings.MEDIA_URL}prescriptions/bons_examens/{nom_fichier}",
                'chemin_qr': chemin_qr,
                'taille_fichier': os.path.getsize(chemin_pdf) if os.path.exists(chemin_pdf) else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur génération PDF bon d'examens: {e}")
            return {
                'success': False,
                'error': str(e),
                'numero': donnees_bon.get('numero', 'UNKNOWN')
            }


# 🔧 Fonction de stockage robuste (corrige l'erreur S3)
def sauvegarder_document_securise(chemin_local, nom_fichier, type_document='ordonnance'):
    """
    Sauvegarde un document de manière sécurisée
    Corrige l'erreur S3: expected string or bytes-like object
    """
    try:
        # 1. Vérifier que le fichier local existe
        if not os.path.exists(chemin_local):
            raise FileNotFoundError(f"Fichier local introuvable: {chemin_local}")
        
        # 2. Lire le fichier en mode binaire (corrige l'erreur S3)
        with open(chemin_local, 'rb') as f:
            contenu_fichier = f.read()
        
        # 3. Tentative de sauvegarde S3 (si configuré)
        url_s3 = None
        try:
            if hasattr(settings, 'AWS_STORAGE_BUCKET_NAME') and settings.AWS_STORAGE_BUCKET_NAME:
                import boto3
                from botocore.exceptions import ClientError
                
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
                )
                
                # Chemin S3
                chemin_s3 = f"prescriptions/{type_document}s/{nom_fichier}"
                
                # Upload vers S3 avec le contenu binaire (corrige l'erreur)
                s3_client.put_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=chemin_s3,
                    Body=contenu_fichier,  # ✅ Contenu binaire au lieu d'objet
                    ContentType='application/pdf',
                    ContentDisposition=f'attachment; filename="{nom_fichier}"'
                )
                
                url_s3 = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{chemin_s3}"
                logger.info(f"✅ Document uploadé vers S3: {url_s3}")
                
        except Exception as e:
            logger.warning(f"⚠️ Échec upload S3 (fallback local): {e}")
        
        # 4. URL locale de fallback
        url_locale = f"{settings.MEDIA_URL}prescriptions/{type_document}s/{nom_fichier}"
        
        return {
            'success': True,
            'url_locale': url_locale,
            'url_s3': url_s3,
            'url_finale': url_s3 if url_s3 else url_locale,
            'taille': len(contenu_fichier)
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde document: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# 🔧 Fonctions utilitaires simplifiées
def generer_ordonnance_complete(donnees):
    """
    Fonction principale pour générer une ordonnance complète
    """
    generateur = GenerateurPDFOrdonnance()
    resultat_pdf = generateur.generer_pdf_ordonnance(donnees)
    
    if resultat_pdf['success']:
        # Sauvegarder de manière sécurisée
        resultat_stockage = sauvegarder_document_securise(
            resultat_pdf['chemin_pdf'],
            resultat_pdf['nom_fichier'],
            'ordonnance'
        )
        
        # Combiner les résultats
        resultat_pdf.update(resultat_stockage)
    
    return resultat_pdf


def generer_bon_examen_complet(donnees):
    """
    Fonction principale pour générer un bon d'examens complet
    """
    generateur = GenerateurPDFOrdonnance()
    resultat_pdf = generateur.generer_pdf_bon_examen(donnees)
    
    if resultat_pdf['success']:
        # Sauvegarder de manière sécurisée
        resultat_stockage = sauvegarder_document_securise(
            resultat_pdf['chemin_pdf'],
            resultat_pdf['nom_fichier'],
            'bon_examen'
        )
        
        # Combiner les résultats
        resultat_pdf.update(resultat_stockage)
    
    return resultat_pdf


# 🔧 Test de la génération
def tester_generation_pdf():
    """
    Fonction de test pour vérifier la génération PDF
    """
    print("🧪 Test de génération PDF...")
    
    # Données de test
    donnees_test = {
        'numero': 'TEST_001',
        'patient': {
            'nom': 'Dupont',
            'prenom': 'Jean',
            'date_naissance': '01/01/1980'
        },
        'medecin': {
            'nom': 'Martin',
            'prenom': 'Pierre'
        },
        'medicaments': [
            {
                'nom': 'Paracétamol 500mg',
                'posologie': '1 comprimé 3 fois par jour',
                'duree_traitement': '7 jours',
                'instructions': 'À prendre avec un verre d\'eau'
            }
        ],
        'instructions_generales': 'Repos recommandé pendant la durée du traitement.'
    }
    
    # Test de génération
    resultat = generer_ordonnance_complete(donnees_test)
    
    if resultat['success']:
        print(f"✅ Test réussi - PDF généré: {resultat['chemin_pdf']}")
        print(f"📄 Taille: {resultat['taille_fichier']} bytes")
        print(f"🌐 URL: {resultat['url_pdf']}")
    else:
        print(f"❌ Test échoué: {resultat['error']}")
    
    return resultat


if __name__ == "__main__":
    print("Générateur PDF Ordonnances - Version Corrigée")
    print("Ce module corrige les erreurs de génération et de stockage PDF")
    
    # Décommenter pour tester
    # tester_generation_pdf()



# 🔧 CORRECTION: Fonction manquante pour générer les PDFs d'ordonnances
def generer_pdf_ordonnance_detaille(ordonnance):
    """
    Fonction de pont entre la vue Django et la classe GenerateurPDFOrdonnance
    Extrait les données de l'objet Ordonnance et génère le PDF
    
    Args:
        ordonnance: Instance du modèle Ordonnance avec ses médicaments liés
        
    Returns:
        dict: Résultat de la génération PDF avec success/error
    """
    try:
        logger.info(f"🔄 Génération PDF pour ordonnance {ordonnance.numero_unique}")
        
        # 1. Extraire les médicaments liés à l'ordonnance
        prescriptions_medicaments = ordonnance.prescriptions.all()
        logger.info(f"📊 Nombre de médicaments trouvés: {prescriptions_medicaments.count()}")
        
        medicaments_data = []
        for prescription in prescriptions_medicaments:
            medicament_info = {
                'nom': f"{prescription.produit.nom_commercial} {prescription.produit.dosage}",
                'principe_actif': prescription.produit.principe_actif,
                'forme': prescription.produit.forme,
                'quantite': prescription.quantite,
                'posologie': prescription.posologie,
                'duree_traitement': prescription.duree_traitement,
                'instructions': prescription.instructions_specifiques,
                'avant_repas': prescription.avant_repas,
                'avec_repas': prescription.avec_repas,
                'apres_repas': prescription.apres_repas,
                'substitution_autorisee': prescription.substitution_autorisee
            }
            medicaments_data.append(medicament_info)
            logger.info(f"✅ Médicament ajouté: {medicament_info['nom']}")
        
        # 2. Préparer les données patient
        patient_data = {
            'nom': ordonnance.patient.nom,
            'prenom': ordonnance.patient.prenom,
            'date_naissance': ordonnance.patient.date_naissance.strftime('%d/%m/%Y') if ordonnance.patient.date_naissance else 'Non renseignée',
            'telephone': ordonnance.patient.telephone,
            'adresse': f"{ordonnance.patient.commune}, {ordonnance.patient.quartier}" if hasattr(ordonnance.patient, 'commune') else ''
        }
        
        # 3. Préparer les données médecin
        medecin_data = {
            'nom': ordonnance.medecin.nom,
            'prenom': ordonnance.medecin.prenom,
            'specialite': getattr(ordonnance.medecin, 'specialite', 'Médecin généraliste'),
            'telephone': getattr(ordonnance.medecin, 'telephone', ''),
            'email': getattr(ordonnance.medecin, 'email', '')
        }
        
        # 4. Structurer toutes les données pour le générateur PDF
        donnees_ordonnance = {
            'numero': ordonnance.numero_unique,
            'patient': patient_data,
            'medecin': medecin_data,
            'medicaments': medicaments_data,
            'diagnostic': ordonnance.diagnostic,
            'motif_prescription': ordonnance.motif_prescription,
            'instructions_generales': ordonnance.instructions_generales,
            'date_prescription': ordonnance.date_prescription.strftime('%d/%m/%Y à %H:%M'),
            'date_validite': ordonnance.date_validite.strftime('%d/%m/%Y'),
            'renouvellement_autorise': ordonnance.renouvellement_autorise,
            'statut': ordonnance.statut
        }
        
        logger.info(f"📋 Données préparées pour {len(medicaments_data)} médicaments")
        
        # 5. Générer le PDF avec la classe GenerateurPDFOrdonnance
        generateur = GenerateurPDFOrdonnance()
        resultat = generateur.generer_pdf_ordonnance(donnees_ordonnance)
        
        if resultat['success']:
            logger.info(f"✅ PDF généré avec succès: {resultat['url_pdf']}")
        else:
            logger.error(f"❌ Erreur génération PDF: {resultat.get('error', 'Erreur inconnue')}")
        
        return resultat
        
    except Exception as e:
        logger.error(f"❌ Erreur dans generer_pdf_ordonnance_detaille: {e}")
        return {
            'success': False,
            'error': f"Erreur génération PDF: {str(e)}",
            'numero': getattr(ordonnance, 'numero_unique', 'UNKNOWN')
        }


def generer_pdf_bon_examen_detaille(bon_examen):
    """
    Fonction de pont pour générer les PDFs de bons d'examens
    
    Args:
        bon_examen: Instance du modèle BonExamen avec ses examens liés
        
    Returns:
        dict: Résultat de la génération PDF avec success/error
    """
    try:
        logger.info(f"🔄 Génération PDF pour bon d'examen {bon_examen.numero_unique}")
        
        # 1. Extraire les examens liés
        examens_prescrits = bon_examen.examens.all()
        logger.info(f"📊 Nombre d'examens trouvés: {examens_prescrits.count()}")
        
        examens_data = []
        for examen_prescrit in examens_prescrits:
            examen_info = {
                'nom': examen_prescrit.acte.nom,
                'code': examen_prescrit.acte.code,
                'categorie': examen_prescrit.acte.categorie,
                'localisation': examen_prescrit.localisation,
                'instructions': examen_prescrit.instructions_specifiques,
                'preparation': examen_prescrit.preparation_specifique or examen_prescrit.acte.preparation_requise,
                'urgent': examen_prescrit.urgent,
                'duree_estimee': examen_prescrit.acte.duree_estimee
            }
            examens_data.append(examen_info)
            logger.info(f"✅ Examen ajouté: {examen_info['nom']}")
        
        # 2. Préparer les données patient
        patient_data = {
            'nom': bon_examen.patient.nom,
            'prenom': bon_examen.patient.prenom,
            'date_naissance': bon_examen.patient.date_naissance.strftime('%d/%m/%Y') if bon_examen.patient.date_naissance else 'Non renseignée',
            'telephone': bon_examen.patient.telephone,
            'adresse': f"{bon_examen.patient.commune}, {bon_examen.patient.quartier}" if hasattr(bon_examen.patient, 'commune') else ''
        }
        
        # 3. Préparer les données médecin
        medecin_data = {
            'nom': bon_examen.medecin.nom,
            'prenom': bon_examen.medecin.prenom,
            'specialite': getattr(bon_examen.medecin, 'specialite', 'Médecin généraliste'),
            'telephone': getattr(bon_examen.medecin, 'telephone', ''),
            'email': getattr(bon_examen.medecin, 'email', '')
        }
        
        # 4. Structurer toutes les données pour le générateur PDF
        donnees_bon = {
            'numero': bon_examen.numero_unique,
            'patient': patient_data,
            'medecin': medecin_data,
            'examens': examens_data,
            'motif': bon_examen.motif,
            'diagnostic_provisoire': bon_examen.diagnostic_provisoire,
            'renseignements_cliniques': bon_examen.renseignements_cliniques,
            'instructions_preparation': bon_examen.instructions_preparation,
            'priorite': bon_examen.get_priorite_display(),
            'delai_realisation': bon_examen.delai_realisation,
            'date_prescription': bon_examen.date_prescription.strftime('%d/%m/%Y à %H:%M'),
            'date_validite': bon_examen.date_validite.strftime('%d/%m/%Y'),
            'statut': bon_examen.statut
        }
        
        logger.info(f"📋 Données préparées pour {len(examens_data)} examens")
        
        # 5. Générer le PDF avec la classe GenerateurPDFOrdonnance
        generateur = GenerateurPDFOrdonnance()
        resultat = generateur.generer_pdf_bon_examen(donnees_bon)
        
        if resultat['success']:
            logger.info(f"✅ PDF bon d'examen généré avec succès: {resultat['url_pdf']}")
        else:
            logger.error(f"❌ Erreur génération PDF bon d'examen: {resultat.get('error', 'Erreur inconnue')}")
        
        return resultat
        
    except Exception as e:
        logger.error(f"❌ Erreur dans generer_pdf_bon_examen_detaille: {e}")
        return {
            'success': False,
            'error': f"Erreur génération PDF: {str(e)}",
            'numero': getattr(bon_examen, 'numero_unique', 'UNKNOWN')
        }


# 🔧 Fonction utilitaire pour déboguer les ordonnances
def debug_ordonnance_medicaments(ordonnance):
    """
    Fonction de débogage pour vérifier le contenu d'une ordonnance
    """
    try:
        print(f"🔍 DEBUG - Ordonnance {ordonnance.numero_unique}")
        print(f"📊 Patient: {ordonnance.patient.nom_complet()}")
        print(f"👨‍⚕️ Médecin: Dr {ordonnance.medecin.nom} {ordonnance.medecin.prenom}")
        
        prescriptions = ordonnance.prescriptions.all()
        print(f"💊 Nombre de prescriptions: {prescriptions.count()}")
        
        for i, prescription in enumerate(prescriptions, 1):
            print(f"  {i}. {prescription.produit.nom_commercial} {prescription.produit.dosage}")
            print(f"     Posologie: {prescription.posologie}")
            print(f"     Durée: {prescription.duree_traitement}")
            print(f"     Quantité: {prescription.quantite}")
        
        return True
    except Exception as e:
        print(f"❌ Erreur debug: {e}")
        return False

