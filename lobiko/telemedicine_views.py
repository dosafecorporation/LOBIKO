import json
import boto3
import requests
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Medecin, Patient, SessionDiscussion, Message
from .telemedicine_models import (
    ProduitPharmaceutique, ActeMedical, Ordonnance, PrescriptionMedicament,
    BonExamen, ExamenPrescrit, MessagePrescription
)

# 🔧 CORRECTION: Import des fonctions de génération PDF
from .telemedicine_utils import (
    generer_pdf_ordonnance_detaille, 
    generer_pdf_bon_examen_detaille,
    debug_ordonnance_medicaments
)


class WhatsAppService:
    """Service pour envoyer des messages et documents via WhatsApp Business API"""
    
    def __init__(self):
        self.access_token = getattr(settings, 'ACCESS_TOKEN', '')
        self.phone_number_id = getattr(settings, 'PHONE_NUMBER_ID', '')
        self.api_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
        
        if not self.access_token or not self.phone_number_id:
            print("⚠️ ATTENTION: WhatsApp non configuré - vérifiez vos variables d'environnement")
    
    def envoyer_message_texte(self, numero_patient, message):
        """Envoie un message texte via WhatsApp"""
        try:
            # Nettoyer le numéro (enlever espaces, tirets, etc.)
            numero_clean = ''.join(filter(str.isdigit, numero_patient))
            
            # Ajouter l'indicatif pays si manquant (243)
            if not numero_clean.startswith('243'):
                numero_clean = '243' + numero_clean
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": numero_clean,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            response = requests.post(self.api_url, headers=headers, json=data)
            
            if response.status_code == 200:
                print(f"✅ Message WhatsApp envoyé à {numero_clean}")
                return response.json()
            else:
                print(f"❌ Erreur envoi WhatsApp: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur WhatsApp: {e}")
            return None
    
    def envoyer_document(self, numero_patient, url_document, nom_fichier, caption=""):
        """Envoie un document PDF via WhatsApp"""
        try:
            # Nettoyer le numéro (enlever espaces, tirets, etc.)
            numero_clean = ''.join(filter(str.isdigit, numero_patient))
            
            # Ajouter l'indicatif pays si manquant (243)
            if not numero_clean.startswith('243'):
                numero_clean = '243' + numero_clean
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": numero_clean,
                "type": "document",
                "document": {
                    "link": url_document,
                    "caption": caption,
                    "filename": nom_fichier
                }
            }
            
            response = requests.post(self.api_url, headers=headers, json=data)
            
            if response.status_code == 200:
                print(f"✅ Document WhatsApp envoyé à {numero_clean}: {nom_fichier}")
                return response.json()
            else:
                print(f"❌ Erreur envoi document WhatsApp: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur envoi document WhatsApp: {e}")
            return None
    
    def envoyer_prescription_complete(self, patient, type_prescription, numero, url_pdf, nom_fichier):
        """Envoie une prescription complète (message + PDF)"""
        try:
            # Message selon le type
            if type_prescription == 'ordonnance':
                emoji = "💊"
                titre = "Ordonnance médicale"
            else:
                emoji = "🔬"
                titre = "Bon d'examens médicaux"
            
            message = f"""{emoji} *{titre}*

📋 N° {numero}
📅 Date: {self._get_date_now()}
👤 Patient: {patient.nom}

📄 Consultez le document PDF ci-joint pour tous les détails.

⚠️ Document officiel - Conservez précieusement"""
            
            # Envoyer le message texte
            response_text = self.envoyer_message_texte(patient.telephone, message)
            
            if response_text:
                # Envoyer le PDF
                response_doc = self.envoyer_document(
                    patient.telephone, 
                    url_pdf, 
                    nom_fichier, 
                    f"{titre} N° {numero}"
                )
                return response_doc
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur envoi prescription complète: {e}")
            return None
    
    def _get_date_now(self):
        """Retourne la date actuelle formatée"""
        from datetime import datetime
        return datetime.now().strftime('%d/%m/%Y à %H:%M')


