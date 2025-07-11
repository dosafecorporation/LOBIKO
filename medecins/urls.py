from django.urls import path
from . import views

urlpatterns = [
    path('inscription/', views.inscription_medecin, name='inscription_medecin'),
    path('login/', views.login_medecin, name='login_medecin'),
    path('logout/', views.logout_medecin, name='logout_medecin'),
    path('dashboard/', views.dashboard_medecin, name='dashboard_medecin'),
]
