from django.urls import path
from . import views

app_name = 'medecins'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('session/<int:session_id>/send/', views.send_message, name='send_message'),
    path('session/<int:session_id>/close/', views.close_session, name='close_session'),
]
