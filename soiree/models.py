from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import uuid


class DemandeAdhesion(models.Model):
    """Demande d'adhésion depuis la page d'accueil"""
    TYPE_CHOICES = (
        ('maquis', 'Maquis'),
        ('boite', 'Boîte de Nuit'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pseudo = models.CharField(max_length=30, unique=True)
    nom_etablissement = models.CharField(max_length=100)
    type_etablissement = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quartier = models.CharField(max_length=100)
    ville = models.CharField(max_length=100, default="Ouagadougou")
    
    # Informations du gestionnaire
    nom_gestionnaire = models.CharField(max_length=50)
    prenom_gestionnaire = models.CharField(max_length=50)
    telephone_gestionnaire = models.CharField(max_length=20)
    email_gestionnaire = models.EmailField()
    
    date_demande = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=[
        ('en_attente', 'En attente'),
        ('approuvee', 'Approuvée'),
        ('rejetee', 'Rejetée')
    ], default='en_attente')
    
    def __str__(self):
        return f"{self.pseudo} - {self.nom_etablissement}"
    
    class Meta:
        verbose_name = "Demande d'adhésion"
        verbose_name_plural = "Demandes d'adhésion"


class Service(models.Model):
    TYPE_CHOICES = (
        ('maquis', 'Maquis'),
        ('boite', 'Boîte de Nuit'),
    )
    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    localisation = models.CharField(max_length=200)
    adresse = models.TextField()
    telephone = models.CharField(max_length=20, blank=True)
    proprietaire = models.ForeignKey(User, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)
    
    # Nouveaux champs
    types_boissons_enregistres = models.BooleanField(default=False, 
        help_text="Les types de boissons ont-ils été enregistrés ?")
    derniere_mise_a_jour_boissons = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nom} ({self.get_type_display()})"

    def est_visible_participants(self):
        """L'établissement est visible seulement si les types de boissons sont enregistrés"""
        return self.types_boissons_enregistres and self.actif

    def total_ventes_periode(self, debut, fin):
        """Total des ventes sur une période donnée"""
        return self.consommationparticipant_set.filter(
            date_consommation__range=[debut, fin]
        ).aggregate(
            total=models.Sum('montant_total')
        )['total'] or 0

    def total_ventes_aujourd_hui(self):
        aujourd_hui = timezone.now().date()
        return self.total_ventes_periode(aujourd_hui, aujourd_hui)

    def total_ventes_periode_classement(self):
        """Ventes entre 17h30 de la veille et 11h00 d'aujourd'hui pour le classement"""
        maintenant = timezone.now()
        hier_17h30 = (maintenant - timedelta(days=1)).replace(hour=17, minute=30, second=0, microsecond=0)
        aujourd_hui_11h = maintenant.replace(hour=11, minute=0, second=0, microsecond=0)
        
        if maintenant.hour < 11:
            # Si on est avant 11h, on prend la période d'hier 17h30 à aujourd'hui 11h
            debut = hier_17h30
            fin = aujourd_hui_11h
        else:
            # Sinon, on prend la période d'aujourd'hui 17h30 à demain 11h
            debut = maintenant.replace(hour=17, minute=30, second=0, microsecond=0)
            fin = (maintenant + timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0)
        
        return self.total_ventes_periode(debut, fin)

    class Meta:
        verbose_name = "Établissement"
        verbose_name_plural = "Établissements"


class TypeBoisson(models.Model):
    """Types de boissons avec prix de vente par établissement"""
    CATEGORIE_CHOICES = (
        ('champagne', 'Champagne'),
        ('whisky', 'Whisky'),
        ('brakina', 'BRAKINA'),
        ('sobbra', 'SOBBRA'),
        ('liqueur', 'Liqueur'),
        ('g_guiness', 'GROSSE GUINNESS'),
        ('p_guiness', 'PETIT GUINNESS'),
        ('soft', 'Boisson Non-Alcoolisée'),
        ('autre', 'Autre'),
    )
    
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES)
    prix_vente = models.DecimalField(max_digits=10, decimal_places=2)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.service.nom} - {self.get_categorie_display()} ({self.prix_vente} FCFA)"
    
    class Meta:
        unique_together = ['service', 'categorie']
        verbose_name = "Type de boisson"
        verbose_name_plural = "Types de boissons"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pseudo = models.CharField(max_length=30, blank=False, unique=True)
    nom = models.CharField(max_length=20, blank=True)
    prenom = models.CharField(max_length=50, blank=True)
    avatar = models.ImageField(upload_to="avatar", verbose_name="Photo ou avatar", blank=True, null=True)
    tel = models.CharField(max_length=20, unique=True, blank=False, verbose_name="Numéro téléphone")

    def __str__(self):
        return self.pseudo


