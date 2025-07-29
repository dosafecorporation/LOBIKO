"""
URLs pour les API de télémédecine
"""

from django.urls import path
from . import telemedicine_views

urlpatterns = [
    # API pour les données de référence
    path('api/produits-pharmaceutiques/', telemedicine_views.api_produits_pharmaceutiques, name='api_produits_pharmaceutiques'),
    path('api/actes-medicaux/', telemedicine_views.api_actes_medicaux, name='api_actes_medicaux'),
    
    # API pour créer des prescriptions
    path('api/creer-prescription/', telemedicine_views.api_creer_prescription, name='api_creer_prescription'),
    path('api/creer-bon-examen/', telemedicine_views.api_creer_bon_examen, name='api_creer_bon_examen'),
    
    # API pour télécharger les PDF
    path('api/prescription/<int:prescription_id>/telecharger/', telemedicine_views.telecharger_prescription_pdf, name='telecharger_prescription_pdf'),
    path('api/bon-examen/<int:bon_examen_id>/telecharger/', telemedicine_views.telecharger_bon_examen_pdf, name='telecharger_bon_examen_pdf'),
    
    # API pour vérifier les documents
    path('api/verifier-document/', telemedicine_views.api_verifier_document, name='api_verifier_document'),
]

    