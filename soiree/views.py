import pandas as pd
import base64
import os
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
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .models import (
    Service, TypeBoisson, Profile, Gestionnaire, Participant, 
    ConsommationParticipant, Trophee, Pari, DemandeAdhesion,
    ClassementQuotidien, ClassementEtablissement
)
from .forms import (
    ServiceForm, TypeBoissonForm, ProfileForm, GestionnaireForm,
    ParticipantForm, PariForm, DemandeAdhesionForm, TypeBoissonForm,
    ConsommationParticipantForm, ProfileForm, GestionnaireForm, ServiceForm
)
from .utils import is_pseudo_unique, generate_random_password, ensure_media_directories, copy_file_to_service, save_recorded_video
from .forms import CustomUserRegistrationForm
import json


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
        print("🔍 POST reçu pour la demande d'adhésion")
        form = DemandeAdhesionForm(request.POST, request.FILES)
        print(f"🔍 Formulaire valide: {form.is_valid()}")
        
        if form.is_valid():
            # Vérifier l'unicité du pseudo
            pseudo = form.cleaned_data.get('pseudo')
            print(f"🔍 Pseudo saisi: {pseudo}")
            
            if not is_pseudo_unique(pseudo):
                print(f"❌ Pseudo '{pseudo}' déjà utilisé")
                messages.error(request, f'Le pseudo "{pseudo}" est déjà utilisé. Veuillez choisir un autre pseudo.')
                # Préparer le contexte pour afficher le formulaire avec l'erreur
                context = {
                    'form': form,
                    'total_etablissements': Service.objects.filter(actif=True).count(),
                    'total_participants': Participant.objects.filter(actif=True).count(),
                    'top_maquis': [],
                    'top_boites': [],
                    'trophees_recents': Trophee.objects.all().order_by('-date_attribution')[:3],
                    'etablissements': [],
                    'consommations_aujourd_hui': 0,
                }
                return render(request, 'index.html', context)
            
            print(f"✅ Pseudo '{pseudo}' unique, création de la demande...")
            
            demande = form.save(commit=False)
            
            # Traitement des vidéos (uploadées ou enregistrées directement)
            print("🔍 Traitement des vidéos...")
            
            # 1. Vérifier s'il y a une vidéo uploadée via le formulaire
            if 'video_etablissement' in request.FILES:
                print("📹 Vidéo uploadée détectée")
                demande.video_etablissement = request.FILES['video_etablissement']
                print(f"✅ Vidéo uploadée assignée: {demande.video_etablissement.name}")
            
            # 2. Vérifier s'il y a une vidéo enregistrée directement
            recorded_video_data = form.cleaned_data.get('recorded_video_data')
            if recorded_video_data and recorded_video_data.startswith('data:video/'):
                print("🎥 Vidéo enregistrée directement détectée")
                try:
                    # Utiliser l'utilitaire pour sauvegarder la vidéo
                    video_file = save_recorded_video(recorded_video_data, "video_enregistree")
                    if video_file:
                        demande.video_etablissement = video_file
                        print(f"✅ Vidéo enregistrée sauvegardée: {video_file.name}")
                    else:
                        print("❌ Erreur lors de la sauvegarde de la vidéo enregistrée")
                except Exception as e:
                    print(f"❌ Erreur lors du traitement de la vidéo enregistrée: {e}")
                    # En cas d'erreur, on continue sans la vidéo
            
            # 3. Vérifier s'il y a une miniature
            if 'miniature_video' in request.FILES:
                print("🖼️ Miniature uploadée détectée")
                demande.miniature_video = request.FILES['miniature_video']
                print(f"✅ Miniature assignée: {demande.miniature_video.name}")
            
            print(f"🔍 État final - Vidéo: {demande.video_etablissement}, Miniature: {demande.miniature_video}")
            
            # S'assurer que les dossiers media existent
            print("📁 Création des dossiers media...")
            ensure_media_directories()
            
            demande.save()
            print(f"✅ Demande sauvegardée avec l'ID: {demande.id}")
            
            # Ajouter le message de succès
            success_message = f'🎉 Votre demande d\'adhésion pour "{demande.nom_etablissement}" a été envoyée avec succès ! Nous vous contacterons bientôt par email à {demande.email_gestionnaire}.'
            print(f"📝 Ajout du message de succès: {success_message}")
            messages.success(request, success_message)
            
            # Vérifier que le message a été ajouté
            print(f"🔍 Messages dans la requête après ajout: {list(messages.get_messages(request))}")
            
            # Au lieu de rediriger, on recharge le formulaire vide et on affiche le message
            form = DemandeAdhesionForm()
            print("🔄 Formulaire réinitialisé")
            # Le message sera affiché par le template
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


