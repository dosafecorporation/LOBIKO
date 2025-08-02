from asyncio.log import logger
from itertools import chain
import boto3
from django.utils import timezone
from django.http import FileResponse, Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import requests
from django.contrib import messages as django_messages
from botocore.exceptions import ClientError
from bot.utils import send_whatsapp_message
from lobikohealth import settings
from .forms import MedecinInscriptionForm, MedecinLoginForm, MessageForm
from lobiko.models import Medecin, MediaMessage, Message, SessionDiscussion,TarifConsultation
import secrets
from urllib.parse import quote, urlparse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

#added
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.db.models import Avg, Sum
from decimal import Decimal

def inscription_medecin(request):
    if request.method == "POST":
        form = MedecinInscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login_medecin')  # ou autre page
    else:
        form = MedecinInscriptionForm()
    return render(request, 'medecins/inscription.html', {'form': form})

def login_medecin(request):
    if request.method == "POST":
        form = MedecinLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            try:
                medecin = Medecin.objects.get(username=username)
                if medecin.check_password(password):
                    request.session['medecin_id'] = medecin.id
                    return redirect('dashboard_medecin')
                else:
                    messages.error(request, "Mot de passe incorrect.")
            except Medecin.DoesNotExist:
                messages.error(request, "Nom d'utilisateur introuvable.")
    else:
        form = MedecinLoginForm()
    return render(request, 'medecins/login.html', {'form': form})

def logout_medecin(request):
    request.session.flush()
    return redirect('login_medecin')

def dashboard_medecin(request):
    medecin_id = request.session.get('medecin_id')
    if not medecin_id:
        return redirect('login_medecin')
    try:
        medecin = Medecin.objects.get(id=medecin_id)
    except Medecin.DoesNotExist:
        return redirect('login_medecin')

    # Récupérer les sessions en attente (sans médecin attribué)
    sessions_en_attente = SessionDiscussion.objects.filter(medecin__isnull=True, date_fin__isnull=True).select_related('patient')

    # Récupérer les sessions en cours du médecin connecté si tu veux (optionnel)
    sessions_en_cours = SessionDiscussion.objects.filter(medecin=medecin, date_fin__isnull=True).select_related('patient')

    # Consultations du mois
    consultations_mois = SessionDiscussion.objects.filter(
        medecin=medecin,
        date_debut__month=timezone.now().month,
        date_debut__year=timezone.now().year,
    ).count()

    # Récupérer les sessions du mois
    consult = SessionDiscussion.objects.filter(
        medecin=medecin,
        date_debut__month=timezone.now().month,
        date_debut__year=timezone.now().year,
        date_fin__isnull=False
    )

    commission_mois = Decimal("0.00")

    for session in consult:
        tarif = TarifConsultation.objects.filter(
            medecin=medecin,
            date_debut__lte=session.date_debut.date()
        ).order_by("-date_debut").first()

        if tarif:
            commission_mois += tarif.montant

        # Activité récente (5 dernières)
    sessions_recentes = SessionDiscussion.objects.filter(
        medecin=medecin
    ).order_by("-date_debut")[:5]

    context = {
        'medecin': medecin,
        'sessions_en_attente': sessions_en_attente,
        'sessions_en_cours': sessions_en_cours,
        "consultations_mois": consultations_mois,
        "sessions_recentes": sessions_recentes,
        "commission_mois": commission_mois,
    }
    return render(request, 'medecins/dashboard.html', context)

def accepter_session(request, session_id):
    medecin_id = request.session.get('medecin_id')
    if not medecin_id:
        return redirect('login_medecin')
    try:
        medecin = Medecin.objects.get(id=medecin_id)
    except Medecin.DoesNotExist:
        return redirect('login_medecin')

    session = get_object_or_404(SessionDiscussion, id=session_id)

    # Si session sans médecin et pas terminée, on l’attribue au médecin connecté
    if session.medecin is None and session.date_fin is None:
        session.medecin = medecin
        session.save()
        # Rediriger vers la page de discussion avec ce patient
        send_dashboard_update()

        # Préparation du message cordial pour le patient
        patient_tel = session.patient.telephone
        medecin_nom = f"Dr {medecin.prenom} {medecin.nom}"
        specialite = f", {medecin.specialite}" if getattr(medecin, 'specialite', None) else ""
        
        patient_message = (
            f"You are now in contact with {medecin_nom}{specialite}.\n"
            "All your messages from now on will be sent directly to them, and they will contact you shortly😊."
        )

        # Envoi du message WhatsApp
        send_whatsapp_message(patient_tel, patient_message)
        
        return redirect('discussion_session', session_id=session.id)

    # Sinon on revient au dashboard
    return redirect('dashboard_medecin')

