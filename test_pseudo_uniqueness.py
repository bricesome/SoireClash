#!/usr/bin/env python
"""
Script de test pour vérifier la gestion des pseudos uniques
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from django.contrib.auth.models import User
from soiree.models import DemandeAdhesion, Service, Gestionnaire, Participant
from soiree.utils import is_pseudo_unique, generate_unique_pseudo, generate_random_password

def test_pseudo_uniqueness_check():
    """Test de la vérification d'unicité des pseudos"""
    print("🧪 Test de vérification d'unicité des pseudos...")
    
    try:
        # Test avec un pseudo qui n'existe pas
        test_pseudo = f"test_unique_{generate_random_password()[:8]}"
        if is_pseudo_unique(test_pseudo):
            print("✅ Pseudo unique détecté correctement")
        else:
            print("❌ Pseudo unique non détecté")
            return False
        
        # Créer un utilisateur et un service de test
        test_username = f"test_user_{generate_random_password()[:8]}"
        test_password = generate_random_password()
        test_email = f"test_{generate_random_password()[:8]}@example.com"
        
        user = User.objects.create_user(
            username=test_username,
            email=test_email,
            password=test_password,
            first_name="Test",
            last_name="User"
        )
        
        service = Service.objects.create(
            nom="Établissement de Test",
            type="maquis",
            localisation="Quartier Test",
            adresse="Adresse Test",
            proprietaire=user,
            actif=True
        )
        
        # Créer un gestionnaire avec le pseudo de test
        gestionnaire = Gestionnaire.objects.create(
            user=user,
            service=service,
            tel="+22670123456",
            pseudo=test_pseudo,
            nom="Test",
            prenom="User",
            fonction="gerant"
        )
        
        # Maintenant le pseudo ne devrait plus être unique
        if not is_pseudo_unique(test_pseudo):
            print("✅ Pseudo non unique détecté correctement après création")
        else:
            print("❌ Pseudo non unique non détecté après création")
            return False
        
        # Nettoyer
        gestionnaire.delete()
        service.delete()
        user.delete()
        print("✅ Données de test supprimées")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'unicité: {e}")
        return False

def test_generate_unique_pseudo():
    """Test de génération de pseudo unique"""
    print("\n🧪 Test de génération de pseudo unique...")
    
    try:
        # Test avec un pseudo de base
        base_pseudo = "test_base"
        
        # Générer un pseudo unique
        unique_pseudo = generate_unique_pseudo(base_pseudo)
        print(f"✅ Pseudo unique généré: {unique_pseudo}")
        
        # Vérifier qu'il est bien unique
        if is_pseudo_unique(unique_pseudo):
            print("✅ Le pseudo généré est bien unique")
        else:
            print("❌ Le pseudo généré n'est pas unique")
            return False
        
        # Créer un gestionnaire avec ce pseudo
        test_username = f"test_user_{generate_random_password()[:8]}"
        test_password = generate_random_password()
        test_email = f"test_{generate_random_password()[:8]}@example.com"
        
        user = User.objects.create_user(
            username=test_username,
            email=test_email,
            password=test_password,
            first_name="Test",
            last_name="User"
        )
        
        service = Service.objects.create(
            nom="Établissement de Test 2",
            type="maquis",
            localisation="Quartier Test 2",
            adresse="Adresse Test 2",
            proprietaire=user,
            actif=True
        )
        
        gestionnaire = Gestionnaire.objects.create(
            user=user,
            service=service,
            tel="+22670123457",
            pseudo=unique_pseudo,
            nom="Test",
            prenom="User",
            fonction="gerant"
        )
        
        # Maintenant, générer un autre pseudo unique avec la même base
        # devrait donner un pseudo différent
        new_unique_pseudo = generate_unique_pseudo(base_pseudo)
        print(f"✅ Nouveau pseudo unique généré: {new_unique_pseudo}")
        
        if new_unique_pseudo != unique_pseudo:
            print("✅ Les pseudos sont bien différents")
        else:
            print("❌ Les pseudos sont identiques")
            return False
        
        # Vérifier que le nouveau pseudo est unique
        if is_pseudo_unique(new_unique_pseudo):
            print("✅ Le nouveau pseudo est bien unique")
        else:
            print("❌ Le nouveau pseudo n'est pas unique")
            return False
        
        # Nettoyer
        gestionnaire.delete()
        service.delete()
        user.delete()
        print("✅ Données de test supprimées")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de génération: {e}")
        return False

def test_pseudo_conflict_resolution():
    """Test de résolution des conflits de pseudo"""
    print("\n🧪 Test de résolution des conflits de pseudo...")
    
    try:
        # Créer plusieurs utilisateurs avec des pseudos similaires
        base_pseudo = "conflict_test"
        pseudos_crees = []
        
        for i in range(3):
            test_username = f"test_user_{i}_{generate_random_password()[:8]}"
            test_password = generate_random_password()
            test_email = f"test_{i}_{generate_random_password()[:8]}@example.com"
            
            user = User.objects.create_user(
                username=test_username,
                email=test_email,
                password=test_password,
                first_name=f"Test{i}",
                last_name="User"
            )
            
            service = Service.objects.create(
                nom=f"Établissement de Test {i}",
                type="maquis",
                localisation=f"Quartier Test {i}",
                adresse=f"Adresse Test {i}",
                proprietaire=user,
                actif=True
            )
            
            # Générer un pseudo unique
            unique_pseudo = generate_unique_pseudo(base_pseudo)
            pseudos_crees.append(unique_pseudo)
            
            gestionnaire = Gestionnaire.objects.create(
                user=user,
                service=service,
                tel=f"+2267012345{i}",
                pseudo=unique_pseudo,
                nom=f"Test{i}",
                prenom="User",
                fonction="gerant"
            )
            
            print(f"✅ Gestionnaire {i} créé avec le pseudo: {unique_pseudo}")
        
        # Vérifier que tous les pseudos sont uniques
        if len(set(pseudos_crees)) == len(pseudos_crees):
            print("✅ Tous les pseudos générés sont uniques")
        else:
            print("❌ Certains pseudos générés sont identiques")
            return False
        
        # Nettoyer
        for i in range(3):
            user = User.objects.get(username__startswith=f"test_user_{i}_")
            gestionnaire = Gestionnaire.objects.get(user=user)
            service = Service.objects.get(proprietaire=user)
            
            gestionnaire.delete()
            service.delete()
            user.delete()
        
        print("✅ Données de test supprimées")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de résolution des conflits: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🔐 TEST DE LA GESTION DES PSEUDOS UNIQUES - SOIRÉE CLASH 🔐")
    print("=" * 70)
    
    tests = [
        ("Vérification d'unicité", test_pseudo_uniqueness_check),
        ("Génération de pseudo unique", test_generate_unique_pseudo),
        ("Résolution des conflits", test_pseudo_conflict_resolution),
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
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! La gestion des pseudos uniques fonctionne parfaitement.")
        print("\n💡 Vous pouvez maintenant soumettre des demandes d'adhésion sans conflit de pseudo.")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
