from django.contrib import admin
from .models import CompteWhatsApp, Patient, Assureur, Assurance, Medecin, SessionDiscussion, Message

# Register your models here.
admin.site.register(CompteWhatsApp)
admin.site.register(Patient)
admin.site.register(Assureur)
admin.site.register(Assurance)
admin.site.register(Medecin)
admin.site.register(SessionDiscussion)
admin.site.register(Message)