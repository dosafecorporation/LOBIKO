# bot/urls.py
from django.urls import path
from .views import webhook
from bot import views

app_name = 'bot'
urlpatterns = [
    path('webhook/', webhook, name='whatsapp_webhook'),
    path('recevoir-message/', views.recevoir_message_medecin, name='recevoir_message_medecin'),
]
