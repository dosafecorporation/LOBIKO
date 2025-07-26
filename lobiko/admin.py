from django.contrib import admin
from .models import Patient, Assureur, Assurance, SessionDiscussion, Medecin, Message, MediaMessage,TarifConsultation

# Register your models here.
admin.site.register(Patient)
admin.site.register(Assureur)
admin.site.register(Assurance)
admin.site.register(SessionDiscussion)
admin.site.register(Medecin)
admin.site.register(Message)
admin.site.register(MediaMessage)
admin.site.register(TarifConsultation)

# Import de l'administration de télémédecine
from . import telemedicine_admin