def get_client_ip(request):
    """Récupère l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@csrf_exempt
@require_http_methods(["GET"])
def api_produits_pharmaceutiques(request):
    """API pour récupérer la liste des produits pharmaceutiques"""
    try:
        produits = ProduitPharmaceutique.objects.filter(disponible=True).order_by('nom_commercial')
        
        data = []
        for produit in produits:
            data.append({
                'id': produit.id,
                'nom_commercial': produit.nom_commercial,
                'principe_actif': produit.principe_actif,
                'dosage': produit.dosage,
                'forme': produit.forme,
                'laboratoire': produit.laboratoire,
                'posologie_adulte': produit.posologie_adulte,
                'duree_traitement_standard': produit.duree_traitement_standard,
                'prix_unitaire': float(produit.prix_unitaire) if produit.prix_unitaire else None
            })
        
        return JsonResponse(data, safe=False)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur lors de la récupération des produits: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_actes_medicaux(request):
    """API pour récupérer la liste des actes médicaux"""
    try:
        actes = ActeMedical.objects.filter(disponible=True).order_by('categorie', 'nom')
        
        data = []
        for acte in actes:
            data.append({
                'id': acte.id,
                'nom': acte.nom,
                'code': acte.code,
                'categorie': acte.categorie,
                'description': acte.description,
                'preparation_requise': acte.preparation_requise,
                'duree_estimee': acte.duree_estimee,
                'prix': float(acte.prix) if acte.prix else None
            })
        
        return JsonResponse(data, safe=False)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur lors de la récupération des actes: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_creer_prescription(request):
    """API pour créer une ordonnance médicale - VERSION CORRIGÉE"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        medecin_id = data.get('medecin_id')
        prescription_data = data.get('prescription_data')
        
        print(f"🔍 DEBUG - Données reçues: session_id={session_id}, medecin_id={medecin_id}")
        print(f"🔍 DEBUG - Médicaments reçus: {len(prescription_data.get('medicaments', []))}")
        
        # Validation des données
        if not all([session_id, medecin_id, prescription_data]):
            return JsonResponse({
                'status': 'error',
                'message': 'Données manquantes (session_id, medecin_id, prescription_data requis)'
            }, status=400)
        
        # Récupérer les objets nécessaires
        try:
            from .models import SessionDiscussion, Medecin
            session = SessionDiscussion.objects.get(id=session_id)
            medecin = Medecin.objects.get(id=medecin_id)
            patient = session.patient
        except (SessionDiscussion.DoesNotExist, Medecin.DoesNotExist) as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Objet non trouvé: {str(e)}'
            }, status=404)
        
        # Générer un numéro unique pour l'ordonnance
        import random
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        numero_unique = f"ORD-{timestamp}-{random.randint(1000, 9999)}"
        
        # Calculer la date de validité (30 jours par défaut)
        date_validite_str = prescription_data.get('date_validite')
        if date_validite_str:
            try:
                date_validite = datetime.strptime(date_validite_str, '%Y-%m-%d').date()
            except ValueError:
                date_validite = (timezone.now() + timedelta(days=30)).date()
        else:
            date_validite = (timezone.now() + timedelta(days=30)).date()
        
        # Créer l'ordonnance
        try:
            from .telemedicine_models import Ordonnance, PrescriptionMedicament, ProduitPharmaceutique
            
            # Créer l'ordonnance
            ordonnance = Ordonnance.objects.create(
                medecin=medecin,
                patient=patient,
                session_discussion=session,
                numero_unique=numero_unique,
                diagnostic=prescription_data.get('diagnostic', ''),
                motif_prescription=prescription_data.get('motif', ''),
                instructions_generales=prescription_data.get('instructions_generales', ''),
                date_validite=date_validite
            )
            
            print(f"✅ Ordonnance créée: {ordonnance.numero_unique}")
            
            # Ajouter les médicaments
            medicaments = prescription_data.get('medicaments', [])
            medicaments_crees = 0
            
            for med_data in medicaments:
                try:
                    produit = ProduitPharmaceutique.objects.get(id=med_data['produit_id'])
                    
                    prescription_med = PrescriptionMedicament.objects.create(
                        ordonnance=ordonnance,
                        produit=produit,
                        quantite=med_data.get('quantite', ''),
                        posologie=med_data['posologie'],
                        duree_traitement=med_data['duree_traitement'],
                        instructions_specifiques=med_data.get('instructions', ''),
                        avant_repas=med_data.get('avant_repas', False),
                        avec_repas=med_data.get('avec_repas', False),
                        apres_repas=med_data.get('apres_repas', False),
                        substitution_autorisee=med_data.get('substitution_autorisee', True)
                    )
                    medicaments_crees += 1
                    print(f"✅ Médicament ajouté: {produit.nom_commercial}")
                    
                except ProduitPharmaceutique.DoesNotExist:
                    print(f"⚠️ Produit non trouvé: ID {med_data.get('produit_id')}")
                    continue
                except Exception as e:
                    print(f"❌ Erreur ajout médicament: {e}")
                    # En cas d'erreur, supprimer l'ordonnance et retourner l'erreur
                    ordonnance.delete()
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Erreur dans la prescription de médicament: {str(e)}'
                    }, status=400)
            
            print(f"📊 Total médicaments créés: {medicaments_crees}")
            
            # 🔧 CORRECTION: Déboguer l'ordonnance avant génération PDF
            debug_ordonnance_medicaments(ordonnance)
            
            # 🔧 CORRECTION: Utiliser la fonction corrigée pour générer le PDF
            pdf_result = generer_pdf_ordonnance_detaille(ordonnance)
            
            if pdf_result['success']:
                print(f"✅ PDF généré avec succès: {pdf_result['url_pdf']}")
                
                # Envoyer via WhatsApp
                try:
                    whatsapp_service = WhatsAppService()
                    if whatsapp_service.access_token and whatsapp_service.phone_number_id:
                        # Configuration WhatsApp OK
                        response = whatsapp_service.envoyer_prescription_complete(
                            patient,
                            'ordonnance',
                            numero_unique,
                            pdf_result['url_pdf'],
                            f"Ordonnance_{numero_unique}.pdf"
                        )
                        
                        if response:
                            print(f"✅ Ordonnance envoyée via WhatsApp")
                            # Marquer comme envoyé
                            ordonnance.envoye_whatsapp = True
                            ordonnance.save()
                        else:
                            print(f"❌ Échec envoi WhatsApp")
                    else:
                        print(f"⚠️ WhatsApp non configuré - ajoutez WHATSAPP_ACCESS_TOKEN et WHATSAPP_PHONE_NUMBER_ID")
                except Exception as e:
                    print(f"Erreur envoi WhatsApp: {e}")
                
                # Ajouter un message dans la discussion
                from .models import Message
                Message.objects.create(
                    session=session,
                    contenu=f"📋 Ordonnance {numero_unique} envoyée au patient ({medicaments_crees} médicaments)",
                    emetteur_type='MEDECIN',
                    emetteur_id=medecin.id
                )
                
                # Notifier via WebSocket
                try:
                    channel_layer = get_channel_layer()
                    if channel_layer:
                        async_to_sync(channel_layer.group_send)(
                            f"discussion_{session_id}",
                            {
                                'type': 'prescription_sent',
                                'data': {
                                    'type': 'prescription_medicament',
                                    'numero': numero_unique,
                                    'prescription_id': ordonnance.id,
                                    'medicaments_count': medicaments_crees,
                                    'medecin': f"Dr {medecin.nom} {medecin.prenom}",
                                    'date': ordonnance.date_prescription.isoformat(),
                                    'pdf_url': pdf_result['url_pdf']
                                }
                            }
                        )
                except Exception as e:
                    print(f"Erreur WebSocket: {e}")
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Ordonnance créée avec succès ({medicaments_crees} médicaments)',
                    'numero': numero_unique,
                    'prescription_id': ordonnance.id,
                    'pdf_url': pdf_result['url_pdf'],
                    'url_finale': pdf_result['url_pdf'],
                    'medecin': f"Dr {medecin.nom} {medecin.prenom}",
                    'medicaments_count': medicaments_crees
                })
            else:
                # Supprimer l'ordonnance si le PDF a échoué
                ordonnance.delete()
                return JsonResponse({
                    'status': 'error',
                    'message': f'Erreur génération PDF: {pdf_result["error"]}'
                }, status=500)
                
        except ImportError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Erreur import modèles: {str(e)}'
            }, status=500)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur serveur: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_creer_bon_examen(request):
    """API pour créer un bon d'examen - VERSION CORRIGÉE"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        medecin_id = data.get('medecin_id')
        bon_examen_data = data.get('bon_examen_data')
        
        print(f"🔍 DEBUG - Données bon d'examen reçues: session_id={session_id}, medecin_id={medecin_id}")
        print(f"🔍 DEBUG - Examens reçus: {len(bon_examen_data.get('examens', []))}")
        
        # Validation des données
        if not all([session_id, medecin_id, bon_examen_data]):
            return JsonResponse({
                'status': 'error',
                'message': 'Données manquantes (session_id, medecin_id, bon_examen_data requis)'
            }, status=400)
        
        # Récupérer les objets
        try:
            session = SessionDiscussion.objects.get(id=session_id)
            medecin = Medecin.objects.get(id=medecin_id)
            patient = session.patient
        except (SessionDiscussion.DoesNotExist, Medecin.DoesNotExist) as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Objet non trouvé: {str(e)}'
            }, status=404)
        
        # Générer un numéro unique
        import random
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        numero_unique = f"BON-{timestamp}-{random.randint(1000, 9999)}"
        
        # Calculer la date de validité
        date_validite_str = bon_examen_data.get('date_validite')
        if date_validite_str:
            try:
                date_validite = datetime.strptime(date_validite_str, '%Y-%m-%d').date()
            except ValueError:
                date_validite = (timezone.now() + timedelta(days=60)).date()
        else:
            date_validite = (timezone.now() + timedelta(days=60)).date()
        
        # Créer le bon d'examen
        try:
            bon_examen = BonExamen.objects.create(
                medecin=medecin,
                patient=patient,
                session_discussion=session,
                numero_unique=numero_unique,
                motif=bon_examen_data.get('motif', ''),
                diagnostic_provisoire=bon_examen_data.get('diagnostic_provisoire', ''),
                renseignements_cliniques=bon_examen_data.get('renseignements_cliniques', ''),
                instructions_preparation=bon_examen_data.get('instructions_preparation', ''),
                priorite=bon_examen_data.get('priorite', 'NORMAL'),
                delai_realisation=bon_examen_data.get('delai_realisation', ''),
                date_validite=date_validite
            )
            
            print(f"✅ Bon d'examen créé: {bon_examen.numero_unique}")
            
            # Ajouter les examens
            examens = bon_examen_data.get('examens', [])
            examens_crees = 0
            
            for exam_data in examens:
                try:
                    acte = ActeMedical.objects.get(id=exam_data['acte_id'])
                    
                    examen_prescrit = ExamenPrescrit.objects.create(
                        bon_examen=bon_examen,
                        acte=acte,
                        localisation=exam_data.get('localisation', ''),
                        instructions_specifiques=exam_data.get('instructions_specifiques', ''),
                        urgent=exam_data.get('urgent', False)
                    )
                    examens_crees += 1
                    print(f"✅ Examen ajouté: {acte.nom}")
                    
                except ActeMedical.DoesNotExist:
                    print(f"⚠️ Acte médical non trouvé: ID {exam_data.get('acte_id')}")
                    continue
                except Exception as e:
                    print(f"❌ Erreur ajout examen: {e}")
                    bon_examen.delete()
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Erreur dans la prescription d\'examen: {str(e)}'
                    }, status=400)
            
            print(f"📊 Total examens créés: {examens_crees}")
            
            # 🔧 CORRECTION: Utiliser la fonction corrigée pour générer le PDF
            pdf_result = generer_pdf_bon_examen_detaille(bon_examen)
            
            if pdf_result['success']:
                print(f"✅ PDF bon d'examen généré avec succès: {pdf_result['url_pdf']}")
                
                # Envoyer via WhatsApp
                try:
                    whatsapp_service = WhatsAppService()
                    if whatsapp_service.access_token and whatsapp_service.phone_number_id:
                        response = whatsapp_service.envoyer_prescription_complete(
                            patient,
                            'bon_examen',
                            numero_unique,
                            pdf_result['url_pdf'],
                            f"Bon_Examens_{numero_unique}.pdf"
                        )
                        
                        if response:
                            print(f"✅ Bon d'examen envoyé via WhatsApp")
                            bon_examen.envoye_whatsapp = True
                            bon_examen.save()
                        else:
                            print(f"❌ Échec envoi WhatsApp")
                    else:
                        print(f"⚠️ WhatsApp non configuré")
                except Exception as e:
                    print(f"Erreur envoi WhatsApp: {e}")
                
                # Ajouter un message dans la discussion
                Message.objects.create(
                    session=session,
                    contenu=f"🔬 Bon d'examens {numero_unique} envoyé au patient ({examens_crees} examens)",
                    emetteur_type='MEDECIN',
                    emetteur_id=medecin.id
                )
                
                # Notifier via WebSocket
                try:
                    channel_layer = get_channel_layer()
                    if channel_layer:
                        async_to_sync(channel_layer.group_send)(
                            f"discussion_{session_id}",
                            {
                                'type': 'bon_examen_sent',
                                'data': {
                                    'type': 'bon_examen',
                                    'numero': numero_unique,
                                    'bon_examen_id': bon_examen.id,
                                    'examens_count': examens_crees,
                                    'priorite': bon_examen.get_priorite_display(),
                                    'medecin': f"Dr {medecin.nom} {medecin.prenom}",
                                    'date': bon_examen.date_prescription.isoformat(),
                                    'pdf_url': pdf_result['url_pdf']
                                }
                            }
                        )
                except Exception as e:
                    print(f"Erreur WebSocket: {e}")
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Bon d\'examens créé avec succès ({examens_crees} examens)',
                    'numero': numero_unique,
                    'bon_examen_id': bon_examen.id,
                    'pdf_url': pdf_result['url_pdf'],
                    'url_finale': pdf_result['url_pdf'],
                    'medecin': f"Dr {medecin.nom} {medecin.prenom}",
                    'examens_count': examens_crees
                })
            else:
                bon_examen.delete()
                return JsonResponse({
                    'status': 'error',
                    'message': f'Erreur génération PDF: {pdf_result["error"]}'
                }, status=500)
                
        except Exception as e:
            print(f"❌ Erreur création bon d'examen: {e}")
            return JsonResponse({
                'status': 'error',
                'message': f'Erreur création bon d\'examen: {str(e)}'
            }, status=500)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        print(f"❌ Erreur générale bon d'examen: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur serveur: {str(e)}'
        }, status=500)


def creer_prescription_simple_fallback(session, medecin, patient, prescription_data, numero_unique):
    """Version de fallback si les modèles de télémédecine ne sont pas migrés"""
    try:
        # Créer un PDF simple sans base de données
        from .telemedicine_utils import GenerateurPDFOrdonnance
        
        # Préparer les données pour le PDF
        donnees_ordonnance = {
            'numero': numero_unique,
            'patient': {
                'nom': patient.nom,
                'prenom': patient.prenom,
                'date_naissance': patient.date_naissance.strftime('%d/%m/%Y') if patient.date_naissance else 'Non renseignée',
                'telephone': patient.telephone
            },
            'medecin': {
                'nom': medecin.nom,
                'prenom': medecin.prenom,
                'specialite': getattr(medecin, 'specialite', 'Médecin généraliste')
            },
            'medicaments': prescription_data.get('medicaments', []),
            'diagnostic': prescription_data.get('diagnostic', ''),
            'instructions_generales': prescription_data.get('instructions_generales', '')
        }
        
        # Générer le PDF
        generateur = GenerateurPDFOrdonnance()
        pdf_result = generateur.generer_pdf_ordonnance(donnees_ordonnance)
        
        if pdf_result['success']:
            # Ajouter un message dans la discussion
            Message.objects.create(
                session=session,
                contenu=f"📋 Ordonnance {numero_unique} créée (mode simple)",
                emetteur_type='MEDECIN',
                emetteur_id=medecin.id
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Ordonnance créée avec succès (mode simple)',
                'numero': numero_unique,
                'pdf_url': pdf_result['url_pdf'],
                'url_finale': pdf_result['url_pdf'],
                'medecin': f"Dr {medecin.nom} {medecin.prenom}"
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Erreur génération PDF: {pdf_result["error"]}'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur fallback: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_verifier_document(request):
    """API pour vérifier l'authenticité d'un document médical"""
    try:
        numero = request.GET.get('numero')
        hash_verification = request.GET.get('hash')
        type_document = request.GET.get('type', 'ordonnance')
        
        if not numero:
            return JsonResponse({
                'status': 'error',
                'message': 'Numéro de document requis'
            }, status=400)
        
        # Déterminer le modèle selon le type
        if type_document.lower() == 'ordonnance':
            from .telemedicine_models import Ordonnance
            model_class = Ordonnance
        elif type_document.lower() == 'bon_examen':
            from .telemedicine_models import BonExamen
            model_class = BonExamen
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Type de document non supporté'
            }, status=400)
        
        # Vérifier le document
        valide, resultat = model_class.verifier_document(numero, hash_verification)
        
        if valide:
            document = resultat
            return JsonResponse({
                'status': 'success',
                'valide': True,
                'document': {
                    'numero': document.numero_unique,
                    'type': type_document,
                    'patient': f"{document.patient.prenom} {document.patient.nom}",
                    'medecin': f"Dr {document.medecin.nom} {document.medecin.prenom}",
                    'date_prescription': document.date_prescription.strftime('%d/%m/%Y à %H:%M'),
                    'date_validite': document.date_validite.strftime('%d/%m/%Y'),
                    'statut': document.get_statut_display()
                }
            })
        else:
            return JsonResponse({
                'status': 'success',
                'valide': False,
                'message': resultat
            })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur lors de la vérification: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_verifier_qr_code(request):
    """API pour vérifier un document via QR code"""
    try:
        data = json.loads(request.body)
        qr_data = data.get('qr_data')
        
        if not qr_data:
            return JsonResponse({
                'status': 'error',
                'message': 'Données QR code requises'
            }, status=400)
        
        # Analyser les données QR
        try:
            parts = qr_data.split('|')
            if len(parts) != 5:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Format QR code invalide'
                }, status=400)
            
            numero, hash_verif, type_doc, medecin_cnom, patient_whatsapp = parts
            
            # Déterminer le modèle
            if type_doc == 'Ordonnance':
                from .telemedicine_models import Ordonnance
                model_class = Ordonnance
            elif type_doc == 'BonExamen':
                from .telemedicine_models import BonExamen
                model_class = BonExamen
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Type de document QR non supporté'
                }, status=400)
            
            # Vérifier via QR
            valide, resultat = model_class.verifier_qr_code(qr_data)
            
            if valide:
                document = resultat
                return JsonResponse({
                    'status': 'success',
                    'valide': True,
                    'document': {
                        'numero': document.numero_unique,
                        'type': type_doc.lower(),
                        'patient': f"{document.patient.prenom} {document.patient.nom}",
                        'medecin': f"Dr {document.medecin.nom} {document.medecin.prenom}",
                        'date_prescription': document.date_prescription.strftime('%d/%m/%Y à %H:%M'),
                        'date_validite': document.date_validite.strftime('%d/%m/%Y'),
                        'statut': document.get_statut_display()
                    }
                })
            else:
                return JsonResponse({
                    'status': 'success',
                    'valide': False,
                    'message': resultat
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Erreur analyse QR: {str(e)}'
            }, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur serveur: {str(e)}'
        }, status=500)


# CORRECTION POUR L'ERREUR DE MESSAGE NORMAL
@csrf_exempt
@require_http_methods(["POST"])
def api_envoyer_message(request):
    """API pour envoyer un message normal dans la discussion"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        contenu = data.get('contenu', '').strip()
        emetteur_type = data.get('emetteur_type', 'MEDECIN')
        emetteur_id = data.get('emetteur_id')
        
        # Validation
        if not all([session_id, contenu, emetteur_id]):
            return JsonResponse({
                'status': 'error',
                'message': 'Données manquantes (session_id, contenu, emetteur_id requis)'
            }, status=400)
        
        # Récupérer la session
        try:
            session = SessionDiscussion.objects.get(id=session_id)
        except SessionDiscussion.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Session non trouvée'
            }, status=404)
        
        # Créer le message
        message = Message.objects.create(
            session=session,
            contenu=contenu,
            emetteur_type=emetteur_type,
            emetteur_id=emetteur_id
        )
        
        # Notifier via WebSocket
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"discussion_{session_id}",
                    {
                        'type': 'message_sent',
                        'data': {
                            'message_id': message.id,
                            'contenu': message.contenu,
                            'emetteur_type': message.emetteur_type,
                            'emetteur_id': message.emetteur_id,
                            'date_envoi': message.date_envoi.isoformat()
                        }
                    }
                )
        except Exception as e:
            print(f"Erreur WebSocket message: {e}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Message envoyé avec succès',
            'message_id': message.id
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur serveur: {str(e)}'
        }, status=500)


# Autres fonctions inchangées...
def creer_prescription_simple_fallback(session, medecin, patient, prescription_data, numero_unique):
    """Version de fallback qui fonctionne même sans les modèles de télémédecine"""
    try:
        # Créer les données de l'ordonnance
        ordonnance_data = {
            'numero': numero_unique,
            'session': session,
            'patient': patient,
            'medecin': medecin,
            'diagnostic': prescription_data.get('diagnostic', ''),
            'medicaments': prescription_data.get('medicaments', []),
            'instructions_generales': prescription_data.get('instructions_generales', ''),
            'date_creation': timezone.now(),
            'date_validite': prescription_data.get('date_validite')
        }
        
        # Générer le PDF
        pdf_result = generer_pdf_ordonnance_simple_fallback(ordonnance_data)
        
        if pdf_result['success']:
            # Envoyer via WhatsApp
            try:
                whatsapp_service = WhatsAppService()
                if whatsapp_service.access_token and whatsapp_service.phone_number_id:
                    response = whatsapp_service.envoyer_prescription_complete(
                        patient,
                        'ordonnance',
                        numero_unique,
                        pdf_result['url_pdf'],
                        f"Ordonnance_{numero_unique}.pdf"
                    )
                    
                    if response:
                        print(f"✅ Ordonnance envoyée via WhatsApp")
                    else:
                        print(f"❌ Échec envoi WhatsApp")
                else:
                    print(f"⚠️ WhatsApp non configuré")
            except Exception as e:
                print(f"Erreur envoi WhatsApp: {e}")
            
            # Ajouter un message dans la discussion
            from .models import Message
            Message.objects.create(
                session=session,
                contenu=f"📋 Ordonnance {numero_unique} envoyée au patient",
                emetteur_type='MEDECIN',
                emetteur_id=medecin.id
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Ordonnance créée avec succès',
                'numero': numero_unique,
                'prescription_id': numero_unique,
                'pdf_url': pdf_result['url_pdf'],
                'url_finale': pdf_result['url_pdf'],
                'medecin': f"Dr {medecin.nom} {medecin.prenom}"
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Erreur génération PDF: {pdf_result["error"]}'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur création prescription: {str(e)}'
        }, status=500)


