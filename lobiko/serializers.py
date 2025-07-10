from rest_framework import serializers
from .models import (
    Patient, Assureur, Assurance,
    SessionDiscussion, Message, Medecin
)

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

class AssureurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assureur
        fields = '__all__'

class AssuranceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assurance
        fields = '__all__'

class MedecinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medecin
        fields = '__all__'

class SessionDiscussionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionDiscussion
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'