def inscription_participant(request):
    """Inscription publique des participants depuis la page d'accueil"""
    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            # Vérifier l'unicité du pseudo
            if not is_pseudo_unique(form.cleaned_data['pseudo']):
                messages.error(request, 'Ce pseudo est déjà utilisé. Veuillez en choisir un autre.')
                context = {'form': form}
                return render(request, 'inscription_participant.html', context)
            
            try:
                with transaction.atomic():
                    # Créer le compte utilisateur
                    email = form.cleaned_data['email']
                    pseudo = form.cleaned_data['pseudo']
                    
                    # Vérifier si l'email est déjà utilisé
                    if User.objects.filter(email=email).exists():
                        messages.error(request, 'Cette adresse email est déjà utilisée.')
                        context = {'form': form}
                        return render(request, 'inscription_participant.html', context)
                    
                    # Créer l'utilisateur avec un mot de passe temporaire
                    password = generate_random_password()
                    user = User.objects.create_user(
                        username=pseudo,
                        email=email,
                        password=password,
                        first_name=form.cleaned_data['prenom'],
                        last_name=form.cleaned_data['nom']
                    )
                    
                    # Créer le profil utilisateur
                    profile = Profile.objects.create(
                        user=user,
                        pseudo=pseudo,
                        nom=form.cleaned_data['nom'],
                        prenom=form.cleaned_data['prenom'],
                        tel=None  # Le téléphone sera rempli plus tard
                    )
                    
                    # Créer le participant
                    participant = form.save(commit=False)
                    participant.user = user
                    
                    # Traiter la photo si elle existe
                    if form.cleaned_data.get('photo'):
                        try:
                            # Importer la fonction de traitement des photos
                            from .utils import process_participant_photo, ensure_photo_directories
                            
                            # S'assurer que les dossiers photos existent
                            ensure_photo_directories()
                            
                            # Traiter et redimensionner la photo
                            processed_photo = process_participant_photo(form.cleaned_data['photo'])
                            if processed_photo:
                                participant.photo = processed_photo
                                print(f"✅ Photo du participant traitée et redimensionnée: {processed_photo.name}")
                            else:
                                print("⚠️ Échec du traitement de la photo, utilisation de l'original")
                        except Exception as e:
                            print(f"❌ Erreur lors du traitement de la photo: {e}")
                            # En cas d'erreur, utiliser la photo originale
                            participant.photo = form.cleaned_data['photo']
                    
                    participant.save()
                    
                    # Connecter automatiquement l'utilisateur
                    login(request, user)
                    
                    # Envoyer un email de bienvenue avec le mot de passe temporaire
                    try:
                        from django.core.mail import send_mail
                        from django.conf import settings
                        
                        subject = 'Soirée Clash - Bienvenue !'
                        message = f"""
                        Bonjour {form.cleaned_data['prenom']} {form.cleaned_data['nom']},

                        Bienvenue sur Soirée Clash ! Votre inscription a été effectuée avec succès.

                        Vos identifiants de connexion :
                        - Nom d'utilisateur : {pseudo}
                        - Mot de passe temporaire : {password}
                        - Établissement : {form.cleaned_data['service'].nom}

                        Pour votre sécurité, nous vous recommandons de changer votre mot de passe après votre première connexion.

                        Cordialement,
                        L'équipe Soirée Clash
                        """
                        
                        send_mail(
                            subject,
                            message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[email],
                            fail_silently=False,
                        )
                        
                    except Exception as e:
                        # Si l'email échoue, on continue mais on affiche un avertissement
                        messages.warning(request, 'Inscription réussie, mais l\'email de bienvenue n\'a pas pu être envoyé.')
                    
                    messages.success(request, f'🎉 Bienvenue {pseudo} ! Votre inscription a été effectuée avec succès.')
                    return redirect('app:dashboard')
                    
            except Exception as e:
                messages.error(request, f'Erreur lors de l\'inscription : {str(e)}')
                context = {'form': form}
                return render(request, 'inscription_participant.html', context)
    else:
        form = ParticipantForm()
    
    # Débogage : vérifier les établissements disponibles
    services_disponibles = Service.objects.filter(actif=True, types_boissons_enregistres=True)
    print(f"🔍 Établissements disponibles pour inscription: {services_disponibles.count()}")
    for service in services_disponibles:
        print(f"  - {service.nom} ({service.type}) - Actif: {service.actif} - Types boissons: {service.types_boissons_enregistres}")
    
    # Récupérer tous les types de boissons par établissement pour l'affichage
    boissons_par_etablissement = {}
    for service in services_disponibles:
        types_boissons = TypeBoisson.objects.filter(service=service, actif=True).order_by('categorie')
        
        # Différencier la logique selon le type d'établissement
        if service.type == 'boite':
            # Pour les boîtes de nuit : système d'enchères (pas de prix fixe)
            boissons_par_etablissement[service.id] = {
                'nom': service.nom,
                'type': service.get_type_display(),
                'type_etablissement': 'boite',
                'boissons': list(types_boissons.values('categorie')),
                'systeme': 'enchères'
            }
        else:
            # Pour les maquis : système de prix fixes
            boissons_par_etablissement[service.id] = {
                'nom': service.nom,
                'type': service.get_type_display(),
                'type_etablissement': 'maquis',
                'boissons': list(types_boissons.values('categorie', 'prix_vente')),
                'systeme': 'prix_fixes'
            }
    
    # Débogage : afficher les données des boissons
    print(f"🔍 Données des boissons préparées: {boissons_par_etablissement}")
    
    context = {
        'form': form,
        'boissons_par_etablissement': boissons_par_etablissement
    }
    return render(request, 'inscription_participant.html', context)


