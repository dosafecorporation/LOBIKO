from django.contrib import admin
from .models import Patient, Assureur, Assurance, SessionDiscussion, Medecin, Message

# Register your models here.
admin.site.register(Patient)
admin.site.register(Assureur)
admin.site.register(Assurance)
admin.site.register(SessionDiscussion)
admin.site.register(Medecin)
admin.site.register(Message)