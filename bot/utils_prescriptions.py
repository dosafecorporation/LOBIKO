# utils_prescriptions.py - Utilitaires pour génération PDF avec stockage S3

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import qrcode
from io import BytesIO
import uuid
from datetime import datetime, timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)

def upload_prescription_to_s3(file_data, file_name, mime_type='application/pdf'):
    """Upload un fichier de prescription vers S3"""
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )
    
    # Dossier spécifique pour les prescriptions
    s3_key = f"{settings.AWS_S3_MEDIA_FOLDER}prescriptions/{file_name}"
    
    try:
        s3.upload_fileobj(
            ContentFile(file_data),
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_key,
            ExtraArgs={
                'ContentType': mime_type,
                'ACL': 'public-read' if settings.AWS_DEFAULT_ACL == 'public-read' else 'private'
            }
        )
        
        url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{s3_key}"
        logger.info(f"Prescription uploadée vers S3: {url}")
        
        return {
            'url': url,
            's3_key': s3_key
        }
    except ClientError as e:
        logger.error(f"Erreur upload prescription S3: {str(e)}")
        return None

def generer_qr_code_prescription(data):
    """Générer un QR code pour la prescription"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="#2E8B57", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def generer_prescription_pdf(prescription):
    """Générer le PDF d'une prescription avec stockage S3"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=2*cm, 
        leftMargin=2*cm, 
        topMargin=2*cm, 
        bottomMargin=2*cm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2E8B57')
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#4682B4')
    )
    
    normal_style = styles['Normal']
    
    # Contenu du document
    story = []
    
    # En-tête avec informations clinique
    header_data = [
        ['', 'LOBIKO HEALTH', f'ORDONNANCE MÉDICALE'],
        ['', 'Centre Médical Spécialisé', f'N° {prescription.numero}'],
        ['', '123 Avenue de la Santé, Kinshasa', ''],
        ['', 'Tél: +243 123 456 789', '']
    ]
    
    header_table = Table(header_data, colWidths=[3*cm, 10*cm, 4*cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (1, 0), 16),
        ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (2, 0), (2, 0), 14),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#2E8B57')),
        ('TEXTCOLOR', (2, 0), (2, 0), colors.HexColor('#4682B4')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # Informations du patient
    story.append(Paragraph("INFORMATIONS DU PATIENT", header_style))
    
    patient_data = [
        ['Nom complet:', prescription.patient.nom_complet],
        ['Âge:', f"{prescription.patient.age} ans"],
        ['Sexe:', prescription.patient.get_sexe_display()],
        ['Téléphone:', prescription.patient.telephone],
        ['Adresse:', f"{prescription.patient.commune}, {prescription.patient.quartier}"],
        ['Date de consultation:', prescription.date_creation.strftime('%d/%m/%Y')],
    ]
    
    patient_table = Table(patient_data, colWidths=[4*cm, 10*cm])
    patient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(patient_table)
    story.append(Spacer(1, 20))
    
    # Informations du médecin
    story.append(Paragraph("MÉDECIN PRESCRIPTEUR", header_style))
    
    medecin_info = f"""
    <b>Dr. {prescription.medecin.get_full_name()}</b><br/>
    Médecin Généraliste - Ordre des Médecins N° 12345<br/>
    Spécialité: Médecine Interne
    """
    
    story.append(Paragraph(medecin_info, normal_style))
    story.append(Spacer(1, 20))
    
    # Diagnostic
    if prescription.diagnostic:
        story.append(Paragraph("DIAGNOSTIC", header_style))
        story.append(Paragraph(prescription.diagnostic, normal_style))
        story.append(Spacer(1, 15))
    
    # Motif de prescription
    if prescription.motif_prescription:
        story.append(Paragraph("MOTIF DE LA PRESCRIPTION", header_style))
        story.append(Paragraph(prescription.motif_prescription, normal_style))
        story.append(Spacer(1, 15))
    
    # Prescription médicamenteuse
    story.append(Paragraph("PRESCRIPTION MÉDICAMENTEUSE", header_style))
    
    # Tableau des médicaments
    medicaments_data = [['Médicament', 'Dosage', 'Posologie', 'Durée', 'Quantité']]
    
    for ligne in prescription.lignes.all():
        medicament_info = f"{ligne.produit.nom_commercial}"
        if ligne.produit.nom_generique:
            medicament_info += f"\\n({ligne.produit.nom_generique})"
        medicament_info += f"\\n{ligne.produit.forme}"
        
        medicaments_data.append([
            medicament_info,
            ligne.produit.dosage,
            ligne.posologie,
            ligne.duree_traitement,
            ligne.quantite_prescrite or "-"
        ])
    
    medicaments_table = Table(medicaments_data, colWidths=[4*cm, 2.5*cm, 3.5*cm, 2.5*cm, 2.5*cm])
    medicaments_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E9ECEF')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#495057')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    story.append(medicaments_table)
    story.append(Spacer(1, 20))
    
    # Instructions spécifiques par médicament
    for ligne in prescription.lignes.all():
        if ligne.instructions_specifiques:
            story.append(Paragraph(f"<b>{ligne.produit.nom_commercial}:</b> {ligne.instructions_specifiques}", normal_style))
    
    story.append(Spacer(1, 15))
    
    # Instructions générales
    if prescription.instructions_generales:
        story.append(Paragraph("INSTRUCTIONS GÉNÉRALES", header_style))
        story.append(Paragraph(prescription.instructions_generales, normal_style))
        story.append(Spacer(1, 15))
    
    # Instructions standard
    instructions_standard = """
    <b>INSTRUCTIONS IMPORTANTES :</b><br/>
    • Respecter scrupuleusement la posologie indiquée<br/>
    • Ne pas interrompre le traitement sans avis médical<br/>
    • En cas d'effets indésirables, consulter immédiatement<br/>
    • Conserver les médicaments dans un endroit sec et frais<br/>
    • Tenir hors de portée des enfants<br/>
    • Ne pas dépasser la date de validité de cette ordonnance
    """
    
    story.append(Paragraph(instructions_standard, normal_style))
    story.append(Spacer(1, 30))
    
    # Validité
    if prescription.date_validite:
        validite_text = f"<b>Validité:</b> Cette ordonnance est valable jusqu'au {prescription.date_validite.strftime('%d/%m/%Y')}"
        story.append(Paragraph(validite_text, normal_style))
        story.append(Spacer(1, 15))
    
    # Pied de page avec signature
    footer_data = [
        [f"Date d'émission: {prescription.date_creation.strftime('%d/%m/%Y à %H:%M')}", ''],
        [f"Lieu: Kinshasa, RDC", 'Signature et cachet du médecin'],
        ['', ''],
        ['', '________________________'],
    ]
    
    footer_table = Table(footer_data, colWidths=[10*cm, 7*cm])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(footer_table)
    
    # Construire le PDF
    doc.build(story)
    
    # Upload vers S3
    buffer.seek(0)
    filename = f"ordonnance_{prescription.numero}_{uuid.uuid4().hex[:8]}.pdf"
    
    upload_result = upload_prescription_to_s3(
        buffer.read(),
        filename,
        'application/pdf'
    )
    
    if upload_result:
        # Sauvegarder les informations dans la prescription
        prescription.pdf_file_url = upload_result['url']
        prescription.s3_key = upload_result['s3_key']
        
        # Générer les données du QR code
        qr_data = f"Ordonnance: {prescription.numero}\\nPatient: {prescription.patient.nom_complet}\\nMédecin: Dr. {prescription.medecin.get_full_name()}\\nDate: {prescription.date_creation.strftime('%d/%m/%Y')}\\nLobiko Health - Vérification: https://lobiko.health/verify/{prescription.numero}"
        prescription.qr_code_data = qr_data
        
        prescription.save()
        
        return upload_result
    
    return None

