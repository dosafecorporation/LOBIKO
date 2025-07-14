import json
import requests
import logging
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.utils.timezone import now
from lobiko.models import Medecin, Message, Patient, SessionDiscussion, Choices
from django.conf import settings
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration
VERIFY_TOKEN = settings.VERIFY_TOKEN
ACCESS_TOKEN = settings.ACCESS_TOKEN
PHONE_NUMBER_ID = settings.PHONE_NUMBER_ID

# Stockage temporaire des états utilisateurs
users_state = {}

def is_valid_date(date_string):
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message}
    }
    try:
        resp = requests.post(url, json=data, headers=headers)
        resp.raise_for_status()
        logger.info(f"Message envoyé à {to}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur envoi message: {str(e)}")

def create_patient_session(patient):
    """Crée une nouvelle session de discussion pour un patient"""
    session = SessionDiscussion.objects.create(patient=patient)
    logger.info(f"Nouvelle session créée pour le patient {patient.id}")
    return session

def handle_patient_registration(from_number, content):
    """Gère le processus d'inscription étape par étape"""
    state = users_state.get(from_number, {})
    temp_data = state.get('temp_data', {})
    
    if state.get('step') == 'awaiting_nom':
        temp_data['nom'] = content
        state.update({'step': 'awaiting_postnom', 'temp_data': temp_data})
        return "Merci ! Veuillez entrer votre postnom :"
    
    elif state.get('step') == 'awaiting_postnom':
        temp_data['postnom'] = content
        state.update({'step': 'awaiting_prenom', 'temp_data': temp_data})
        return "Merci ! Veuillez entrer votre prénom :"
    
    elif state.get('step') == 'awaiting_prenom':
        temp_data['prenom'] = content
        state.update({
            'step': 'awaiting_sexe', 
            'temp_data': temp_data
        })
        sex_options = "/".join([label for code, label in Choices.SEXE])
        return f"Merci ! Veuillez indiquer votre sexe ({sex_options}) :"
    
    elif state.get('step') == 'awaiting_sexe':
        sexe = content.upper()[:1]  # Prend la première lettre majuscule
        if sexe not in [code for code, label in Choices.SEXE]:
            return f"❌ Sexe invalide. Options: {', '.join([label for code, label in Choices.SEXE])}"
        
        temp_data['sexe'] = sexe
        state.update({'step': 'awaiting_date_naissance', 'temp_data': temp_data})
        return "Merci ! Veuillez entrer votre date de naissance (AAAA-MM-JJ) :"
    
    elif state.get('step') == 'awaiting_date_naissance':
        if not is_valid_date(content):
            return "❌ Format de date invalide. Utilisez AAAA-MM-JJ."
        
        temp_data['date_naissance'] = content
        state.update({
            'step': 'awaiting_etat_civil', 
            'temp_data': temp_data
        })
        civil_options = ", ".join([label for label, _ in Choices.ETAT_CIVIL])
        return f"Merci ! Veuillez indiquer votre état civil ({civil_options}) :"
    
    elif state.get('step') == 'awaiting_etat_civil':
        temp_data['etat_civil'] = content
        state.update({'step': 'awaiting_commune', 'temp_data': temp_data})
        commune_options = "\n".join([f"- {label}" for label, _ in Choices.COMMUNE])
        return f"Merci ! Dans quelle commune habitez-vous ?\n{commune_options}"
    
    elif state.get('step') == 'awaiting_commune':
        if content not in [label for label, _ in Choices.COMMUNE]:
            return "❌ Commune invalide. Veuillez choisir parmi la liste."
        
        temp_data['commune'] = content
        state.update({'step': 'awaiting_quartier', 'temp_data': temp_data})
        return "Merci ! Veuillez indiquer votre quartier :"
    
    elif state.get('step') == 'awaiting_quartier':
        temp_data['quartier'] = content
        state.update({'step': 'awaiting_avenue', 'temp_data': temp_data})
        return "Merci ! Veuillez indiquer votre avenue/rue (facultatif) :"
    
    elif state.get('step') == 'awaiting_avenue':
        temp_data['avenue'] = content if content else None
        state.update({
            'step': 'awaiting_langue', 
            'temp_data': temp_data
        })
        langue_options = ", ".join([label for code, label in Choices.LANGUES])
        return f"Merci ! Quelle est votre langue préférée ? ({langue_options})"
    
    elif state.get('step') == 'awaiting_langue':
        langue = next((code for code, label in Choices.LANGUES if label.lower() == content.lower()), None)
        if not langue:
            return f"❌ Langue invalide. Veuillez choisir parmi la liste."
        
        temp_data['langue_preferee'] = [langue]
        
        # Création du patient
        try:
            Patient.objects.create(
                whatsapp_id=from_number,
                nom=temp_data['nom'],
                postnom=temp_data['postnom'],
                prenom=temp_data['prenom'],
                sexe=temp_data['sexe'],
                date_naissance=temp_data['date_naissance'],
                etat_civil=temp_data['etat_civil'],
                telephone=from_number,
                commune=temp_data['commune'],
                quartier=temp_data['quartier'],
                avenue=temp_data['avenue'],
                langue_preferee=temp_data['langue_preferee'],
            )
            users_state.pop(from_number, None)
            return f"✅ Inscription réussie, {temp_data['prenom']} ! Tapez 'médecin' pour parler à un professionnel."
        except Exception as e:
            logger.error(f"Erreur création patient: {str(e)}")
            users_state.pop(from_number, None)
            return "❌ Erreur lors de l'inscription. Veuillez recommencer."
    
    return None

