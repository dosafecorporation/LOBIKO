from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    CompteWhatsAppViewSet, PatientViewSet, AssureurViewSet, AssuranceViewSet,
    MedecinViewSet, SessionDiscussionViewSet, MessageViewSet
)

router = DefaultRouter()
router.register(r'whatsapp-accounts', CompteWhatsAppViewSet)
router.register(r'patients', PatientViewSet)
router.register(r'assureurs', AssureurViewSet)
router.register(r'assurances', AssuranceViewSet)
router.register(r'medecins', MedecinViewSet)
router.register(r'sessions', SessionDiscussionViewSet)
router.register(r'messages', MessageViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]