# ==========================================
# CONFIGURATION AWS S3 ADAPTÉE POUR TÉLÉMÉDECINE LOBIKO
# ==========================================

import os

# ==========================================
# VOTRE CONFIGURATION S3 EXISTANTE (CONSERVÉE)
# ==========================================

# Configuration Amazon S3 existante
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = 'eu-north-1'  # Votre région existante
AWS_S3_CUSTOM_DOMAIN = f'{os.getenv("AWS_STORAGE_BUCKET_NAME")}.s3.amazonaws.com'
AWS_DEFAULT_ACL = 'public-read'
AWS_QUERYSTRING_AUTH = False
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
    'ContentDisposition': 'attachment',
}

# ==========================================
# CONFIGURATION SPÉCIFIQUE TÉLÉMÉDECINE
# ==========================================

# Configuration WhatsApp pour les prescriptions
ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', '')
PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')

# Configuration spécifique pour les prescriptions médicales
TELEMEDICINE_S3_SETTINGS = {
    'bucket_name': AWS_STORAGE_BUCKET_NAME,  # Utilise votre bucket existant
    'region': AWS_S3_REGION_NAME,  # Utilise votre région existante
    'folder_prefix': 'prescriptions/',  # Dossier dédié aux prescriptions
    'access_key': AWS_ACCESS_KEY_ID,
    'secret_key': AWS_SECRET_ACCESS_KEY,
    'custom_domain': AWS_S3_CUSTOM_DOMAIN,
    'object_parameters': {
        'CacheControl': 'max-age=3600',  # Cache plus court pour les prescriptions
        'ContentDisposition': 'attachment',  # Force le téléchargement
        'ContentType': 'application/pdf',  # Type MIME pour les PDF
        'ServerSideEncryption': 'AES256',  # Chiffrement pour les données médicales
    }
}

# Répertoire pour les médias (QR codes, etc.)
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Assurer que le répertoire media existe
os.makedirs(MEDIA_ROOT, exist_ok=True)

# Configuration de sécurité pour les prescriptions
PRESCRIPTION_ENCRYPTION_KEY = os.environ.get('PRESCRIPTION_ENCRYPTION_KEY', 'default-key-change-in-production')

# ==========================================
# CONFIGURATION UNIFIÉE RECOMMANDÉE
# ==========================================

# Si vous voulez séparer complètement les prescriptions, 
# vous pouvez créer un bucket dédié (optionnel)
TELEMEDICINE_SEPARATE_BUCKET = os.environ.get('TELEMEDICINE_SEPARATE_BUCKET', 'false').lower() == 'true'

if TELEMEDICINE_SEPARATE_BUCKET:
    # Configuration pour un bucket séparé (optionnel)
    TELEMEDICINE_BUCKET_NAME = os.environ.get('TELEMEDICINE_BUCKET_NAME', 'lobiko-prescriptions')
    TELEMEDICINE_S3_SETTINGS['bucket_name'] = TELEMEDICINE_BUCKET_NAME
else:
    # Utilise votre bucket existant avec un préfixe
    TELEMEDICINE_S3_SETTINGS['bucket_name'] = AWS_STORAGE_BUCKET_NAME

