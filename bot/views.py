import json
import requests
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.utils.timezone import now
from datetime import timedelta
from lobiko.models import Medecin, Message, Patient, SessionDiscussion
from django.conf import settings

logger = logging.getLogger(__name__)

# Configuration (mettre dans settings.py)
VERIFY_TOKEN = settings.VERIFY_TOKEN
ACCESS_TOKEN = settings.ACCESS_TOKEN
PHONE_NUMBER_ID = settings.PHONE_NUMBER_ID

# Stockage simple en mémoire (attention : multi-processes ou déploiement multi-instance => envisager cache redis)
users_state = {}

valid_sexes = ['Homme', 'Femme']
valid_langues = ['Français', 'Anglais', 'Lingala', 'Swahili', 'Kikongo', 'Tshiluba']

def is_valid_date(date_string):
    from datetime import datetime
    try:
        d = datetime.strptime(date_string, '%Y-%m-%d')
        return d.strftime('%Y-%m-%d') == date_string
    except ValueError:
        return False

def send_reply(to, message):
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
    resp = requests.post(url, json=data, headers=headers)
    if resp.status_code != 200:
        logger.error(f"Erreur envoi message: {resp.text}")
    else:
        logger.info(f"Réponse envoyée à {to} : {message}")

@csrf_exempt
def webhook(request):
    if request.method == "GET":
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("Webhook validé par Meta")
            return HttpResponse(challenge)
        else:
            return HttpResponseForbidden()

    elif request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        # Exemple: vérifier présence message
        try:
            entry = data.get('entry', [])[0]
            changes = entry.get('changes', [])[0]
            value = changes.get('value', {})
            messages = value.get('messages', [])
            if not messages:
                return JsonResponse({"status": "no messages"})
            message = messages[0]
            from_number = message.get('from')
            content = message.get('text', {}).get('body', '').strip()

            if not from_number or not content:
                return JsonResponse({"status": "missing from or content"})

            logger.info(f"Message reçu de {from_number}: {content}")

            # Gestion session expiration 1h
            now_ts = now()
            user_state = users_state.get(from_number)
            if user_state:
                last_update = user_state.get('last_updated')
                if last_update and (now_ts - last_update) > timedelta(hours=1):
                    users_state.pop(from_number)
                    send_reply(from_number, "⏳ Votre session a expiré après 1h d'inactivité. Recommençons !")
                    return JsonResponse({"status": "session expired"})

            # Commande annuler
            if content.lower() == "annuler":
                users_state.pop(from_number, None)
                send_reply(from_number, "🛑 Votre session a été annulée. Vous pouvez recommencer à tout moment.")
                return JsonResponse({"status": "session cancelled"})

            # Check patient inscrit via ORM
            try:
                patient = Patient.objects.filter(telephone=from_number).first()
            except Exception as e:
                logger.error(f"Erreur DB: {e}")
                send_reply(from_number, "Désolé, une erreur est survenue lors de la vérification du compte.")
                return JsonResponse({"status": "db error"})

            if patient:
                try:
                    session_active = SessionDiscussion.objects.filter(
                        patient=patient,
                        date_fin__isnull=True,
                        medecin__isnull=False
                    ).latest('date_debut')  # on prend la plus récente
                except SessionDiscussion.DoesNotExist:
                    session_active = None

                if session_active:
                    # Sauvegarde le message dans la BDD
                    Message.objects.create(
                        session=session_active,
                        contenu=content,
                        emetteur='patient',
                        patient=patient,
                        timestamp=now()
                    )

                    # À ce stade, le médecin verra ce message depuis son interface automatiquement.
                    # (optionnel) Tu pourrais aussi ajouter un système de "notification visuelle" plus tard.

                    return JsonResponse({"status": "message saved from patient"})

            # Gestion conversation en fonction du state
            if state and state.get('step') == 'awaiting_medecin_confirmation':
                rep = content.lower()
                if rep == 'oui':
                    try:
                        # Vérifie s'il n'y a pas déjà une session en attente
                        session_existante = SessionDiscussion.objects.filter(
                            patient=patient, date_fin__isnull=True
                        ).exists()

                        if not session_existante:
                            SessionDiscussion.objects.create(patient=patient)
                            send_reply(from_number, "✅ Parfait. Un médecin va bientôt vous répondre, merci de patienter.")
                        else:
                            send_reply(from_number, "🔁 Une demande est déjà en attente. Un médecin va vous répondre bientôt.")
                    except Exception as e:
                        logger.error(f"Erreur création session: {e}")
                        send_reply(from_number, "❌ Une erreur est survenue. Merci de réessayer plus tard.")
                    users_state.pop(from_number, None)
                elif rep == 'non':
                    send_reply(from_number, "🛑 Pas de souci. N'hésitez pas à revenir quand vous le souhaitez.")
                    users_state.pop(from_number, None)
                else:
                    send_reply(from_number, "❓ Merci de répondre par 'oui' ou 'non'. Souhaitez-vous parler à un médecin maintenant ?")
                return JsonResponse({"status": "handled medecin confirmation"})

            # Début inscription
            state = users_state.get(from_number)
            if not state:
                users_state[from_number] = {
                    'step': 'awaiting_nom',
                    'last_updated': now_ts,
                    'temp_data': {}
                }
                send_reply(from_number, "👋 Bienvenue ! Quel est votre nom ?")
                return JsonResponse({"status": "started inscription"})

            # Processus inscription
            state = users_state[from_number]
            state['last_updated'] = now_ts
            temp_data = state.get('temp_data', {})

            # Logique étapes inscription (exemple simplifié)
            step = state.get('step')
            if step == 'awaiting_nom':
                temp_data['nom'] = content
                state['step'] = 'awaiting_postnom'
                send_reply(from_number, "Merci ! Veuillez entrer votre postnom :")
            elif step == 'awaiting_postnom':
                temp_data['postnom'] = content
                state['step'] = 'awaiting_prenom'
                send_reply(from_number, "Merci ! Veuillez entrer votre prénom :")
            elif step == 'awaiting_prenom':
                temp_data['prenom'] = content
                state['step'] = 'awaiting_sexe'
                send_reply(from_number, f"Merci ! Veuillez entrer votre sexe ({', '.join(valid_sexes)}) :")
            elif step == 'awaiting_sexe':
                sexe = content.capitalize()
                if sexe not in valid_sexes:
                    send_reply(from_number, f"❌ Sexe invalide. Choisissez parmi : {', '.join(valid_sexes)}")
                    return JsonResponse({"status": "invalid sexe"})
                temp_data['sexe'] = sexe
                state['step'] = 'awaiting_date_naissance'
                send_reply(from_number, "Merci ! Veuillez entrer votre date de naissance (YYYY-MM-DD) :")
            elif step == 'awaiting_date_naissance':
                if not is_valid_date(content):
                    send_reply(from_number, "❌ Format ou date invalide. Utilisez le format YYYY-MM-DD, ex: 1995-08-22")
                    return JsonResponse({"status": "invalid date"})
                temp_data['date_naissance'] = content
                state['step'] = 'awaiting_etat_civil'
                send_reply(from_number, "Merci ! Veuillez entrer votre état civil :")
            elif step == 'awaiting_etat_civil':
                temp_data['etat_civil'] = content
                state['step'] = 'awaiting_adresse'
                send_reply(from_number, "Merci ! Veuillez entrer votre adresse :")
            elif step == 'awaiting_adresse':
                temp_data['adresse'] = content
                state['step'] = 'awaiting_langue_preferee'
                send_reply(from_number, f"Merci ! Veuillez entrer votre langue préférée ({', '.join(valid_langues)}) :")
            elif step == 'awaiting_langue_preferee':
                langue = content.capitalize()
                if langue not in valid_langues:
                    send_reply(from_number, f"❌ Langue invalide. Choisissez parmi : {', '.join(valid_langues)}")
                    return JsonResponse({"status": "invalid langue"})
                temp_data['langue_preferee'] = langue

                # Création patient en base
                try:
                    patient = Patient.objects.create(
                        whatsapp_id=from_number,
                        nom=temp_data['nom'],
                        postnom=temp_data['postnom'],
                        prenom=temp_data['prenom'],
                        sexe=temp_data['sexe'],
                        date_naissance=temp_data['date_naissance'],
                        etat_civil=temp_data['etat_civil'],
                        telephone=from_number,
                        adresse=temp_data['adresse'],
                        langue_preferee=temp_data['langue_preferee'],
                    )
                    send_reply(from_number, f"✅ Merci {temp_data['nom']}, votre compte a été créé avec succès. Bienvenue sur Lobiko 👨‍⚕️ !")
                except Exception as e:
                    logger.error(f"Erreur création patient: {e}")
                    send_reply(from_number, "Désolé, une erreur est survenue lors de la création du compte. Recommençons !")

                # Nettoyage état
                users_state.pop(from_number, None)

            else:
                send_reply(from_number, "Désolé, une erreur est survenue. On recommence.")
                users_state.pop(from_number, None)

            return JsonResponse({"status": "message processed"})

        except Exception as e:
            logger.error(f"Erreur traitement webhook: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return HttpResponse(status=405)

@csrf_exempt
def recevoir_message_medecin(request):
    if request.method != "POST":
        return JsonResponse({"status": "invalid method"}, status=405)

    data = request.POST
    session_id = data.get('session_id')
    medecin_id = data.get('medecin_id')
    contenu = data.get('message', '').strip()

    if not session_id or not medecin_id or not contenu:
        return JsonResponse({"status": "missing fields"}, status=400)

    try:
        session = SessionDiscussion.objects.get(id=session_id)
        medecin = Medecin.objects.get(id=medecin_id)
    except (SessionDiscussion.DoesNotExist, Medecin.DoesNotExist):
        return JsonResponse({"status": "invalid session or medecin"}, status=404)

    # Vérifie que ce médecin est bien affecté à cette session
    if session.medecin != medecin:
        return JsonResponse({"status": "unauthorized"}, status=403)

    # Sauvegarde le message
    Message.objects.create(
        session=session,
        contenu=contenu,
        emetteur='medecin',
        medecin=medecin,
        timestamp=now()
    )

    # Envoie au patient
    numero = session.patient.telephone
    send_reply(numero, contenu)

    return JsonResponse({"status": "ok"})