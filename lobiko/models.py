from django.db import models

# ✅ Compte WhatsApp (représente celui qui écrit)
class CompteWhatsApp(models.Model):
    whatsapp_id = models.CharField(max_length=50, unique=True)  # Ex : "243898209300"
    nom_utilisateur = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom_utilisateur or self.whatsapp_id

# ✅ Patient (celui qui est réellement consulté)
class Patient(models.Model):
    name = models.CharField(max_length=100)
    date_naissance = models.DateField(null=True, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# ✅ Assureur
class Assureur(models.Model):
    nom = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    contact = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.nom

# ✅ Lien entre patient et assureur
class Assurance(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    assureur = models.ForeignKey(Assureur, on_delete=models.CASCADE)
    numero_police = models.CharField(max_length=100)
    date_debut = models.DateField()
    date_fin = models.DateField()

    def __str__(self):
        return f"{self.patient.name} assuré par {self.assureur.nom}"

# ✅ Médecin
class Medecin(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    specialite = models.CharField(max_length=100, blank=True)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# ✅ Session de discussion (liée au patient ET au compte WhatsApp)
class SessionDiscussion(models.Model):
    compte = models.ForeignKey(CompteWhatsApp, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, null=True, blank=True, on_delete=models.SET_NULL)
    date_debut = models.DateTimeField(auto_now_add=True)
    date_transfert = models.DateTimeField(null=True, blank=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    prise_en_charge = models.BooleanField(default=False)

    def __str__(self):
        return f"Session {self.id} - {self.compte} → {self.patient}"

# ✅ Messages échangés dans la session
class Message(models.Model):
    session = models.ForeignKey(SessionDiscussion, on_delete=models.CASCADE, related_name='messages')
    emetteur = models.CharField(max_length=10, choices=[('bot', 'Bot'), ('patient', 'Patient'), ('medecin', 'Médecin')])
    contenu = models.TextField()
    horodatage = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.horodatage} | {self.emetteur.upper()} : {self.contenu[:40]}"
