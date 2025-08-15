from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Service, TypeBoisson, Profile, Gestionnaire, Participant, 
    ConsommationParticipant, Trophee, Pari, DemandeAdhesion,
    ClassementQuotidien, ClassementEtablissement
)


@admin.register(DemandeAdhesion)
class DemandeAdhesionAdmin(admin.ModelAdmin):
    list_display = ['pseudo', 'nom_etablissement', 'type_etablissement', 'quartier', 'ville', 'statut', 'date_demande']
    list_filter = ['statut', 'type_etablissement', 'ville', 'date_demande']
    search_fields = ['pseudo', 'nom_etablissement', 'nom_gestionnaire', 'prenom_gestionnaire']
    readonly_fields = ['date_demande']
    actions = ['approuver_demandes', 'rejeter_demandes']
    
    def approuver_demandes(self, request, queryset):
        for demande in queryset.filter(statut='en_attente'):
            demande.statut = 'approuvee'
            demande.save()
        self.message_user(request, f"{queryset.count()} demande(s) approuvée(s).")
    approuver_demandes.short_description = "Approuver les demandes sélectionnées"
    
    def rejeter_demandes(self, request, queryset):
        for demande in queryset.filter(statut='en_attente'):
            demande.statut = 'rejetee'
            demande.save()
        self.message_user(request, f"{queryset.count()} demande(s) rejetée(s).")
    rejeter_demandes.short_description = "Rejeter les demandes sélectionnées"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type', 'localisation', 'proprietaire', 'types_boissons_enregistres', 'actif', 'date_creation']
    list_filter = ['type', 'actif', 'types_boissons_enregistres', 'date_creation']
    search_fields = ['nom', 'localisation', 'proprietaire__username']
    readonly_fields = ['date_creation', 'derniere_mise_a_jour_boissons']
    actions = ['activer_services', 'desactiver_services']
    
    def activer_services(self, request, queryset):
        queryset.update(actif=True)
        self.message_user(request, f"{queryset.count()} service(s) activé(s).")
    activer_services.short_description = "Activer les services sélectionnés"
    
    def desactiver_services(self, request, queryset):
        queryset.update(actif=False)
        self.message_user(request, f"{queryset.count()} service(s) désactivé(s).")
    desactiver_services.short_description = "Désactiver les services sélectionnés"


@admin.register(TypeBoisson)
class TypeBoissonAdmin(admin.ModelAdmin):
    list_display = ['service', 'categorie', 'prix_vente', 'actif', 'date_creation']
    list_filter = ['categorie', 'actif', 'service__type', 'date_creation']
    search_fields = ['service__nom', 'categorie']
    readonly_fields = ['date_creation']
    list_editable = ['prix_vente', 'actif']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'pseudo', 'nom', 'prenom', 'tel']
    search_fields = ['user__username', 'pseudo', 'nom', 'prenom', 'tel']
    list_filter = ['user__is_active']


@admin.register(Gestionnaire)
class GestionnaireAdmin(admin.ModelAdmin):
    list_display = ['user', 'pseudo', 'service', 'fonction', 'tel', 'mot_de_passe_reinitialise']
    list_filter = ['fonction', 'service__type', 'mot_de_passe_reinitialise']
    search_fields = ['user__username', 'pseudo', 'nom', 'prenom', 'tel', 'service__nom']
    actions = ['reinitialiser_mots_de_passe']
    
    def reinitialiser_mots_de_passe(self, request, queryset):
        for gestionnaire in queryset:
            gestionnaire.mot_de_passe_reinitialise = False
            gestionnaire.save()
        self.message_user(request, f"{queryset.count()} gestionnaire(s) marqué(s) pour réinitialisation de mot de passe.")
    reinitialiser_mots_de_passe.short_description = "Marquer pour réinitialisation de mot de passe"


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'pseudo', 'service', 'date_inscription', 'actif']
    list_filter = ['actif', 'service__type', 'date_inscription']
    search_fields = ['user__username', 'pseudo', 'service__nom']
    readonly_fields = ['date_inscription']
    actions = ['activer_participants', 'desactiver_participants']
    
    def activer_participants(self, request, queryset):
        queryset.update(actif=True)
        self.message_user(request, f"{queryset.count()} participant(s) activé(s).")
    activer_participants.short_description = "Activer les participants sélectionnés"
    
    def desactiver_participants(self, request, queryset):
        queryset.update(actif=False)
        self.message_user(request, f"{queryset.count()} participant(s) désactivé(s).")
    desactiver_participants.short_description = "Désactiver les participants sélectionnés"


@admin.register(ConsommationParticipant)
class ConsommationParticipantAdmin(admin.ModelAdmin):
    list_display = ['participant', 'service', 'type_boisson', 'quantite', 'montant_total', 'date_consommation', 'saisi_par']
    list_filter = ['service__type', 'type_boisson__categorie', 'date_consommation', 'saisi_par']
    search_fields = ['participant__pseudo', 'service__nom', 'saisi_par__pseudo']
    readonly_fields = ['date_consommation', 'date_saisie', 'montant_total']
    date_hierarchy = 'date_consommation'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('participant', 'service', 'type_boisson', 'saisi_par')


@admin.register(Trophee)
class TropheeAdmin(admin.ModelAdmin):
    list_display = ['type_trophee', 'gagnant', 'etablissement', 'date_attribution', 'montant_total']
    list_filter = ['type_trophee', 'date_attribution', 'etablissement__type']
    search_fields = ['gagnant__pseudo', 'etablissement__nom']
    readonly_fields = ['date_attribution']
    date_hierarchy = 'date_attribution'


@admin.register(Pari)
class PariAdmin(admin.ModelAdmin):
    list_display = ['user', 'participant', 'montant', 'evenement', 'date_evenement', 'date_pari', 'gagne', 'resultat_disponible']
    list_filter = ['evenement', 'gagne', 'resultat_disponible', 'date_evenement', 'date_pari']
    search_fields = ['user__username', 'participant__pseudo']
    readonly_fields = ['date_pari', 'cote', 'montant_gains']
    date_hierarchy = 'date_pari'
    actions = ['calculer_resultats']
    
    def calculer_resultats(self, request, queryset):
        for pari in queryset.filter(gagne__isnull=True):
            # Ici vous pouvez implémenter la logique de calcul des résultats
            # basée sur les consommations des participants
            pass
        self.message_user(request, f"Calcul des résultats lancé pour {queryset.count()} pari(s).")
    calculer_resultats.short_description = "Calculer les résultats des paris"


@admin.register(ClassementQuotidien)
class ClassementQuotidienAdmin(admin.ModelAdmin):
    list_display = ['date', 'type_etablissement', 'participant', 'etablissement', 'montant_total', 'position']
    list_filter = ['date', 'type_etablissement', 'etablissement']
    search_fields = ['participant__pseudo', 'etablissement__nom']
    readonly_fields = ['date']
    date_hierarchy = 'date'
    ordering = ['date', 'type_etablissement', 'position']


@admin.register(ClassementEtablissement)
class ClassementEtablissementAdmin(admin.ModelAdmin):
    list_display = ['date', 'type_etablissement', 'etablissement', 'montant_total', 'position']
    list_filter = ['date', 'type_etablissement', 'etablissement']
    search_fields = ['etablissement__nom']
    readonly_fields = ['date']
    date_hierarchy = 'date'
    ordering = ['date', 'type_etablissement', 'position']


# Configuration de l'admin
admin.site.site_header = "Administration Soirée Clash"
admin.site.site_title = "Soirée Clash Admin"
admin.site.index_title = "Gestion de la plateforme Soirée Clash"
