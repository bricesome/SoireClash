from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    Service, TypeBoisson, Profile, Gestionnaire, Participant, 
    ConsommationParticipant, Trophee, Pari, DemandeAdhesion
)


class CustomUserRegistrationForm(UserCreationForm):
    """Formulaire d'inscription personnalisé avec email"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre adresse email'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre prénom'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnaliser les widgets pour tous les champs
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nom d\'utilisateur unique'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe'
        })
    
    def clean_email(self):
        """Vérifier que l'email est unique"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Cette adresse email est déjà utilisée.')
        return email
    
    def save(self, commit=True):
        """Sauvegarder l'utilisateur et créer un profil"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Créer un profil utilisateur basique
            Profile.objects.create(
                user=user,
                pseudo=user.username,
                nom=user.last_name,
                prenom=user.first_name,
                tel=None  # Le téléphone sera rempli plus tard
            )
        
        return user


class DemandeAdhesionForm(forms.ModelForm):
    """Formulaire de demande d'adhésion depuis la page d'accueil"""
    # Champ caché pour la vidéo enregistrée directement
    recorded_video_data = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="Données de la vidéo enregistrée directement"
    )
    
    class Meta:
        model = DemandeAdhesion
        fields = [
            'pseudo', 'nom_etablissement', 'type_etablissement', 
            'quartier', 'ville', 'nom_gestionnaire', 'prenom_gestionnaire',
            'telephone_gestionnaire', 'email_gestionnaire', 'video_etablissement',
            'miniature_video'
        ]
        widgets = {
            'pseudo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre pseudo unique'
            }),
            'nom_etablissement': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de votre établissement'
            }),
            'type_etablissement': forms.Select(attrs={
                'class': 'form-control'
            }),
            'quartier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quartier de votre établissement'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ville (Ouagadougou par défaut)'
            }),
            'nom_gestionnaire': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du gestionnaire'
            }),
            'prenom_gestionnaire': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom du gestionnaire'
            }),
            'telephone_gestionnaire': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Téléphone du gestionnaire'
            }),
            'email_gestionnaire': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email du gestionnaire'
            }),
            'video_etablissement': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*',
                'id': 'video-upload'
            }),
            'miniature_video': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'miniature-upload'
            })
        }


class ParticipantForm(forms.ModelForm):
    """Formulaire d'inscription des participants"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre adresse email'
        })
    )
    
    class Meta:
        model = Participant
        fields = ['pseudo', 'nom', 'prenom', 'service', 'photo']
        widgets = {
            'pseudo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre pseudo unique'
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre nom'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre prénom'
            }),
            'service': forms.Select(attrs={
                'class': 'form-control',
                'id': 'service-select'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'photo-upload',
                'placeholder': 'Votre photo (optionnel)'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pour l'inscription des participants, permettre la sélection seulement des établissements
        # qui ont des types de boissons enregistrés et qui sont actifs
        self.fields['service'].queryset = Service.objects.filter(
            actif=True,
            types_boissons_enregistres=True
        )


class PariForm(forms.ModelForm):
    """Formulaire de pari"""
    class Meta:
        model = Pari
        fields = ['montant', 'participant', 'evenement', 'date_evenement']
        widgets = {
            'montant': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Montant du pari en FCFA',
                'min': '100',
                'step': '100'
            }),
            'participant': forms.Select(attrs={
                'class': 'form-control'
            }),
            'evenement': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date_evenement': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les participants actifs des établissements visibles
        self.fields['participant'].queryset = Participant.objects.filter(
            service__types_boissons_enregistres=True,
            service__actif=True,
            actif=True
        ).select_related('service')

    def clean_date_evenement(self):
        """Vérifier que la date d'événement n'est pas dans le passé"""
        date_evenement = self.cleaned_data['date_evenement']
        from django.utils import timezone
        if date_evenement < timezone.now().date():
            raise forms.ValidationError("La date d'événement ne peut pas être dans le passé.")
        return date_evenement


class TypeBoissonForm(forms.ModelForm):
    """Formulaire pour enregistrer les types de boissons et leurs prix"""
    class Meta:
        model = TypeBoisson
        fields = ['categorie', 'prix_vente']
        widgets = {
            'categorie': forms.Select(attrs={
                'class': 'form-control'
            }),
            'prix_vente': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prix de vente en FCFA',
                'min': '0',
                'step': '50'
            })
        }


class ConsommationParticipantForm(forms.ModelForm):
    """Formulaire pour enregistrer la consommation d'un participant"""
    class Meta:
        model = ConsommationParticipant
        fields = ['participant', 'type_boisson', 'quantite', 'prix_unitaire']
        widgets = {
            'participant': forms.Select(attrs={
                'class': 'form-control'
            }),
            'type_boisson': forms.Select(attrs={
                'class': 'form-control'
            }),
            'quantite': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Quantité consommée'
            }),
            'prix_unitaire': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '50',
                'placeholder': 'Prix unitaire en FCFA'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and hasattr(user, 'gestionnaire'):
            # Filtrer les participants de l'établissement du gestionnaire
            self.fields['participant'].queryset = Participant.objects.filter(
                service=user.gestionnaire.service,
                actif=True
            )
            # Filtrer les types de boissons de l'établissement
            self.fields['type_boisson'].queryset = TypeBoisson.objects.filter(
                service=user.gestionnaire.service,
                actif=True
            )


class ProfileForm(forms.ModelForm):
    """Formulaire de profil utilisateur"""
    class Meta:
        model = Profile
        fields = ['pseudo', 'nom', 'prenom', 'tel', 'avatar']
        widgets = {
            'pseudo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre pseudo unique'
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre nom'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre prénom'
            }),
            'tel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre numéro de téléphone'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }


class GestionnaireForm(forms.ModelForm):
    """Formulaire de gestionnaire"""
    class Meta:
        model = Gestionnaire
        fields = ['pseudo', 'nom', 'prenom', 'tel', 'fonction', 'avatar']
        widgets = {
            'pseudo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Pseudo du gestionnaire'
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du gestionnaire'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom du gestionnaire'
            }),
            'tel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Téléphone du gestionnaire'
            }),
            'fonction': forms.Select(attrs={
                'class': 'form-control'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }


class ServiceForm(forms.ModelForm):
    """Formulaire de service/établissement"""
    class Meta:
        model = Service
        fields = ['nom', 'type', 'localisation', 'adresse', 'telephone', 'video_etablissement', 'miniature_video']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de l\'établissement'
            }),
            'type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'localisation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Localisation'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse complète'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro de téléphone'
            }),
            'video_etablissement': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*'
            }),
            'miniature_video': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }


# Suppression des anciens formulaires qui ne sont plus nécessaires
# class BilanForm, etc.
