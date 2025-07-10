from rest_framework import viewsets
from .models import (
    Patient, Assureur, Assurance,
    SessionDiscussion, Message, Medecin
)
from .serializers import (
    PatientSerializer, AssureurSerializer,
    AssuranceSerializer, SessionDiscussionSerializer, MessageSerializer,
    MedecinSerializer
)

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

class AssureurViewSet(viewsets.ModelViewSet):
    queryset = Assureur.objects.all()
    serializer_class = AssureurSerializer

class AssuranceViewSet(viewsets.ModelViewSet):
    queryset = Assurance.objects.all()
    serializer_class = AssuranceSerializer

class MedecinViewSet(viewsets.ModelViewSet):
    queryset = Medecin.objects.all()
    serializer_class = MedecinSerializer

class SessionDiscussionViewSet(viewsets.ModelViewSet):
    queryset = SessionDiscussion.objects.all()
    serializer_class = SessionDiscussionSerializer

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer