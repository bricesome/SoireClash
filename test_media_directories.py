#!/usr/bin/env python
"""
Script de test pour vérifier la création des dossiers media
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from django.conf import settings
from soiree.utils import ensure_media_directories

def test_media_directories():
    """Test de la création des dossiers media"""
    print("🧪 Test de création des dossiers media...")
    
    try:
        # Vérifier le MEDIA_ROOT
        print(f"📁 MEDIA_ROOT: {settings.MEDIA_ROOT}")
        
        # Créer les dossiers
        print("🔧 Création des dossiers media...")
        ensure_media_directories()
        
        # Vérifier que les dossiers existent
        media_dirs = [
            'videos/demandes',
            'videos/etablissements',
            'miniatures/demandes',
            'miniatures/videos',
            'images',
            'uploads'
        ]
        
        all_exist = True
        for dir_path in media_dirs:
            full_path = os.path.join(settings.MEDIA_ROOT, dir_path)
            if os.path.exists(full_path):
                print(f"✅ {dir_path} - Existe")
            else:
                print(f"❌ {dir_path} - N'existe pas")
                all_exist = False
        
        if all_exist:
            print("\n🎉 Tous les dossiers media ont été créés avec succès !")
        else:
            print("\n⚠️ Certains dossiers media n'ont pas été créés.")
        
        return all_exist
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_file_creation():
    """Test de création de fichiers dans les dossiers media"""
    print("\n🧪 Test de création de fichiers...")
    
    try:
        # Créer un fichier de test dans videos/demandes
        test_file_path = os.path.join(settings.MEDIA_ROOT, 'videos/demandes', 'test_video.txt')
        
        with open(test_file_path, 'w') as f:
            f.write("Test vidéo")
        
        if os.path.exists(test_file_path):
            print("✅ Fichier de test créé avec succès")
            
            # Nettoyer
            os.remove(test_file_path)
            print("✅ Fichier de test supprimé")
            return True
        else:
            print("❌ Impossible de créer le fichier de test")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test de création de fichier: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("📁 TEST DE LA CRÉATION DES DOSSIERS MEDIA - SOIRÉE CLASH 📁")
    print("=" * 60)
    
    # Test 1: Création des dossiers
    test1_success = test_media_directories()
    
    # Test 2: Création de fichiers
    test2_success = test_file_creation()
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    print(f"📁 Création des dossiers: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"📄 Création de fichiers: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    total_tests = 2
    passed_tests = sum([test1_success, test2_success])
    
    print(f"\n🎯 Résultat: {passed_tests}/{total_tests} tests réussis")
    
    if passed_tests == total_tests:
        print("🎉 Tous les tests sont passés ! Les dossiers media sont prêts.")
        print("\n💡 Vous pouvez maintenant tester l'upload de vidéos.")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez la configuration.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
