import pandas as pd
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.template.loader import get_template
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
import uuid

from .models import (
    Service, ConsommationParticipant, Participant, Trophee, Pari, 
    Gestionnaire, TypeBoisson, DemandeAdhesion, Profile, 
    ClassementQuotidien, ClassementEtablissement
)
from .forms import (
    ParticipantForm, PariForm, DemandeAdhesionForm, TypeBoissonForm,
    ConsommationParticipantForm, ProfileForm, GestionnaireForm, ServiceForm
)


def is_admin(user):
    """Vérifier si l'utilisateur est un administrateur"""
    return user.is_superuser


def logout_view(request):
    """Vue de déconnexion personnalisée"""
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès !')
    return redirect('app:index')


def index(request):
    """Page d'accueil avec statistiques générales et demande d'adhésion"""
    # Permettre à tous les utilisateurs d'accéder à la page d'accueil
    # Plus de redirection automatique forcée
    
    # Formulaire de demande d'adhésion
    if request.method == 'POST':
        form = DemandeAdhesionForm(request.POST)
        if form.is_valid():
            demande = form.save()
            messages.success(request, 'Votre demande d\'adhésion a été envoyée avec succès ! Nous vous contacterons bientôt.')
            return redirect('app:index')
    else:
        form = DemandeAdhesionForm()
    
    # Statistiques publiques
    total_etablissements = Service.objects.filter(actif=True).count()
    total_participants = Participant.objects.filter(actif=True).count()
    
    # Si l'utilisateur est connecté, afficher des informations personnalisées
    if request.user.is_authenticated:
        # Récupérer les établissements de l'utilisateur
        if hasattr(request.user, 'gestionnaire'):
            etablissements = [request.user.gestionnaire.service]
        elif hasattr(request.user, 'profile'):
            etablissements = Service.objects.filter(proprietaire=request.user)
        else:
            etablissements = []
        
        # Statistiques personnelles
        aujourd_hui = timezone.now().date()
        consommations_aujourd_hui = ConsommationParticipant.objects.filter(
            service__in=etablissements,
            date_consommation__date=aujourd_hui
        ).aggregate(total=Sum('montant_total'))['total'] or 0
    else:
        etablissements = []
        consommations_aujourd_hui = 0
    
    # Classements des établissements par type (entre 17h30 de la veille et 11h00 d'aujourd'hui)
    maintenant = timezone.now()
    hier_17h30 = (maintenant - timedelta(days=1)).replace(hour=17, minute=30, second=0, microsecond=0)
    aujourd_hui_11h = maintenant.replace(hour=11, minute=0, second=0, microsecond=0)
    
    if maintenant.hour < 11:
        debut = hier_17h30
        fin = aujourd_hui_11h
    else:
        debut = maintenant.replace(hour=17, minute=30, second=0, microsecond=0)
        fin = (maintenant + timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0)
    
    # Top 3 maquis
    top_maquis = Service.objects.filter(
        type='maquis', 
        actif=True,
        types_boissons_enregistres=True
    ).annotate(
        total_ventes=Sum('consommationparticipant__montant_total')
    ).filter(
        consommationparticipant__date_consommation__range=[debut, fin]
    ).order_by('-total_ventes')[:3]
    
    # Top 3 boîtes de nuit
    top_boites = Service.objects.filter(
        type='boite', 
        actif=True,
        types_boissons_enregistres=True
    ).annotate(
        total_ventes=Sum('consommationparticipant__montant_total')
    ).filter(
        consommationparticipant__date_consommation__range=[debut, fin]
    ).order_by('-total_ventes')[:3]
    
    # Trophées récents
    trophees_recents = Trophee.objects.all().order_by('-date_attribution')[:3]
    
    context = {
        'form': form,
        'total_etablissements': total_etablissements,
        'total_participants': total_participants,
        'top_maquis': top_maquis,
        'top_boites': top_boites,
        'trophees_recents': trophees_recents,
        'etablissements': etablissements,
        'consommations_aujourd_hui': consommations_aujourd_hui,
    }
    return render(request, 'index.html', context)


