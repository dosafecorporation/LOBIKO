import json
import requests
import logging
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.utils.timezone import now, timedelta
from lobiko.models import Medecin, Message, Patient, SessionDiscussion, Choices
from django.conf import settings
from datetime import datetime
import threading
import time

logger = logging.getLogger(__name__)

# Configuration
VERIFY_TOKEN = settings.VERIFY_TOKEN
ACCESS_TOKEN = settings.ACCESS_TOKEN
PHONE_NUMBER_ID = settings.PHONE_NUMBER_ID
REGISTRATION_TIMEOUT = 3600  # 1 heure en secondes

# Stockage temporaire des états utilisateurs
users_state = {}
registration_timers = {}

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

def cancel_registration(phone_number):
    """Annule l'inscription après le timeout"""
    if phone_number in users_state:
        send_whatsapp_message(phone_number, "⏱️ Délai d'inscription dépassé. Veuillez recommencer.")
        users_state.pop(phone_number, None)
        registration_timers.pop(phone_number, None)

def start_registration_timer(phone_number):
    """Démarre un timer pour annuler l'inscription après 1h"""
    if phone_number in registration_timers:
        registration_timers[phone_number].cancel()
    
    timer = threading.Timer(REGISTRATION_TIMEOUT, cancel_registration, args=[phone_number])
    timer.start()
    registration_timers[phone_number] = timer

def handle_stop_command(phone_number):
    """Gère la commande d'annulation"""
    if phone_number in users_state:
        users_state.pop(phone_number, None)
        if phone_number in registration_timers:
            registration_timers[phone_number].cancel()
            registration_timers.pop(phone_number, None)
        send_whatsapp_message(phone_number, "✅ Opération annulée. Tapez à nouveau pour recommencer.")
        return True
    return False

def handle_patient_registration(from_number, content):
    """Gère le processus d'inscription étape par étape"""
    # Vérifie si l'utilisateur veut annuler
    if content.lower() in ['stop', 'annuler', 'cancel']:
        if handle_stop_command(from_number):
            return None
    
    state = users_state.get(from_number, {})
    temp_data = state.get('temp_data', {})
    
    # Réinitialise le timer à chaque interaction
    if from_number in users_state:
        start_registration_timer(from_number)
    
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
        input_etat_civil = content.strip().lower()
        selected_etat = next((label for label, _ in Choices.ETAT_CIVIL 
                            if label.lower() == input_etat_civil), None)
        
        if not selected_etat:
            civil_options = ", ".join([label for label, _ in Choices.ETAT_CIVIL])
            return f"❌ État civil invalide. Choisissez parmi : {civil_options}"
        
        temp_data['etat_civil'] = selected_etat
        state.update({'step': 'awaiting_commune', 'temp_data': temp_data})
        commune_options = "\n".join([f"- {label}" for label, _ in Choices.COMMUNE])
        return f"Merci ! Dans quelle commune habitez-vous ?\n{commune_options}"
    
    elif state.get('step') == 'awaiting_commune':
        input_commune = content.strip().lower()
        selected_commune = next((label for label, _ in Choices.COMMUNE 
                               if label.lower() == input_commune), None)
        
        if not selected_commune:
            commune_options = "\n".join([f"- {label}" for label, _ in Choices.COMMUNE])
            return f"❌ Commune invalide. Veuillez choisir parmi :\n{commune_options}"
        
        temp_data['commune'] = selected_commune
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
            if from_number in registration_timers:
                registration_timers[from_number].cancel()
                registration_timers.pop(from_number, None)
            return f"✅ Inscription réussie, {temp_data['prenom']} ! Tapez 'médecin' pour parler à un professionnel ou 'stop' pour annuler."
        except Exception as e:
            logger.error(f"Erreur création patient: {str(e)}")
            users_state.pop(from_number, None)
            if from_number in registration_timers:
                registration_timers[from_number].cancel()
                registration_timers.pop(from_number, None)
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
            content = message.get('text', {}).get('body', '').strip().lower()

            if not from_number or not content:
                return JsonResponse({"status": "missing data"})

            logger.info(f"Message de {from_number}: {content}")

            # Vérifie si c'est une commande d'annulation
            if content in ['stop', 'annuler', 'cancel']:
                handle_stop_command(from_number)
                return JsonResponse({"status": "operation cancelled"})

            # Vérifier si le patient existe
            patient = Patient.objects.filter(telephone=from_number).first()

            if patient:
                # Gestion des sessions existantes
                active_session = SessionDiscussion.objects.filter(
                    patient=patient, 
                    date_fin__isnull=True
                ).order_by('-date_debut').first()

                if content == 'médecin':
                    if active_session:
                        send_whatsapp_message(from_number, "✅ Vous avez déjà une demande en cours. Un médecin va vous répondre.")
                    else:
                        session = create_patient_session(patient)
                        send_whatsapp_message(from_number, "✅ Votre demande a été enregistrée. Un médecin va vous contacter. Tapez 'stop' pour annuler.")
                    return JsonResponse({"status": "session handled"})

                if active_session:
                    # Vérifie si le patient veut arrêter la consultation
                    if content in ['stop consultation', 'arrêter consultation']:
                        active_session.date_fin = now()
                        active_session.save()
                        send_whatsapp_message(from_number, "✅ Consultation terminée. Merci !")
                        return JsonResponse({"status": "session ended"})
                    
                    # Enregistrer le message
                    Message.objects.create(
                        session=active_session,
                        contenu=content,
                        timestamp=now(),
                        emetteur_type='PATIENT',
                        emetteur_id=patient.id
                    )
                    return JsonResponse({"status": "message saved"})

                # Réponse par défaut pour patient enregistré
                send_whatsapp_message(from_number, "Tapez 'médecin' pour parler à un professionnel ou 'stop' pour annuler.")
                return JsonResponse({"status": "default response"})

            # Processus d'inscription
            if from_number not in users_state:
                users_state[from_number] = {
                    'step': 'awaiting_nom',
                    'temp_data': {},
                    'last_updated': now()
                }
                start_registration_timer(from_number)
                send_whatsapp_message(from_number, "👋 Bienvenue ! Pour commencer, quel est votre nom ? (Tapez 'stop' pour annuler)")
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
        message_content = data.get('message', '').strip()
        action = data.get('action', 'new_message')
        is_notification = data.get('is_notification', False)

        if not all([session_id, medecin_id]):
            return JsonResponse({"status": "missing data"}, status=400)

        session = SessionDiscussion.objects.get(id=session_id)
        medecin = Medecin.objects.get(id=medecin_id)

        # Vérification des permissions
        if session.medecin and session.medecin != medecin:
            return JsonResponse({"status": "unauthorized"}, status=403)

        if action == 'close_session':
            session.date_fin = now()
            session.save()
            message_content = "La consultation a été clôturée par le médecin."
            is_notification = True

        # Enregistrement du message en BDD
        message = Message.objects.create(
            session=session,
            contenu=message_content,
            timestamp=now(),
            emetteur_type='MEDECIN',
            emetteur_id=medecin.id
        )

        # Envoi au patient seulement si ce n'est pas une notification système
        if not is_notification:
            send_whatsapp_message(session.patient.telephone, message_content)

        return JsonResponse({
            "status": "success",
            "message_id": message.id,
            "timestamp": message.timestamp.isoformat()
        })

    except (SessionDiscussion.DoesNotExist, Medecin.DoesNotExist):
        return JsonResponse({"status": "not found"}, status=404)
    except Exception as e:
        logger.error(f"Erreur traitement message médecin: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)