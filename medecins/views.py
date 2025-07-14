from datetime import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import requests
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
    medecin_id = request.session.get('medecin_id')
    if not medecin_id:
        return redirect('login_medecin')

    medecin = get_object_or_404(Medecin, id=medecin_id)
    session = get_object_or_404(SessionDiscussion, id=session_id)

    # Vérifie que le médecin est bien celui de la session
    if session.medecin != medecin:
        return redirect('dashboard_medecin')

    messages = Message.objects.filter(session=session).order_by('timestamp')
    form = MessageForm()

    if request.method == "POST":
        # Si le bouton "Terminer la session" est cliqué
        if 'close_session' in request.POST:
            session.date_fin = timezone.now()
            session.save()
            return redirect('dashboard_medecin')

        form = MessageForm(request.POST)
        if form.is_valid():
            message_texte = form.cleaned_data['message']

            # Envoi au bot
            bot_url = request.build_absolute_uri(reverse('bot:recevoir_message_medecin'))
            data = {
                'medecin_id': medecin_id,
                'session_id': session_id,
                'message': message_texte
            }
            try:
                response = requests.post(bot_url, data=data)
                if response.status_code == 200:
                    return redirect('discussion_session', session_id=session_id)
                else:
                    form.add_error(None, "Erreur lors de l'envoi au bot.")
            except Exception as e:
                form.add_error(None, f"Échec de la communication avec le bot : {str(e)}")

    return render(request, 'medecins/discussion.html', {
        'medecin': medecin,
        'session': session,
        'messages': messages,
        'form': form,
    })