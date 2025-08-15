from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "app"
urlpatterns = [
    path("", views.index, name='index'),
    path("login/", auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path("logout/", views.logout_view, name='logout'),
    path("register/", views.register, name='register'),
    path("dashboard/", views.dashboard, name='dashboard'),
    path("classements/", views.classements, name='classements'),
    path("trophees/", views.trophees, name='trophees'),
    path("paris/", views.paris, name='paris'),
    path("etablissements/", views.etablissements, name='etablissements'),
    path("participants/", views.participants, name='participants'),
    
    # Nouvelles vues pour la gestion des boissons et consommations
    path("gestion-boissons/", views.gestion_boissons, name='gestion_boissons'),
    path("gestion-consommations/", views.gestion_consommations, name='gestion_consommations'),
    
    # Vues d'administration
    path("admin-demandes-adhesion/", views.admin_demandes_adhesion, name='admin_demandes_adhesion'),
    
    # Exports Excel
    path("export/consommations/excel/", views.export_consommations_excel, name='export_consommations_excel'),
    path("export/classements/excel/", views.export_classements_excel, name='export_classements_excel'),
    
    # API endpoints
    path("api/classements/", views.api_classements, name='api_classements'),
    path("api/consommations/", views.api_consommations, name='api_consommations'),
]