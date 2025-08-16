from django.core.management.base import BaseCommand
from django.db import transaction
from soiree.models import Service, TypeBoisson


class Command(BaseCommand):
    help = 'Met à jour le statut types_boissons_enregistres pour tous les établissements'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Mise à jour du statut des boissons...')
        
        with transaction.atomic():
            # Récupérer tous les établissements
            services = Service.objects.all()
            updated_count = 0
            
            for service in services:
                # Vérifier si l'établissement a des types de boissons
                has_boissons = TypeBoisson.objects.filter(service=service, actif=True).exists()
                
                # Mettre à jour le statut si nécessaire
                if has_boissons and not service.types_boissons_enregistres:
                    service.types_boissons_enregistres = True
                    service.save()
                    updated_count += 1
                    self.stdout.write(f'✅ {service.nom}: Types de boissons marqués comme enregistrés')
                elif not has_boissons and service.types_boissons_enregistres:
                    service.types_boissons_enregistres = False
                    service.save()
                    updated_count += 1
                    self.stdout.write(f'❌ {service.nom}: Types de boissons marqués comme non enregistrés')
                else:
                    status = "enregistrés" if service.types_boissons_enregistres else "non enregistrés"
                    self.stdout.write(f'ℹ️  {service.nom}: Statut déjà correct ({status})')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'🎉 Mise à jour terminée ! {updated_count} établissement(s) mis à jour.'
                )
            )
            
            # Afficher un résumé
            total_services = services.count()
            services_with_boissons = services.filter(types_boissons_enregistres=True).count()
            services_without_boissons = total_services - services_with_boissons
            
            self.stdout.write(f'\n📊 Résumé:')
            self.stdout.write(f'   - Total établissements: {total_services}')
            self.stdout.write(f'   - Avec types de boissons: {services_with_boissons}')
            self.stdout.write(f'   - Sans types de boissons: {services_without_boissons}')
            
            # Afficher les établissements visibles pour les participants
            visible_services = services.filter(actif=True, types_boissons_enregistres=True)
            self.stdout.write(f'\n👥 Établissements visibles pour l\'inscription des participants:')
            for service in visible_services:
                boisson_count = TypeBoisson.objects.filter(service=service, actif=True).count()
                self.stdout.write(f'   - {service.nom} ({service.get_type_display()}): {boisson_count} type(s) de boisson(s)')
