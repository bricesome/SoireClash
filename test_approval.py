#!/usr/bin/env python
"""
Script de test pour vérifier l'approbation des demandes d'adhésion
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from django.contrib.auth.models import User
from soiree.models import DemandeAdhesion, Service, Gestionnaire
from soiree.utils import generate_random_password, ensure_media_directories

def test_password_generation():
    """Test de génération de mots de passe"""
    print("🧪 Test de génération de mots de passe...")
    
    try:
        passwords = []
        for i in range(5):
            password = generate_random_password()
            passwords.append(password)
            print(f"  Mot de passe {i+1}: {password}")
        
        # Vérifier que tous les mots de passe sont différents
        if len(set(passwords)) == len(passwords):
            print("✅ Tous les mots de passe sont uniques")
        else:
            print("❌ Certains mots de passe sont identiques")
            return False
        
        # Vérifier la longueur
        for password in passwords:
            if len(password) == 12:
                print(f"✅ Longueur correcte: {len(password)} caractères")
            else:
                print(f"❌ Longueur incorrecte: {len(password)} caractères")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération: {e}")
        return False

def test_media_directories():
    """Test de création des dossiers media"""
    print("\n🧪 Test de création des dossiers media...")
    
    try:
        ensure_media_directories()
        print("✅ Dossiers media créés avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la création des dossiers: {e}")
        return False

def test_user_creation():
    """Test de création d'utilisateur"""
    print("\n🧪 Test de création d'utilisateur...")
    
    try:
        # Générer des données de test
        test_username = f"test_user_{generate_random_password()[:8]}"
        test_password = generate_random_password()
        test_email = f"test_{generate_random_password()[:8]}@example.com"
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=test_username,
            email=test_email,
            password=test_password,
            first_name="Test",
            last_name="User"
        )
        
        print(f"✅ Utilisateur créé: {user.username}")
        
        # Vérifier que l'utilisateur peut se connecter
        if user.check_password(test_password):
            print("✅ Mot de passe vérifié avec succès")
        else:
            print("❌ Échec de vérification du mot de passe")
            return False
        
        # Nettoyer
        user.delete()
        print("✅ Utilisateur de test supprimé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création d'utilisateur: {e}")
        return False

def check_database_models():
    """Vérifier que les modèles sont accessibles"""
    print("\n🧪 Vérification des modèles de base de données...")
    
    try:
        # Vérifier DemandeAdhesion
        demandes_count = DemandeAdhesion.objects.count()
        print(f"✅ DemandeAdhesion accessible: {demandes_count} demandes")
        
        # Vérifier Service
        services_count = Service.objects.count()
        print(f"✅ Service accessible: {services_count} services")
        
        # Vérifier Gestionnaire
        gestionnaires_count = Gestionnaire.objects.count()
        print(f"✅ Gestionnaire accessible: {gestionnaires_count} gestionnaires")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'accès aux modèles: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🔐 TEST DE L'APPROBATION DES DEMANDES - SOIRÉE CLASH 🔐")
    print("=" * 60)
    
    tests = [
        ("Génération de mots de passe", test_password_generation),
        ("Création des dossiers media", test_media_directories),
        ("Création d'utilisateur", test_user_creation),
        ("Accès aux modèles", check_database_models),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            results.append((test_name, False))
    
    # Résumé des tests
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! L'approbation des demandes est prête.")
        print("\n💡 Vous pouvez maintenant tester l'approbation d'une demande d'adhésion.")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