@csrf_exempt
def webhook(request):
    if request.method == "GET":
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("Webhook validé")
            return HttpResponse(challenge)
        return HttpResponseForbidden()

    elif request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            entry = data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            message = value.get('messages', [{}])[0]
            
            from_number = message.get('from')
            content = message.get('text', {}).get('body', '').strip()

            if not from_number or not content:
                return JsonResponse({"status": "missing data"})

            logger.info(f"Message de {from_number}: {content}")

            # Vérifier si le patient existe
            patient = Patient.objects.filter(telephone=from_number).first()

            if patient:
                # Gestion des sessions existantes
                active_session = SessionDiscussion.objects.filter(
                    patient=patient, 
                    date_fin__isnull=True
                ).order_by('-date_debut').first()

                if content.lower() == 'médecin':
                    if active_session:
                        send_whatsapp_message(from_number, "✅ Vous avez déjà une demande en cours. Un médecin va vous répondre.")
                    else:
                        create_patient_session(patient)
                        send_whatsapp_message(from_number, "✅ Votre demande a été enregistrée. Un médecin va vous contacter.")
                    return JsonResponse({"status": "session handled"})

                if active_session:
                    # Enregistrer le message
                    Message.objects.create(
                        session=active_session,
                        contenu=content,
                        timestamp=now(),
                        emetteur_patient=patient,
                        emetteur_type='PATIENT',
                        emetteur_id=patient.id
                    )
                    return JsonResponse({"status": "message saved"})

                # Réponse par défaut pour patient enregistré
                send_whatsapp_message(from_number, "Tapez 'médecin' pour parler à un professionnel.")
                return JsonResponse({"status": "default response"})

            # Processus d'inscription
            if from_number not in users_state:
                users_state[from_number] = {
                    'step': 'awaiting_nom',
                    'temp_data': {},
                    'last_updated': now()
                }
                send_whatsapp_message(from_number, "👋 Bienvenue ! Pour commencer, quel est votre nom ?")
                return JsonResponse({"status": "registration started"})

            # Gestion des étapes d'inscription
            response = handle_patient_registration(from_number, content)
            if response:
                send_whatsapp_message(from_number, response)
                return JsonResponse({"status": "registration step"})

            return JsonResponse({"status": "processed"})

        except Exception as e:
            logger.error(f"Erreur webhook: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return HttpResponse(status=405)

@csrf_exempt
def recevoir_message_medecin(request):
    if request.method != "POST":
        return JsonResponse({"status": "invalid method"}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        session_id = data.get('session_id')
        medecin_id = data.get('medecin_id')
        contenu = data.get('message', '').strip()

        if not all([session_id, medecin_id, contenu]):
            return JsonResponse({"status": "missing data"}, status=400)

        session = SessionDiscussion.objects.get(id=session_id)
        medecin = Medecin.objects.get(id=medecin_id)

        if session.medecin and session.medecin != medecin:
            return JsonResponse({"status": "unauthorized"}, status=403)

        # Si premier message, associer le médecin à la session
        if not session.medecin:
            session.medecin = medecin
            session.save()

        # Enregistrer le message
        Message.objects.create(
            session=session,
            contenu=contenu,
            timestamp=now(),
            emetteur_medecin=medecin,
            emetteur_type='MEDECIN',
            emetteur_id=medecin.id
        )

        # Envoyer au patient
        send_whatsapp_message(session.patient.telephone, contenu)

        return JsonResponse({"status": "success"})

    except (SessionDiscussion.DoesNotExist, Medecin.DoesNotExist):
        return JsonResponse({"status": "not found"}, status=404)
    except Exception as e:
        logger.error(f"Erreur message médecin: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)