from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.utils import timezone
from .forms import LoginForm
from lobiko.models import Medecin, SessionDiscussion, Message, Patient

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            tel = form.cleaned_data['telephone']
            try:
                medecin = Medecin.objects.get(telephone=tel)
                request.session['medecin_id'] = medecin.id
                return redirect('medecins:dashboard')
            except Medecin.DoesNotExist:
                messages.error(request, "Aucun médecin trouvé avec ce numéro.")
    else:
        form = LoginForm()
    return render(request, 'medecins/login.html', {'form': form})

def logout_view(request):
    request.session.flush()
    return redirect('medecins:login')

def get_current_medecin(request):
    med_id = request.session.get('medecin_id')
    return Medecin.objects.get(id=med_id) if med_id else None

def dashboard(request):
    medecin = get_current_medecin(request)
    if not medecin:
        return redirect('medecins:login')
    
    sessions = SessionDiscussion.objects.filter(medecin=medecin, date_fin__isnull=True)
    return render(request, 'medecins/dashboard.html', {'medecin': medecin, 'sessions': sessions})

def session_detail(request, session_id):
    medecin = get_current_medecin(request)
    if not medecin:
        return redirect('medecins:login')
    
    session = get_object_or_404(SessionDiscussion, id=session_id, medecin=medecin)
    messages_list = Message.objects.filter(session=session).order_by('timestamp')
    return render(request, 'medecins/session_detail.html', {
        'session': session,
        'messages': messages_list
    })

def send_message(request, session_id):
    medecin = get_current_medecin(request)
    if not medecin:
        return redirect('medecins:login')

    session = get_object_or_404(SessionDiscussion, id=session_id, medecin=medecin)
    
    if request.method == 'POST':
        contenu = request.POST.get('contenu')
        if contenu:
            Message.objects.create(session=session, emetteur='medecin', contenu=contenu)
    return redirect('medecins:session_detail', session_id=session.id)

def close_session(request, session_id):
    medecin = get_current_medecin(request)
    if not medecin:
        return redirect('medecins:login')
    
    session = get_object_or_404(SessionDiscussion, id=session_id, medecin=medecin)
    session.date_fin = timezone.now()
    session.save()
    messages.success(request, "Session clôturée.")
    return redirect('medecins:dashboard')
