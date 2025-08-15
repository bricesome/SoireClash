# 🚀 Fonctionnalité d'Adhésion Automatique - Soirée Clash

## 📋 Vue d'ensemble

Cette fonctionnalité permet de créer automatiquement un compte utilisateur et d'envoyer un email de réinitialisation de mot de passe lorsqu'une demande d'adhésion est approuvée par un administrateur.

## 🔧 Fonctionnalités implémentées

### 1. **Création automatique de compte**
- ✅ Création automatique de l'utilisateur Django
- ✅ Création automatique du profil utilisateur
- ✅ Création automatique du gestionnaire
- ✅ Création automatique de l'établissement
- ✅ Attribution automatique des rôles et permissions

### 2. **Email de réinitialisation automatique**
- ✅ Envoi automatique d'email lors de l'approbation
- ✅ Lien de réinitialisation sécurisé avec token
- ✅ Template d'email personnalisé avec le design Soirée Clash
- ✅ Expiration du lien après 24 heures

### 3. **Interface de réinitialisation complète**
- ✅ Formulaire de demande de réinitialisation
- ✅ Confirmation d'envoi d'email
- ✅ Formulaire de nouveau mot de passe
- ✅ Confirmation finale de changement

## 🎯 Comment ça fonctionne

### **Étape 1 : Demande d'adhésion**
1. Un établissement remplit le formulaire d'adhésion sur la page d'accueil
2. La demande est enregistrée avec le statut "en_attente"

### **Étape 2 : Approbation par l'admin**
1. L'administrateur se connecte à l'interface admin
2. Il va dans "Demandes d'adhésion"
3. Il sélectionne la demande et clique sur "Approuver les demandes sélectionnées"

### **Étape 3 : Création automatique**
1. **Création de l'établissement** : Service avec les informations fournies
2. **Création du compte utilisateur** : User Django avec pseudo et email
3. **Création du profil** : Profile avec pseudo et téléphone
4. **Création du gestionnaire** : Gestionnaire lié à l'établissement
5. **Envoi d'email** : Lien de réinitialisation de mot de passe

### **Étape 4 : Activation du compte**
1. Le gestionnaire reçoit l'email
2. Il clique sur le lien de réinitialisation
3. Il crée son nouveau mot de passe
4. Il peut se connecter et accéder à son dashboard

## 📁 Fichiers modifiés/créés

### **Fichiers modifiés :**
- `soiree/views.py` - Logique de création automatique
- `soiree/admin.py` - Action d'approbation automatique
- `conf/urls.py` - URLs de réinitialisation de mot de passe
- `templates/login.html` - Lien vers réinitialisation

### **Fichiers créés :**
- `templates/registration/password_reset_form.html` - Formulaire de demande
- `templates/registration/password_reset_done.html` - Confirmation d'envoi
- `templates/registration/password_reset_confirm.html` - Nouveau mot de passe
- `templates/registration/password_reset_complete.html` - Confirmation finale
- `templates/registration/password_reset_email.html` - Template d'email
- `templates/registration/password_reset_subject.txt` - Sujet d'email

## 🔐 Sécurité

- **Token sécurisé** : Utilisation du système Django de tokens
- **Expiration** : Liens valides 24 heures maximum
- **Validation** : Vérification de l'utilisateur et du token
- **HTTPS** : URLs construites avec le protocole approprié

## 📧 Configuration email

Assurez-vous que les paramètres SMTP sont configurés dans `conf/settings.py` :

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre_email@gmail.com'
EMAIL_HOST_PASSWORD = 'votre_mot_de_passe_app'
DEFAULT_FROM_EMAIL = 'votre_email@gmail.com'
```

## 🚀 Utilisation

### **Pour l'administrateur :**
1. Se connecter à l'admin Django
2. Aller dans "Demandes d'adhésion"
3. Sélectionner les demandes à approuver
4. Cliquer sur "Approuver les demandes sélectionnées"

### **Pour le gestionnaire :**
1. Recevoir l'email d'approbation
2. Cliquer sur le lien de réinitialisation
3. Créer un nouveau mot de passe
4. Se connecter avec ses identifiants

## ⚠️ Points d'attention

- **Gestion des erreurs** : Si la création échoue, la demande est marquée comme rejetée
- **Doublons** : Vérification des pseudo et email uniques
- **Permissions** : Seuls les administrateurs peuvent approuver les demandes
- **Logs** : Messages de succès/erreur dans l'interface admin

## 🔄 Workflow complet

```
Demande d'adhésion → Admin approuve → Compte créé automatiquement → 
Email envoyé → Gestionnaire réinitialise mot de passe → 
Connexion possible → Dashboard accessible
```

## 📞 Support

En cas de problème avec cette fonctionnalité, vérifiez :
1. La configuration email dans `settings.py`
2. Les logs du serveur Django
3. Les messages d'erreur dans l'interface admin
4. La validité des données de la demande d'adhésion
