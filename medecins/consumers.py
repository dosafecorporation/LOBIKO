import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from lobiko.models import SessionDiscussion, Message, MediaMessage
import logging
from django.contrib.auth.models import AnonymousUser

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("dashboard_updates", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("dashboard_updates", self.channel_name)

    async def receive(self, text_data):
        pass

    async def dashboard_update(self, event):
        await self.send(text_data=json.dumps(event))


class DiscussionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f"discussion_{self.session_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def discussion_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message
        }))

    async def new_message(self, event):
        # Envoie les messages aux clients
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'data': event['data']
        }))

    async def new_media(self, event):
        # Envoie les médias aux clients
        await self.send(text_data=json.dumps({
            'type': 'new_media',
            'data': event['data']
        }))

# Handler pour les prescriptions envoyées
    async def prescription_sent(self, event):
        """
        Handler pour les messages de prescription envoyée
        Corrige l'erreur: No handler for message type prescription_sent
        """
        try:
            prescription_data = event.get('data', {})
            
            # Envoyer les données de prescription au client
            await self.send(text_data=json.dumps({
                'type': 'prescription_sent',
                'data': {
                    'type': prescription_data.get('type', 'prescription_medicament'),
                    'numero': prescription_data.get('numero', ''),
                    'medecin': prescription_data.get('medecin', ''),
                    'date': prescription_data.get('date', ''),
                    'pdf_url': prescription_data.get('pdf_url', ''),
                    'prescription_id': prescription_data.get('prescription_id', ''),
                    'medicaments_count': prescription_data.get('medicaments_count', 0),
                    'priorite': prescription_data.get('priorite', 'Normal'),
                    'examens_count': prescription_data.get('examens_count', 0),
                    'bon_examen_id': prescription_data.get('bon_examen_id', ''),
                    'message': prescription_data.get('message', 'Prescription envoyée avec succès')
                }
            }))
            
            logger.info(f"Message prescription envoyé via WebSocket: {prescription_data.get('numero', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Erreur handler prescription_sent: {e}")
            # Envoyer un message d'erreur au client
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Erreur lors de l\'envoi de la prescription'
            }))

    # Handler pour les bons d'examens
    async def bon_examen_sent(self, event):
        """
        Handler pour les bons d'examens envoyés
        """
        try:
            bon_data = event.get('data', {})
            
            await self.send(text_data=json.dumps({
                'type': 'bon_examen_sent',
                'data': {
                    'type': 'bon_examen',
                    'numero': bon_data.get('numero', ''),
                    'medecin': bon_data.get('medecin', ''),
                    'date': bon_data.get('date', ''),
                    'pdf_url': bon_data.get('pdf_url', ''),
                    'bon_examen_id': bon_data.get('bon_examen_id', ''),
                    'examens_count': bon_data.get('examens_count', 0),
                    'priorite': bon_data.get('priorite', 'Normal'),
                    'message': bon_data.get('message', 'Bon d\'examens envoyé avec succès')
                }
            }))
            
            logger.info(f"Bon d'examens envoyé via WebSocket: {bon_data.get('numero', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Erreur handler bon_examen_sent: {e}")

    # NOUVEAU: Handler générique pour les erreurs
    async def error_message(self, event):
        """
        Handler pour les messages d'erreur
        """
        error_data = event.get('data', {})
        
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_data.get('message', 'Une erreur est survenue'),
            'code': error_data.get('code', 'UNKNOWN_ERROR')
        }))

    # NOUVEAU: Handler pour les notifications système
    async def system_notification(self, event):
        """
        Handler pour les notifications système
        """
        notification_data = event.get('data', {})
        
        await self.send(text_data=json.dumps({
            'type': 'system_notification',
            'data': {
                'message': notification_data.get('message', ''),
                'level': notification_data.get('level', 'info'),  # info, warning, error, success
                'timestamp': notification_data.get('timestamp', ''),
                'auto_dismiss': notification_data.get('auto_dismiss', True)
            }
        }))


# Fonction utilitaire pour envoyer des messages de prescription
async def envoyer_notification_prescription(session_id, prescription_data):
    """
    Fonction utilitaire pour envoyer une notification de prescription via WebSocket
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    room_group_name = f'discussion_{session_id}'
    
    try:
        await channel_layer.group_send(
            room_group_name,
            {
                'type': 'prescription_sent',
                'data': prescription_data
            }
        )
        logger.info(f"Notification prescription envoyée pour session {session_id}")
    except Exception as e:
        logger.error(f"Erreur envoi notification prescription: {e}")


# Fonction utilitaire pour envoyer des messages de bon d'examens
async def envoyer_notification_bon_examen(session_id, bon_data):
    """
    Fonction utilitaire pour envoyer une notification de bon d'examens via WebSocket
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    room_group_name = f'discussion_{session_id}'
    
    try:
        await channel_layer.group_send(
            room_group_name,
            {
                'type': 'bon_examen_sent',
                'data': bon_data
            }
        )
        logger.info(f"Notification bon d'examens envoyée pour session {session_id}")
    except Exception as e:
        logger.error(f"Erreur envoi notification bon d'examens: {e}")


# Fonction utilitaire pour envoyer des erreurs
async def envoyer_erreur_websocket(session_id, message_erreur, code_erreur="ERROR"):
    """
    Fonction utilitaire pour envoyer des messages d'erreur via WebSocket
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    room_group_name = f'discussion_{session_id}'
    
    try:
        await channel_layer.group_send(
            room_group_name,
            {
                'type': 'error_message',
                'data': {
                    'message': message_erreur,
                    'code': code_erreur
                }
            }
        )
        logger.warning(f"Message d'erreur envoyé pour session {session_id}: {message_erreur}")
    except Exception as e:
        logger.error(f"Erreur envoi message d'erreur: {e}")
    