def discussion_session(request, session_id):
    # Vérification de l'authentification
    medecin_id = request.session.get('medecin_id')
    if not medecin_id:
        return redirect('login_medecin')

    medecin = get_object_or_404(Medecin, id=medecin_id)
    session = get_object_or_404(SessionDiscussion, id=session_id)

    # Vérification des permissions
    if session.medecin and session.medecin != medecin:
        return redirect('dashboard_medecin')

    # Récupération des messages et des médias
    messages_list = Message.objects.filter(session=session).order_by('timestamp')
    media_files = MediaMessage.objects.filter(session=session).order_by('timestamp')

    # Fusionner les messages et médias par ordre chronologique
    all_messages = sorted(
        chain(messages_list, media_files),
        key=lambda x: x.timestamp
    )

    form = MessageForm(request.POST or None)

    if request.method == "POST":
        # Gestion de la fermeture de session
        if 'close_session' in request.POST:
            session.date_fin = timezone.now()
            session.save()
            
            # Envoi notification au bot
            bot_url = request.build_absolute_uri(reverse('bot:recevoir_message_medecin'))
            notification_data = {
                'medecin_id': medecin_id,
                'session_id': session_id,
                'message': "The doctor closed the consultation.",
                'is_notification': True,
                'action': 'close_session'
            }
            try:
                requests.post(bot_url, json=notification_data, timeout=5)
            except requests.RequestException:
                pass
            
            django_messages.success(request, "La session a été clôturée.")
            return redirect('dashboard_medecin')

        # Gestion de l'envoi de message
        if form.is_valid():
            message_content = form.cleaned_data['message']
            
            # Envoi au bot via webhook (sans créer le message en BDD ici)
            bot_url = request.build_absolute_uri(reverse('bot:recevoir_message_medecin'))
            message_data = {
                'medecin_id': medecin_id,
                'session_id': session_id,
                'message': message_content,
                'is_notification': False,
                'action': 'new_message'
            }

            try:
                response = requests.post(
                    bot_url,
                    json=message_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    django_messages.success(request, "Message envoyé avec succès.")
                else:
                    raise requests.RequestException(f"Code {response.status_code}: {response.text}")
                
                return redirect('discussion_session', session_id=session_id)

            except requests.RequestException as e:
                django_messages.error(
                    request, 
                    f"Erreur lors de l'envoi du message: {str(e)}"
                )
                return redirect('discussion_session', session_id=session_id)

    return render(request, 'medecins/discussion.html', {
        'medecin': medecin,
        'session': session,
        'all_messages': all_messages,
        'form': form,
    })

def generate_jitsi_link(session, medecin):
    """Génère un lien Jitsi pour une session"""
    room_name = f"consult-{medecin.id}-{session.patient.id}-{secrets.token_hex(4)}"
    base_url = "https://meet.jit.si/"
    url = base_url + quote(room_name)
    url += f"#user.displayName=Dr.{quote(medecin.nom)}"
    return url

@require_POST
def initier_appel_jitsi(request, session_id):
    medecin_id = request.session.get('medecin_id')
    if not medecin_id:
        return redirect('login_medecin')

    medecin = get_object_or_404(Medecin, id=medecin_id)
    session = get_object_or_404(SessionDiscussion, id=session_id)

    # Vérification des permissions
    if session.medecin != medecin:
        return redirect('dashboard_medecin')

    # Génération du lien Jitsi
    jitsi_link = generate_jitsi_link(session, medecin)
    message_content = f"🔊 Link for video consultation: {jitsi_link}"

    # Préparation des données pour le bot
    bot_url = request.build_absolute_uri(reverse('bot:recevoir_message_medecin'))
    message_data = {
        'medecin_id': medecin_id,
        'session_id': session_id,
        'message': message_content,
        'is_notification': False,
        'action': 'new_message'
    }

    try:
        # Envoi au bot qui va gérer l'enregistrement et l'envoi WhatsApp
        response = requests.post(
            bot_url,
            json=message_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        if response.status_code == 200:
            django_messages.success(request, "Lien d'appel envoyé avec succès!")
        else:
            # Si le bot répond avec une erreur, on la transmet
            error_data = response.json()
            raise requests.RequestException(error_data.get('message', 'Erreur inconnue'))

    except requests.RequestException as e:
        django_messages.error(
            request, 
            f"Erreur lors de l'envoi du lien d'appel: {str(e)}"
        )
        logger.error(f"Erreur appel Jitsi - session {session_id}: {str(e)}")

    return redirect('discussion_session', session_id=session_id)

def proxy_download(request, session_id, media_id):
    medecin_id = request.session.get('medecin_id')
    if not medecin_id:
        return redirect('login_medecin')

    medecin = get_object_or_404(Medecin, id=medecin_id)
    session = get_object_or_404(SessionDiscussion, id=session_id)

    # Vérification des permissions
    if session.medecin != medecin:
        return redirect('dashboard_medecin')
    
    try:
        media = MediaMessage.objects.get(id=media_id)
        
        # Vérification des permissions
        if not request.session.get('medecin_id'):
            raise Http404
        
        medecin = Medecin.objects.get(id=request.session['medecin_id'])
        if media.session.medecin != medecin:
            raise Http404
        
        s3 = boto3.client('s3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        try:
            # Utilisez la clé S3 stockée dans le modèle
            response = s3.get_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=media.s3_key
            )
            
            # Créez la réponse avec les bons headers
            file_response = FileResponse(
                response['Body'],
                content_type=response['ContentType'],
                as_attachment=True,
                filename=media.file_name  # Utilise le nom stocké en BDD
            )
            return file_response
            
        except ClientError as e:
            logger.error(f"Erreur S3: {str(e)}")
            raise Http404("Fichier introuvable sur S3")
            
    except (MediaMessage.DoesNotExist, Medecin.DoesNotExist):
        raise Http404("Ressource introuvable")
    
def send_dashboard_update():
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "dashboard_updates",
        {
            "type": "dashboard_update",
            "message": "Mise à jour sur les consultations"
        }
    )