def register(request):
    """Inscription des utilisateurs"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Compte créé avec succès ! Vous pouvez maintenant vous connecter.')
            return redirect('app:login')
    else:
        form = UserCreationForm()
    
    return render(request, 'register.html', {'form': form})


@login_required
def dashboard(request):
    """Dashboard principal avec statistiques personnalisées"""
    user = request.user
    
    # Récupérer les établissements de l'utilisateur
    if hasattr(user, 'gestionnaire'):
        etablissements = [user.gestionnaire.service]
        # Vérifier si les types de boissons sont enregistrés
        if not user.gestionnaire.service.types_boissons_enregistres:
            messages.warning(request, 'Votre établissement ne sera visible aux participants que lorsque vous aurez enregistré vos types de boissons et leurs prix.')
    elif hasattr(user, 'profile'):
        etablissements = Service.objects.filter(proprietaire=user)
    else:
        etablissements = []
    
    # Statistiques des consommations
    aujourd_hui = timezone.now().date()
    debut_semaine = aujourd_hui - timedelta(days=aujourd_hui.weekday())
    debut_mois = aujourd_hui.replace(day=1)
    
    consommations_aujourd_hui = ConsommationParticipant.objects.filter(
        service__in=etablissements,
        date_consommation__date=aujourd_hui
    ).aggregate(total=Sum('montant_total'))['total'] or 0
    
    consommations_semaine = ConsommationParticipant.objects.filter(
        service__in=etablissements,
        date_consommation__date__gte=debut_semaine
    ).aggregate(total=Sum('montant_total'))['total'] or 0
    
    consommations_mois = ConsommationParticipant.objects.filter(
        service__in=etablissements,
        date_consommation__date__gte=debut_mois
    ).aggregate(total=Sum('montant_total'))['total'] or 0
    
    # Top participants
    top_participants = Participant.objects.filter(
        service__in=etablissements
    ).annotate(
        total_depenses=Sum('consommationparticipant__montant_total')
    ).order_by('-total_depenses')[:5]
    
    context = {
        'etablissements': etablissements,
        'consommations_aujourd_hui': consommations_aujourd_hui,
        'consommations_semaine': consommations_semaine,
        'consommations_mois': consommations_mois,
        'top_participants': top_participants,
    }
    return render(request, 'dashboard.html', context)


@login_required
def classements(request):
    """Page des classements des établissements et participants"""
    # Classement des maquis
    maquis = Service.objects.filter(
        type='maquis', 
        actif=True,
        types_boissons_enregistres=True
    ).annotate(
        total_ventes=Sum('consommationparticipant__montant_total')
    ).order_by('-total_ventes')
    
    # Classement des boîtes de nuit
    boites = Service.objects.filter(
        type='boite', 
        actif=True,
        types_boissons_enregistres=True
    ).annotate(
        total_ventes=Sum('consommationparticipant__montant_total')
    ).order_by('-total_ventes')
    
    # Top participants par type d'établissement
    top_participants_maquis = Participant.objects.filter(
        service__type='maquis',
        service__actif=True,
        service__types_boissons_enregistres=True
    ).annotate(
        total_depenses=Sum('consommationparticipant__montant_total')
    ).order_by('-total_depenses')[:10]
    
    top_participants_boites = Participant.objects.filter(
        service__type='boite',
        service__actif=True,
        service__types_boissons_enregistres=True
    ).annotate(
        total_depenses=Sum('consommationparticipant__montant_total')
    ).order_by('-total_depenses')[:10]
    
    context = {
        'maquis': maquis,
        'boites': boites,
        'top_participants_maquis': top_participants_maquis,
        'top_participants_boites': top_participants_boites,
    }
    return render(request, 'classements.html', context)


@login_required
def trophees(request):
    """Page des trophées et récompenses"""
    # Trophées récents
    trophees_recents = Trophee.objects.all().order_by('-date_attribution')[:10]
    
    # Trophées par type
    trophees_maquis = Trophee.objects.filter(
        type_trophee__in=['sultan_maquis', 'roi_ventes_maquis']
    ).order_by('-date_attribution')[:5]
    
    trophees_boite = Trophee.objects.filter(
        type_trophee__in=['empereur_boite', 'bouquet_or']
    ).order_by('-date_attribution')[:5]
    
    context = {
        'trophees_recents': trophees_recents,
        'trophees_maquis': trophees_maquis,
        'trophees_boite': trophees_boite,
    }
    return render(request, 'trophees.html', context)


@login_required
def paris(request):
    """Page des paris"""
    if request.method == 'POST':
        form = PariForm(request.POST)
        if form.is_valid():
            pari = form.save(commit=False)
            pari.user = request.user
            pari.cote = 2.00  # Cote fixe de 2
            
            # Vérifier si on peut encore parier
            if not pari.peut_parler():
                messages.error(request, 'Il est trop tard pour parier sur cet événement du jour. Les paris sont fermés après 17h00.')
                return redirect('app:paris')
            
            pari.save()
            messages.success(request, 'Pari placé avec succès !')
            return redirect('app:paris')
    else:
        form = PariForm()
    
    # Paris de l'utilisateur
    paris_utilisateur = Pari.objects.filter(user=request.user).order_by('-date_pari')
    
    # Paris actifs (non résolus)
    paris_actifs = Pari.objects.filter(
        gagne__isnull=True
    ).order_by('-date_pari')[:20]
    
    context = {
        'form': form,
        'paris_utilisateur': paris_utilisateur,
        'paris_actifs': paris_actifs,
    }
    return render(request, 'paris.html', context)


@login_required
def etablissements(request):
    """Gestion des établissements"""
    if hasattr(request.user, 'gestionnaire'):
        etablissements = [request.user.gestionnaire.service]
    elif hasattr(request.user, 'profile'):
        etablissements = Service.objects.filter(proprietaire=request.user)
    else:
        etablissements = []
    
    context = {
        'etablissements': etablissements,
    }
    return render(request, 'etablissements.html', context)


@login_required
def participants(request):
    """Gestion des participants"""
    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save(commit=False)
            participant.user = request.user
            participant.save()
            messages.success(request, 'Participant ajouté avec succès !')
            return redirect('app:participants')
    else:
        form = ParticipantForm()
    
    # Participants de l'utilisateur
    if hasattr(request.user, 'gestionnaire'):
        participants = Participant.objects.filter(service=request.user.gestionnaire.service)
    elif hasattr(request.user, 'profile'):
        participants = Participant.objects.filter(service__proprietaire=request.user)
    else:
        participants = []
    
    context = {
        'form': form,
        'participants': participants,
    }
    return render(request, 'participants.html', context)


@login_required
def gestion_boissons(request):
    """Gestion des types de boissons et leurs prix"""
    if not hasattr(request.user, 'gestionnaire'):
        messages.error(request, 'Accès réservé aux gestionnaires.')
        return redirect('app:dashboard')
    
    if request.method == 'POST':
        form = TypeBoissonForm(request.POST)
        if form.is_valid():
            boisson = form.save(commit=False)
            boisson.service = request.user.gestionnaire.service
            boisson.save()
            
            # Marquer que les types de boissons sont enregistrés
            service = request.user.gestionnaire.service
            service.types_boissons_enregistres = True
            service.derniere_mise_a_jour_boissons = timezone.now()
            service.save()
            
            messages.success(request, 'Type de boisson ajouté avec succès !')
            return redirect('app:gestion_boissons')
    else:
        form = TypeBoissonForm()
    
    # Types de boissons existants
    types_boissons = TypeBoisson.objects.filter(
        service=request.user.gestionnaire.service
    ).order_by('categorie')
    
    context = {
        'form': form,
        'types_boissons': types_boissons,
        'service': request.user.gestionnaire.service,
    }
    return render(request, 'gestion_boissons.html', context)


@login_required
def gestion_consommations(request):
    """Gestion des consommations des participants"""
    if not hasattr(request.user, 'gestionnaire'):
        messages.error(request, 'Accès réservé aux gestionnaires.')
        return redirect('app:dashboard')
    
    if request.method == 'POST':
        form = ConsommationParticipantForm(request.POST, user=request.user)
        if form.is_valid():
            consommation = form.save(commit=False)
            consommation.service = request.user.gestionnaire.service
            consommation.saisi_par = request.user.gestionnaire
            consommation.save()
            messages.success(request, 'Consommation enregistrée avec succès !')
            return redirect('app:gestion_consommations')
    else:
        form = ConsommationParticipantForm(user=request.user)
    
    # Consommations récentes
    consommations = ConsommationParticipant.objects.filter(
        service=request.user.gestionnaire.service
    ).order_by('-date_consommation')[:50]
    
    context = {
        'form': form,
        'consommations': consommations,
        'service': request.user.gestionnaire.service,
    }
    return render(request, 'gestion_consommations.html', context)


@user_passes_test(is_admin)
def admin_demandes_adhesion(request):
    """Administration des demandes d'adhésion"""
    demandes = DemandeAdhesion.objects.all().order_by('-date_demande')
    
    if request.method == 'POST':
        demande_id = request.POST.get('demande_id')
        action = request.POST.get('action')
        
        if demande_id and action:
            demande = get_object_or_404(DemandeAdhesion, id=demande_id)
            
            if action == 'approuver':
                # Créer l'établissement
                service = Service.objects.create(
                    nom=demande.nom_etablissement,
                    type=demande.type_etablissement,
                    localisation=demande.quartier,
                    adresse=f"{demande.quartier}, {demande.ville}",
                    proprietaire=request.user,  # L'admin devient propriétaire temporaire
                    actif=True
                )
                
                # Créer le compte gestionnaire
                user = User.objects.create_user(
                    username=demande.pseudo,
                    email=demande.email_gestionnaire,
                    password=str(uuid.uuid4()),  # Mot de passe temporaire
                    first_name=demande.prenom_gestionnaire,
                    last_name=demande.nom_gestionnaire
                )
                
                gestionnaire = Gestionnaire.objects.create(
                    user=user,
                    pseudo=demande.pseudo,
                    nom=demande.nom_gestionnaire,
                    prenom=demande.prenom_gestionnaire,
                    tel=demande.telephone_gestionnaire,
                    service=service,
                    fonction='gerant'
                )
                
                # Marquer la demande comme approuvée
                demande.statut = 'approuvee'
                demande.save()
                
                # Envoyer un mail de réinitialisation
                # gestionnaire.envoyer_mail_reinitialisation()
                
                messages.success(request, f'Demande approuvée. Compte gestionnaire créé pour {demande.pseudo}.')
                
            elif action == 'rejeter':
                demande.statut = 'rejetee'
                demande.save()
                messages.success(request, 'Demande rejetée.')
    
    context = {
        'demandes': demandes,
    }
    return render(request, 'admin_demandes_adhesion.html', context)


