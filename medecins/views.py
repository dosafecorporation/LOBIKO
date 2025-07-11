from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from .forms import MedecinInscriptionForm, MedecinLoginForm
from lobiko.models import Medecin  # Tu l’as bien précisé : il est dans l'app lobiko

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
                    request.session['medecin_id'] = medecin.id  # Auth "maison"
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
    return render(request, 'medecins/dashboard.html', {'medecin': medecin})