def register(request):
    """Inscription des utilisateurs généraux (pour paris, etc.)"""
    print(f"DEBUG: Méthode de requête: {request.method}")
    
    if request.method == 'POST':
        print("DEBUG: Traitement d'une requête POST")
        form = CustomUserRegistrationForm(request.POST)
        print(f"DEBUG: Formulaire valide: {form.is_valid()}")
        
        if form.is_valid():
            print("DEBUG: Formulaire valide, création de l'utilisateur...")
            try:
                with transaction.atomic():
                    # Créer l'utilisateur et le profil
                    user = form.save()
                    print(f"DEBUG: Utilisateur créé: {user.username}")
                    
                    # Connecter automatiquement l'utilisateur
                    login(request, user)
                    print("DEBUG: Utilisateur connecté automatiquement")
                    
                    # Envoyer un email de bienvenue
                    try:
                        from django.core.mail import send_mail
                        from django.conf import settings
                        
                        subject = 'Soirée Clash - Bienvenue !'
                        message = f"""
                        Bonjour {user.first_name} {user.last_name},

                        Bienvenue sur Soirée Clash ! Votre compte a été créé avec succès.

                        Vos identifiants de connexion :
                        - Nom d'utilisateur : {user.username}
                        - Email : {user.email}

                        Vous pouvez maintenant :
                        - Placer des paris sur les participants
                        - Suivre les classements
                        - Participer à la compétition si vous le souhaitez

                        Cordialement,
                        L'équipe Soirée Clash
                        """
                        
                        send_mail(
                            subject=subject,
                            message=message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[user.email],
                            fail_silently=False,
                        )
                        print("DEBUG: Email de bienvenue envoyé")
                        
                    except Exception as e:
                        print(f"DEBUG: Erreur envoi email: {e}")
                        # Si l'email échoue, on continue mais on affiche un avertissement
                        messages.warning(request, 'Inscription réussie, mais l\'email de bienvenue n\'a pas pu être envoyé.')
                    
                    messages.success(request, f'🎉 Bienvenue {user.username} ! Votre compte a été créé avec succès.')
                    print("DEBUG: Message de succès ajouté, redirection vers dashboard")
                    return redirect('app:dashboard')
                    
            except Exception as e:
                print(f"DEBUG: Erreur lors de la création: {e}")
                messages.error(request, f'Erreur lors de l\'inscription : {str(e)}')
                context = {'form': form}
                return render(request, 'register.html', context)
        else:
            print(f"DEBUG: Erreurs de formulaire: {form.errors}")
            # Afficher les erreurs de validation
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Erreur dans {field}: {error}')
    else:
        print("DEBUG: Affichage du formulaire GET")
        form = CustomUserRegistrationForm()
    
    context = {'form': form}
    print(f"DEBUG: Contexte final: {context}")
    return render(request, 'register.html', context)


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
    # Récupérer toutes les demandes avec leur statut
    demandes = DemandeAdhesion.objects.all().order_by('-date_demande')
    
    # Calculer les vraies statistiques
    total_demandes = demandes.count()
    demandes_en_attente = demandes.filter(statut='en_attente').count()
    demandes_approuvees = demandes.filter(statut='approuvee').count()
    demandes_rejetees = demandes.filter(statut='rejetee').count()
    
    # Statistiques par type d'établissement
    demandes_maquis = demandes.filter(type_etablissement='maquis').count()
    demandes_boites = demandes.filter(type_etablissement='boite').count()
    
    # Statistiques par ville
    demandes_ouaga = demandes.filter(ville='Ouagadougou').count()
    demandes_autres_villes = total_demandes - demandes_ouaga
    
    if request.method == 'POST':
        demande_id = request.POST.get('demande_id')
        action = request.POST.get('action')
        
        if demande_id and action:
            demande = get_object_or_404(DemandeAdhesion, id=demande_id)
            
            if action == 'approuver':
                try:
                    # Créer l'établissement
                    service = Service.objects.create(
                        nom=demande.nom_etablissement,
                        type=demande.type_etablissement,
                        localisation=demande.quartier,
                        adresse=f"{demande.quartier}, {demande.ville}",
                        proprietaire=request.user,  # L'admin devient propriétaire temporaire
                        actif=True
                    )
                    
                    # Créer les dossiers de destination s'ils n'existent pas
                    ensure_media_directories()
                    
                    # Copier la vidéo si elle existe
                    if demande.video_etablissement and demande.video_etablissement.name:
                        try:
                            # Utiliser l'utilitaire pour copier le fichier
                            chemin_destination_video = copy_file_to_service(
                                demande.video_etablissement, 
                                'videos/etablissements', 
                                'video'
                            )
                            
                            if chemin_destination_video:
                                # Mettre à jour le chemin dans le service
                                service.video_etablissement = chemin_destination_video
                                print(f"Vidéo copiée: {chemin_destination_video}")
                            else:
                                print("Erreur lors de la copie de la vidéo")
                        except Exception as e:
                            print(f"Erreur lors de la copie de la vidéo: {e}")
                    
                    # Copier la miniature si elle existe
                    if demande.miniature_video and demande.miniature_video.name:
                        try:
                            # Utiliser l'utilitaire pour copier le fichier
                            chemin_destination_miniature = copy_file_to_service(
                                demande.miniature_video, 
                                'miniatures/videos', 
                                'miniature'
                            )
                            
                            if chemin_destination_miniature:
                                # Mettre à jour le chemin dans le service
                                service.miniature_video = chemin_destination_miniature
                                print(f"Miniature copiée: {chemin_destination_miniature}")
                            else:
                                print("Erreur lors de la copie de la miniature")
                        except Exception as e:
                            print(f"Erreur lors de la copie de la miniature: {e}")
                    
                    # Sauvegarder le service avec les vidéos
                    service.save()
                    
                    # Créer le compte utilisateur pour le gestionnaire
                    username = demande.pseudo  # Utiliser directement le pseudo saisi
                    
                    # Vérifier si le pseudo est déjà utilisé dans auth_user
                    if User.objects.filter(username=username).exists():
                        # Générer un nom d'utilisateur unique en ajoutant un suffixe
                        counter = 1
                        while User.objects.filter(username=f"{username}_{counter}").exists():
                            counter += 1
                        username = f"{username}_{counter}"
                        print(f"⚠️ Pseudo '{demande.pseudo}' déjà utilisé dans auth_user, nouveau nom d'utilisateur: {username}")
                    
                    password = generate_random_password()
                    
                    user = User.objects.create_user(
                        username=username,
                        email=demande.email_gestionnaire,
                        password=password,
                        first_name=demande.prenom_gestionnaire,
                        last_name=demande.nom_gestionnaire
                    )
                    
                    # Créer le profil gestionnaire avec le pseudo saisi par l'utilisateur
                    gestionnaire = Gestionnaire.objects.create(
                        user=user,
                        service=service,
                        tel=demande.telephone_gestionnaire,
                        pseudo=demande.pseudo,
                        nom=demande.nom_gestionnaire,
                        prenom=demande.prenom_gestionnaire,
                        fonction='gerant'
                    )
                    
                    # Envoyer l'email de réinitialisation de mot de passe
                    try:
                        from django.contrib.auth.tokens import default_token_generator
                        from django.utils.http import urlsafe_base64_encode
                        from django.utils.encoding import force_bytes
                        
                        token = default_token_generator.make_token(user)
                        uid = urlsafe_base64_encode(force_bytes(user.pk))
                        
                        reset_url = request.build_absolute_uri(
                            f'/password-reset/{uid}/{token}/'
                        )
                        
                        send_mail(
                            'Création de votre compte gestionnaire - SoireeClash',
                            f'''Bonjour {demande.prenom_gestionnaire} {demande.nom_gestionnaire},

Votre demande d'adhésion pour l'établissement "{demande.nom_etablissement}" a été approuvée !

Vos identifiants de connexion :
- Nom d'utilisateur : {username}
- Mot de passe temporaire : {password}

Pour des raisons de sécurité, nous vous recommandons de changer votre mot de passe dès votre première connexion.

Vous pouvez vous connecter ici : {request.build_absolute_uri('/login/')}

Cordialement,
L'équipe SoireeClash''',
                            settings.DEFAULT_FROM_EMAIL,
                            [demande.email_gestionnaire],
                            fail_silently=False,
                        )
                        
                        messages.success(request, f'Établissement "{demande.nom_etablissement}" approuvé et compte gestionnaire créé avec le pseudo "{demande.pseudo}". Email envoyé à {demande.email_gestionnaire}')
                        
                    except Exception as e:
                        messages.warning(request, f'Établissement approuvé mais erreur lors de l\'envoi de l\'email: {e}')
                    
                    # Supprimer la demande
                    demande.delete()
                    
                except Exception as e:
                    messages.error(request, f'Erreur lors de l\'approbation: {e}')
                    print(f"Erreur détaillée: {e}")
            
            elif action == 'rejeter':
                demande.delete()
                messages.success(request, 'Demande rejetée et supprimée.')
    
    context = {
        'demandes': demandes,
        'total_demandes': total_demandes,
        'demandes_en_attente': demandes_en_attente,
        'demandes_approuvees': demandes_approuvees,
        'demandes_rejetees': demandes_rejetees,
        'demandes_maquis': demandes_maquis,
        'demandes_boites': demandes_boites,
        'demandes_ouaga': demandes_ouaga,
        'demandes_autres_villes': demandes_autres_villes,
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


def test_boissons(request):
    """Vue de test pour vérifier les données des boissons"""
    # Récupérer tous les établissements avec leurs boissons
    services = Service.objects.filter(actif=True, types_boissons_enregistres=True)
    
    boissons_par_etablissement = {}
    for service in services:
        types_boissons = TypeBoisson.objects.filter(service=service, actif=True).order_by('categorie')
        
        if service.type == 'boite':
            boissons_par_etablissement[service.id] = {
                'nom': service.nom,
                'type': service.get_type_display(),
                'type_etablissement': 'boite',
                'boissons': list(types_boissons.values('categorie')),
                'systeme': 'enchères'
            }
        else:
            boissons_par_etablissement[service.id] = {
                'nom': service.nom,
                'type': service.get_type_display(),
                'type_etablissement': 'maquis',
                'boissons': list(types_boissons.values('categorie', 'prix_vente')),
                'systeme': 'prix_fixes'
            }
    
    context = {
        'services': services,
        'boissons_par_etablissement': boissons_par_etablissement,
        'json_data': json.dumps(boissons_par_etablissement, indent=2)
    }
    
    return render(request, 'test_boissons.html', context)


def test_gain_participant(request):
    """Vue de test pour simuler un gain de participant et afficher une vidéo d'établissement"""
    
    # Simuler un gain de participant
    gain_simule = {
        'participant': {
            'nom': 'Test Participant',
            'pseudo': 'TestUser123',
            'montant_gagne': 15000,
            'etablissement': 'Club Test',
            'date_gain': timezone.now().strftime('%d/%m/%Y à %H:%M'),
            'type_trophee': 'Trophée du Jour'
        },
        'etablissement': {
            'nom': 'Club Test',
            'type': 'boite',
            'localisation': 'Zone 4, Ouagadougou',
            'description': 'Un établissement de test pour démontrer les fonctionnalités',
            'video_url': '/media/videos/etablissements/video_3e96e0cc_video_enregistree_d0d0582a.webm'
        },
        'statistiques': {
            'total_participants': 45,
            'total_etablissements': 12,
            'gain_moyen': 8500,
            'gain_max': 25000
        }
    }
    
    # Récupérer une vraie vidéo d'établissement si elle existe
    try:
        service_avec_video = Service.objects.filter(
            video_etablissement__isnull=False,
            video_etablissement__gt=''
        ).first()
        
        if service_avec_video and service_avec_video.video_etablissement:
            gain_simule['etablissement']['video_url'] = service_avec_video.video_etablissement.url
            gain_simule['etablissement']['nom'] = service_avec_video.nom
            gain_simule['etablissement']['type'] = service_avec_video.type
            gain_simule['etablissement']['localisation'] = service_avec_video.localisation
    except Exception as e:
        print(f"Erreur lors de la récupération de la vidéo: {e}")
    
    context = {
        'gain_simule': gain_simule,
        'titre_page': 'Test Gain Participant - Soirée Clash'
    }
    
    return render(request, 'test_gain_participant.html', context)