from django.urls import path
from . import views

urlpatterns = [
    path('inscription/', views.inscription_medecin, name='inscription_medecin'),
    path('login/', views.login_medecin, name='login_medecin'),
    path('logout/', views.logout_medecin, name='logout_medecin'),
    path('dashboard/', views.dashboard_medecin, name='dashboard_medecin'),
    path('session/<int:session_id>/accepter/', views.accepter_session, name='accepter_session'),
    path('discussion/<int:session_id>/', views.discussion_session, name='discussion_session'),
    path('appel/<int:session_id>/', views.initier_appel_jitsi, name='initier_appel_jitsi'),
    path('media/download/<int:session_id>/<int:media_id>/', views.proxy_download, name='proxy_download'),
    path('download/<int:session_id>/<int:media_id>/', views.download_media_file, name='download_media'),
]