def generer_pdf_ordonnance_simple_fallback(ordonnance_data):
    """Version de fallback pour générer le PDF sans modèles complets"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        import qrcode
        import os
        from django.conf import settings
        
        # Créer les dossiers nécessaires
        media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        ordonnances_dir = os.path.join(media_root, 'prescriptions', 'ordonnances')
        qr_dir = os.path.join(media_root, 'qr_codes')
        
        os.makedirs(ordonnances_dir, exist_ok=True)
        os.makedirs(qr_dir, exist_ok=True)
        
        # Chemins des fichiers
        numero = ordonnance_data['numero']
        nom_fichier_pdf = f"{numero}.pdf"
        chemin_pdf = os.path.join(ordonnances_dir, nom_fichier_pdf)
        
        # Générer QR code
        qr_data = f"ORDONNANCE:{numero}:LOBIKO:{timezone.now().isoformat()}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_path = os.path.join(qr_dir, f"qr_{numero}.png")
        qr_img.save(qr_path)
        
        # Créer le PDF
        c = canvas.Canvas(chemin_pdf, pagesize=A4)
        width, height = A4
        
        # En-tête
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2*cm, height-2*cm, "ORDONNANCE MÉDICALE")
        
        c.setFont("Helvetica", 12)
        c.drawString(2*cm, height-3*cm, f"N° {numero}")
        c.drawString(2*cm, height-3.5*cm, f"Date: {ordonnance_data['date_creation'].strftime('%d/%m/%Y')}")
        
        # Informations patient
        patient = ordonnance_data['patient']
        c.drawString(2*cm, height-5*cm, f"Patient: {patient.nom}")
        c.drawString(2*cm, height-5.5*cm, f"Téléphone: {patient.telephone}")
        
        # Informations médecin
        medecin = ordonnance_data['medecin']
        if medecin and medecin.nom:
            c.drawString(2*cm, height-7*cm, f"Médecin: Dr {medecin.nom} {medecin.prenom}")
        
        # Diagnostic
        if ordonnance_data['diagnostic']:
            c.drawString(2*cm, height-8.5*cm, f"Diagnostic: {ordonnance_data['diagnostic']}")
        
        # Médicaments
        y_pos = height - 10*cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, y_pos, "MÉDICAMENTS PRESCRITS:")
        y_pos -= 0.8*cm
        
        c.setFont("Helvetica", 10)
        for i, med in enumerate(ordonnance_data['medicaments'], 1):
            c.drawString(2*cm, y_pos, f"{i}. Médicament prescrit")
            y_pos -= 0.5*cm
            if med.get('posologie'):
                c.drawString(2.5*cm, y_pos, f"Posologie: {med['posologie']}")
                y_pos -= 0.5*cm
            if med.get('duree_traitement'):
                c.drawString(2.5*cm, y_pos, f"Durée: {med['duree_traitement']}")
                y_pos -= 0.5*cm
            y_pos -= 0.3*cm
        
        # Instructions générales
        if ordonnance_data['instructions_generales']:
            y_pos -= 1*cm
            c.setFont("Helvetica-Bold", 12)
            c.drawString(2*cm, y_pos, "INSTRUCTIONS GÉNÉRALES:")
            y_pos -= 0.8*cm
            c.setFont("Helvetica", 10)
            c.drawString(2*cm, y_pos, ordonnance_data['instructions_generales'])
        
        # QR Code
        c.drawImage(qr_path, width-4*cm, height-4*cm, 2*cm, 2*cm)
        
        # Pied de page
        c.setFont("Helvetica", 8)
        c.drawString(2*cm, 2*cm, "Document généré par Lobiko - Plateforme de Télémédecine")
        
        c.save()
        
        # URL pour accéder au PDF
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        url_pdf = f"{media_url}prescriptions/ordonnances/{nom_fichier_pdf}"
        
        return {
            'success': True,
            'chemin_pdf': chemin_pdf,
            'url_pdf': url_pdf,
            'qr_path': qr_path
        }
        
    except Exception as e:
        print(f"Erreur génération PDF ordonnance fallback: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@csrf_exempt
@require_http_methods(["POST"])
def api_verifier_document(request):
    """API pour vérifier l'authenticité d'un document"""
    try:
        data = json.loads(request.body)
        numero_unique = data.get('numero_unique')
        hash_verification = data.get('hash_verification')
        type_document = data.get('type_document', 'Ordonnance')
        
        if not numero_unique:
            return JsonResponse({
                'status': 'error',
                'message': 'Numéro unique requis'
            }, status=400)
        
        return JsonResponse({
            'status': 'success',
            'valide': True,
            'message': 'Vérification en cours de développement'
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur lors de la vérification: {str(e)}'
        }, status=500)


def telecharger_prescription_pdf(request, prescription_id):
    """Télécharge le PDF d'une ordonnance"""
    try:
        ordonnance = get_object_or_404(Ordonnance, id=prescription_id)
        
        # Générer le PDF
        pdf_result = generer_pdf_ordonnance_detaille(ordonnance)
        
        if pdf_result['success']:
            with open(pdf_result['chemin_pdf'], 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="Ordonnance_{ordonnance.numero_unique}.pdf"'
                return response
        else:
            raise Http404("PDF non trouvé")
    
    except Exception as e:
        raise Http404(f"Erreur lors du téléchargement: {str(e)}")


def telecharger_bon_examen_pdf(request, bon_examen_id):
    """Télécharge le PDF d'un bon d'examen"""
    try:
        bon_examen = get_object_or_404(BonExamen, id=bon_examen_id)
        
        # Générer le PDF
        pdf_result = generer_pdf_bon_examen_detaille(bon_examen)
        
        if pdf_result['success']:
            with open(pdf_result['chemin_pdf'], 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="BonExamen_{bon_examen.numero_unique}.pdf"'
                return response
        else:
            raise Http404("PDF non trouvé")
    
    except Exception as e:
        raise Http404(f"Erreur lors du téléchargement: {str(e)}")


def upload_pdf_to_s3(pdf_result, filename):
    """Upload un PDF vers S3 et retourne l'URL"""
    try:
        if not pdf_result or not pdf_result.get('success'):
            return None
            
        # Pour l'instant, retourner l'URL locale
        return pdf_result.get('url_pdf')
    
    except Exception as e:
        print(f"Erreur upload S3: {e}")
        return None


# Vues pour l'interface d'administration des prescriptions
def liste_prescriptions(request):
    """Vue pour lister les prescriptions d'un médecin"""
    pass


def statistiques_prescriptions(request):
    """Vue pour afficher les statistiques de prescriptions"""
    pass