class Gestionnaire(models.Model):
    FONCTION = (
        ('gerant', 'GERANT'),
        ('dg', 'DIRIGEANT'),
        ('animateur', 'ANIMATEUR')
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pseudo = models.CharField(max_length=30, blank=False, unique=True)
    nom = models.CharField(max_length=20, blank=True)
    prenom = models.CharField(max_length=50, blank=True)
    avatar = models.ImageField(upload_to="avatar", verbose_name="Photo ou avatar", blank=True, null=True)
    tel = models.CharField(max_length=20, unique=True, blank=False, verbose_name="Numéro téléphone")
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    fonction = models.CharField(max_length=20, choices=FONCTION)
    mot_de_passe_reinitialise = models.BooleanField(default=False)

    def __str__(self):
        return self.pseudo
    
    def envoyer_mail_reinitialisation(self):
        """Envoyer un mail de réinitialisation du mot de passe"""
        token = uuid.uuid4()
        # Ici vous pouvez implémenter la logique d'envoi d'email
        # avec un token de réinitialisation
        pass


class Participant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pseudo = models.CharField(max_length=30, unique=True)
    nom = models.CharField(max_length=50, blank=True)
    prenom = models.CharField(max_length=50, blank=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date_inscription = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.pseudo} - {self.service.nom}"

    def total_depenses_jour(self, date=None):
        """Total des dépenses d'un participant pour une journée donnée"""
        if date is None:
            date = timezone.now().date()
        
        return self.consommationparticipant_set.filter(
            date_consommation__date=date
        ).aggregate(
            total=models.Sum('montant_total')
        )['total'] or 0

    class Meta:
        verbose_name = "Participant"
        verbose_name_plural = "Participants"


class ConsommationParticipant(models.Model):
    """Consommation d'un participant dans un établissement"""
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    type_boisson = models.ForeignKey(TypeBoisson, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    montant_total = models.DecimalField(max_digits=12, decimal_places=2)
    date_consommation = models.DateTimeField(auto_now_add=True)
    date_saisie = models.DateTimeField(auto_now_add=True)
    saisi_par = models.ForeignKey(Gestionnaire, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        if not self.montant_total:
            self.montant_total = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.participant.pseudo} - {self.type_boisson.categorie} ({self.quantite}) - {self.montant_total} FCFA"

    class Meta:
        verbose_name = "Consommation participant"
        verbose_name_plural = "Consommations participants"
        ordering = ['-date_consommation']


class Trophee(models.Model):
    TYPE_TROPHEE_CHOICES = [
        ('sultan_maquis', 'Sultan du Maquis'),
        ('bouquet_or', 'Bouquet d\'Or'),
        ('roi_ventes_maquis', 'Roi des Ventes Maquis'),
        ('empereur_boite', 'Empereur de la Boîte'),
    ]
    
    type_trophee = models.CharField(max_length=20, choices=TYPE_TROPHEE_CHOICES)
    gagnant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    etablissement = models.ForeignKey(Service, on_delete=models.CASCADE)
    date_attribution = models.DateField()
    montant_total = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    photo_gagnant = models.ImageField(upload_to="trophees", blank=True, null=True)

    def __str__(self):
        return f"{self.get_type_trophee_display()} - {self.gagnant.pseudo} ({self.date_attribution})"

    class Meta:
        verbose_name = "Trophée"
        verbose_name_plural = "Trophées"
        ordering = ['-date_attribution']
        unique_together = ['type_trophee', 'date_attribution', 'etablissement']


class Pari(models.Model):
    EVENEMENT = (
        ('GAIN', 'GAIN'),
        ('PERTE', 'PERTE'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    cote = models.DecimalField(max_digits=4, decimal_places=2, default=2.00)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    evenement = models.CharField(max_length=6, choices=EVENEMENT)
    date_pari = models.DateTimeField(auto_now_add=True)
    date_evenement = models.DateField()
    gagne = models.BooleanField(null=True, blank=True, verbose_name="Pari gagné")
    montant_gains = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    resultat_disponible = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.montant} FCFA sur {self.participant.pseudo}"
    
    def peut_parler(self):
        """Vérifier si on peut encore parier (avant 17h00 le jour de l'événement)"""
        maintenant = timezone.now()
        if self.date_evenement == maintenant.date():
            return maintenant.hour < 17
        return True
    
    def calculer_gains(self):
        """Calculer les gains si le pari est gagné"""
        if self.gagne:
            self.montant_gains = self.montant * self.cote
            return self.montant_gains
        return 0

    class Meta:
        verbose_name = "Pari"
        verbose_name_plural = "Paris"
        ordering = ['-date_pari']


class ClassementQuotidien(models.Model):
    """Classement quotidien des participants par type d'établissement"""
    date = models.DateField()
    type_etablissement = models.CharField(max_length=10, choices=Service.TYPE_CHOICES)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    etablissement = models.ForeignKey(Service, on_delete=models.CASCADE)
    montant_total = models.DecimalField(max_digits=12, decimal_places=2)
    position = models.PositiveIntegerField()
    
    def __str__(self):
        return f"{self.date} - {self.participant.pseudo} ({self.position}ème)"
    
    class Meta:
        unique_together = ['date', 'type_etablissement', 'position']
        ordering = ['date', 'type_etablissement', 'position']


class ClassementEtablissement(models.Model):
    """Classement des établissements par type"""
    date = models.DateField()
    type_etablissement = models.CharField(max_length=10, choices=Service.TYPE_CHOICES)
    etablissement = models.ForeignKey(Service, on_delete=models.CASCADE)
    montant_total = models.DecimalField(max_digits=12, decimal_places=2)
    position = models.PositiveIntegerField()
    
    def __str__(self):
        return f"{self.date} - {self.etablissement.nom} ({self.position}ème)"
    
    class Meta:
        unique_together = ['date', 'type_etablissement', 'position']
        ordering = ['date', 'type_etablissement', 'position']


# Suppression des anciens modèles qui ne sont plus nécessaires
# class Produit, Bilan, etc.