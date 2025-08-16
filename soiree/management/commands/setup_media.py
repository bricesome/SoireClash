from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Crée les dossiers media nécessaires pour l\'application'

    def handle(self, *args, **options):
        # Dossiers à créer
        media_dirs = [
            'videos/demandes',
            'videos/etablissements',
            'miniatures/demandes',
            'miniatures/videos',
            'images',
            'uploads'
        ]
        
        created_dirs = []
        existing_dirs = []
        
        for dir_path in media_dirs:
            full_path = os.path.join(settings.MEDIA_ROOT, dir_path)
            if not os.path.exists(full_path):
                os.makedirs(full_path, exist_ok=True)
                created_dirs.append(dir_path)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Dossier créé: {dir_path}')
                )
            else:
                existing_dirs.append(dir_path)
                self.stdout.write(
                    self.style.WARNING(f'⚠ Dossier existe déjà: {dir_path}')
                )
        
        # Créer le dossier media principal s'il n'existe pas
        if not os.path.exists(settings.MEDIA_ROOT):
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Dossier media principal créé: {settings.MEDIA_ROOT}')
            )
        
        # Résumé
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(f'✓ {len(created_dirs)} nouveaux dossiers créés')
        )
        self.stdout.write(
            self.style.WARNING(f'⚠ {len(existing_dirs)} dossiers existaient déjà')
        )
        self.stdout.write('='*50)
        
        if created_dirs:
            self.stdout.write('\nDossiers créés:')
            for dir_path in created_dirs:
                self.stdout.write(f'  - {dir_path}')
        
        if existing_dirs:
            self.stdout.write('\nDossiers existants:')
            for dir_path in existing_dirs:
                self.stdout.write(f'  - {dir_path}')