def export_consommations_excel(request):
    """Export Excel des consommations"""
    if not request.user.is_superuser:
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('app:dashboard')
    
    consommations = ConsommationParticipant.objects.select_related(
        'service', 'type_boisson', 'participant', 'saisi_par'
    ).all()
    
    # Créer le DataFrame
    data = []
    for c in consommations:
        data.append({
            'Établissement': c.service.nom if c.service else 'N/A',
            'Participant': c.participant.pseudo if c.participant else 'N/A',
            'Type de boisson': c.type_boisson.get_categorie_display() if c.type_boisson else 'N/A',
            'Quantité': c.quantite,
            'Prix unitaire': float(c.prix_unitaire),
            'Montant total': float(c.montant_total),
            'Date consommation': c.date_consommation.strftime('%d/%m/%Y %H:%M'),
            'Saisi par': c.saisi_par.pseudo if c.saisi_par else 'N/A'
        })
    
    df = pd.DataFrame(data)
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=consommations_soiree_clash.xlsx'
    
    df.to_excel(response, index=False)
    return response


def export_classements_excel(request):
    """Export Excel des classements"""
    if not request.user.is_superuser:
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('app:dashboard')
    
    # Classements des participants
    classements_participants = ClassementQuotidien.objects.select_related(
        'participant', 'etablissement'
    ).all()
    
    # Classements des établissements
    classements_etablissements = ClassementEtablissement.objects.select_related(
        'etablissement'
    ).all()
    
    # Créer le DataFrame pour les participants
    data_participants = []
    for c in classements_participants:
        data_participants.append({
            'Date': c.date.strftime('%d/%m/%Y'),
            'Type établissement': c.get_type_etablissement_display(),
            'Participant': c.participant.pseudo if c.participant else 'N/A',
            'Établissement': c.etablissement.nom if c.etablissement else 'N/A',
            'Montant total': float(c.montant_total),
            'Position': c.position
        })
    
    # Créer le DataFrame pour les établissements
    data_etablissements = []
    for c in classements_etablissements:
        data_etablissements.append({
            'Date': c.date.strftime('%d/%m/%Y'),
            'Type établissement': c.get_type_etablissement_display(),
            'Établissement': c.etablissement.nom if c.etablissement else 'N/A',
            'Montant total': float(c.montant_total),
            'Position': c.position
        })
    
    # Créer un fichier Excel avec deux onglets
    with pd.ExcelWriter('classements_soiree_clash.xlsx', engine='openpyxl') as writer:
        pd.DataFrame(data_participants).to_excel(writer, sheet_name='Classements_Participants', index=False)
        pd.DataFrame(data_etablissements).to_excel(writer, sheet_name='Classements_Etablissements', index=False)
    
    # Lire le fichier et le renvoyer
    with open('classements_soiree_clash.xlsx', 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=classements_soiree_clash.xlsx'
    
    return response


# API endpoints pour les données dynamiques
def api_classements(request):
    """API pour les classements"""
    maquis = Service.objects.filter(
        type='maquis', 
        actif=True,
        types_boissons_enregistres=True
    ).annotate(
        total_ventes=Sum('consommationparticipant__montant_total')
    ).values('nom', 'total_ventes').order_by('-total_ventes')[:10]
    
    boites = Service.objects.filter(
        type='boite', 
        actif=True,
        types_boissons_enregistres=True
    ).annotate(
        total_ventes=Sum('consommationparticipant__montant_total')
    ).values('nom', 'total_ventes').order_by('-total_ventes')[:10]
    
    return JsonResponse({
        'maquis': list(maquis),
        'boites': list(boites),
    })


def api_consommations(request):
    """API pour les données de consommations"""
    periode = request.GET.get('periode', 'jour')
    
    aujourd_hui = timezone.now().date()
    if periode == 'jour':
        debut = aujourd_hui
        fin = aujourd_hui
    elif periode == 'semaine':
        debut = aujourd_hui - timedelta(days=7)
        fin = aujourd_hui
    elif periode == 'mois':
        debut = aujourd_hui.replace(day=1)
        fin = aujourd_hui
    else:
        debut = aujourd_hui
        fin = aujourd_hui
    
    consommations = ConsommationParticipant.objects.filter(
        date_consommation__date__range=[debut, fin]
    ).values('service__nom').annotate(
        total=Sum('montant_total')
    ).order_by('-total')
    
    return JsonResponse({
        'consommations': list(consommations),
        'periode': periode,
    })