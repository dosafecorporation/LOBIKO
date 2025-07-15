from datetime import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import requests
from django.contrib import messages as django_messages
from .forms import MedecinInscriptionForm, MedecinLoginForm, MessageForm
from lobiko.models import Medecin, Message, SessionDiscussion  # Tu l’as bien précisé : il est dans l'app lobiko

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

    # On peut aussi récupérer les sessions en cours du médecin connecté si tu veux (optionnel)
    sessions_en_cours = SessionDiscussion.objects.filter(medecin=medecin, date_fin__isnull=True).select_related('patient')

    context = {
        'medecin': medecin,
        'sessions_en_attente': sessions_en_attente,
        'sessions_en_cours': sessions_en_cours,
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
        # Rediriger vers la page de discussion avec ce patient (à créer)
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

    # Récupération des messages
    messages_list = Message.objects.filter(session=session).order_by('timestamp')
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
                'message': "Le médecin a clôturé la consultation.",
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
        'messages': messages_list,
        'form': form,
    })