def generer_bon_examen_pdf(bon_examen):
    """Générer le PDF d'un bon d'examens avec stockage S3"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=2*cm, 
        leftMargin=2*cm, 
        topMargin=2*cm, 
        bottomMargin=2*cm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2E8B57')
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#4682B4')
    )
    
    normal_style = styles['Normal']
    
    # Contenu du document
    story = []
    
    # En-tête
    header_data = [
        ['', 'LOBIKO HEALTH', f'BON D\'EXAMENS'],
        ['', 'Centre Médical Spécialisé', f'N° {bon_examen.numero}'],
        ['', '123 Avenue de la Santé, Kinshasa', ''],
        ['', 'Tél: +243 123 456 789', '']
    ]
    
    header_table = Table(header_data, colWidths=[3*cm, 10*cm, 4*cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (1, 0), 16),
        ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (2, 0), (2, 0), 14),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#2E8B57')),
        ('TEXTCOLOR', (2, 0), (2, 0), colors.HexColor('#4682B4')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # Informations du patient
    story.append(Paragraph("INFORMATIONS DU PATIENT", header_style))
    
    patient_data = [
        ['Nom complet:', bon_examen.patient.nom_complet],
        ['Âge:', f"{bon_examen.patient.age} ans"],
        ['Sexe:', bon_examen.patient.get_sexe_display()],
        ['Téléphone:', bon_examen.patient.telephone],
        ['Adresse:', f"{bon_examen.patient.commune}, {bon_examen.patient.quartier}"],
        ['Date de consultation:', bon_examen.date_creation.strftime('%d/%m/%Y')],
    ]
    
    patient_table = Table(patient_data, colWidths=[4*cm, 10*cm])
    patient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(patient_table)
    story.append(Spacer(1, 20))
    
    # Informations du médecin
    story.append(Paragraph("MÉDECIN PRESCRIPTEUR", header_style))
    
    medecin_info = f"""
    <b>Dr. {bon_examen.medecin.get_full_name()}</b><br/>
    Médecin Généraliste - Ordre des Médecins N° 12345<br/>
    Spécialité: Médecine Interne
    """
    
    story.append(Paragraph(medecin_info, normal_style))
    story.append(Spacer(1, 20))
    
    # Notice urgente si applicable
    if bon_examen.priorite in ['URGENT', 'TRES_URGENT']:
        urgence_text = f"""
        <b>⚠️ EXAMENS {bon_examen.get_priorite_display().upper()}</b><br/>
        Ces examens nécessitent une réalisation en urgence. 
        Veuillez vous présenter dans les plus brefs délais.
        """
        
        story.append(Paragraph(urgence_text, ParagraphStyle(
            'Urgence',
            parent=normal_style,
            backColor=colors.HexColor('#FFE6E6'),
            borderColor=colors.HexColor('#FF0000'),
            borderWidth=1,
            leftIndent=10,
            rightIndent=10,
            spaceAfter=15,
            spaceBefore=10
        )))
    
    # Motif des examens
    if bon_examen.motif_examens:
        story.append(Paragraph("MOTIF DES EXAMENS", header_style))
        story.append(Paragraph(bon_examen.motif_examens, normal_style))
        story.append(Spacer(1, 15))
    
    # Renseignements cliniques
    if bon_examen.renseignements_cliniques:
        story.append(Paragraph("RENSEIGNEMENTS CLINIQUES", header_style))
        story.append(Paragraph(bon_examen.renseignements_cliniques, normal_style))
        story.append(Spacer(1, 15))
    
    # Examens prescrits par catégorie
    story.append(Paragraph("EXAMENS PRESCRITS", header_style))
    
    # Grouper par catégorie
    categories = {}
    for ligne in bon_examen.lignes.all():
        categorie = ligne.acte.get_categorie_display()
        if categorie not in categories:
            categories[categorie] = []
        categories[categorie].append(ligne)
    
    for categorie, lignes in categories.items():
        # Titre de la catégorie
        categorie_title = categorie
        if any(ligne.urgent for ligne in lignes):
            categorie_title += " (URGENT)"
        
        story.append(Paragraph(categorie_title, ParagraphStyle(
            'Categorie',
            parent=header_style,
            fontSize=12,
            textColor=colors.HexColor('#4682B4'),
            spaceAfter=8
        )))
        
        # Tableau des examens de cette catégorie
        examens_data = [['Examen', 'Code', 'Localisation', 'Instructions']]
        
        for ligne in lignes:
            examens_data.append([
                ligne.acte.nom + (" ⚠️" if ligne.urgent else ""),
                ligne.acte.code,
                ligne.localisation or "-",
                ligne.instructions_specifiques or ligne.acte.preparation_requise or "-"
            ])
        
        examens_table = Table(examens_data, colWidths=[4*cm, 2*cm, 3*cm, 6*cm])
        examens_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E9ECEF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#495057')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        story.append(examens_table)
        story.append(Spacer(1, 15))
    
    # Instructions de préparation
    if bon_examen.instructions_preparation:
        story.append(Paragraph("INSTRUCTIONS DE PRÉPARATION", header_style))
        story.append(Paragraph(bon_examen.instructions_preparation, normal_style))
        story.append(Spacer(1, 15))
    
    # Instructions standard
    instructions_standard = """
    <b>INSTRUCTIONS IMPORTANTES :</b><br/>
    • Jeûne requis: 12 heures avant les analyses sanguines (eau autorisée)<br/>
    • Médicaments: Continuer le traitement habituel sauf indication contraire<br/>
    • Échographie: Boire 1 litre d'eau 1 heure avant l'examen et ne pas uriner<br/>
    • Résultats: À récupérer dans les 48-72h pour les analyses de laboratoire<br/>
    • Urgence: En cas de malaise, se présenter immédiatement aux urgences<br/>
    • Rendez-vous: Prendre rendez-vous pour les examens spécialisés
    """
    
    story.append(Paragraph(instructions_standard, normal_style))
    story.append(Spacer(1, 30))
    
    # Pied de page
    footer_data = [
        [f"Date d'émission: {bon_examen.date_creation.strftime('%d/%m/%Y à %H:%M')}", ''],
        [f"Validité: {bon_examen.validite_jours} jours (jusqu'au {bon_examen.date_validite.strftime('%d/%m/%Y')})", 'Signature et cachet du médecin'],
        ['', ''],
        ['', '________________________'],
    ]
    
    footer_table = Table(footer_data, colWidths=[10*cm, 7*cm])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(footer_table)
    
    # Construire le PDF
    doc.build(story)
    
    # Upload vers S3
    buffer.seek(0)
    filename = f"bon_examen_{bon_examen.numero}_{uuid.uuid4().hex[:8]}.pdf"
    
    upload_result = upload_prescription_to_s3(
        buffer.read(),
        filename,
        'application/pdf'
    )
    
    if upload_result:
        # Sauvegarder les informations dans le bon d'examens
        bon_examen.pdf_file_url = upload_result['url']
        bon_examen.s3_key = upload_result['s3_key']
        
        # Générer les données du QR code
        qr_data = f"Bon d'examens: {bon_examen.numero}\\nPatient: {bon_examen.patient.nom_complet}\\nMédecin: Dr. {bon_examen.medecin.get_full_name()}\\nDate: {bon_examen.date_creation.strftime('%d/%m/%Y')}\\nLobiko Health - Vérification: https://lobiko.health/verify/{bon_examen.numero}"
        bon_examen.qr_code_data = qr_data
        
        bon_examen.save()
        
        return upload_result
    
    return None

def envoyer_prescription_websocket(session_id, prescription_obj, type_prescription):
    """Envoyer la prescription via WebSocket"""
    channel_layer = get_channel_layer()
    
    if type_prescription == 'ORDONNANCE':
        data = {
            'type': 'prescription_medicament',
            'prescription_id': str(prescription_obj.id),
            'numero': prescription_obj.numero,
            'patient': prescription_obj.patient.nom_complet,
            'medecin': prescription_obj.medecin.get_full_name(),
            'date': prescription_obj.date_creation.isoformat(),
            'medicaments_count': prescription_obj.lignes.count(),
            'pdf_url': prescription_obj.pdf_file_url,
            's3_key': prescription_obj.s3_key
        }
    else:  # BON_EXAMEN
        data = {
            'type': 'bon_examen',
            'bon_examen_id': str(prescription_obj.id),
            'numero': prescription_obj.numero,
            'patient': prescription_obj.patient.nom_complet,
            'medecin': prescription_obj.medecin.get_full_name(),
            'date': prescription_obj.date_creation.isoformat(),
            'examens_count': prescription_obj.lignes.count(),
            'priorite': prescription_obj.get_priorite_display(),
            'pdf_url': prescription_obj.pdf_file_url,
            's3_key': prescription_obj.s3_key
        }
    
    async_to_sync(channel_layer.group_send)(
        f"discussion_{session_id}",
        {
            'type': 'send_prescription',
            'data': data
        }
    )

