import os
import shutil
import uuid
import random
import string
from django.conf import settings
from django.core.files.base import ContentFile
import base64
import time
from PIL import Image
import io

def generate_random_password(length=12):
    """Génère un mot de passe aléatoire sécurisé"""
    # Caractères autorisés
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%^&*"
    
    # S'assurer qu'il y a au moins un caractère de chaque type
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(symbols)
    ]
    
    # Remplir le reste avec des caractères aléatoires
    all_chars = lowercase + uppercase + digits + symbols
    for _ in range(length - 4):
        password.append(random.choice(all_chars))
    
    # Mélanger le mot de passe
    random.shuffle(password)
    return ''.join(password)

def is_pseudo_unique(pseudo):
    """Vérifie si un pseudo est unique dans tous les modèles"""
    from .models import DemandeAdhesion, Gestionnaire, Participant
    
    print(f"🔍 Vérification de l'unicité du pseudo: '{pseudo}'")
    
    # Vérifier dans DemandeAdhesion
    if DemandeAdhesion.objects.filter(pseudo=pseudo).exists():
        print(f"❌ Pseudo trouvé dans DemandeAdhesion")
        return False
    
    # Vérifier dans Gestionnaire
    if Gestionnaire.objects.filter(pseudo=pseudo).exists():
        print(f"❌ Pseudo trouvé dans Gestionnaire")
        return False
    
    # Vérifier dans Participant
    if Participant.objects.filter(pseudo=pseudo).exists():
        print(f"❌ Pseudo trouvé dans Participant")
        return False
    
    print(f"✅ Pseudo '{pseudo}' est unique")
    return True



def ensure_media_directories():
    """S'assure que tous les dossiers media nécessaires existent"""
    media_dirs = [
        'videos/demandes',
        'videos/etablissements',
        'miniatures/demandes',
        'miniatures/videos',
        'images',
        'uploads'
    ]
    
    for dir_path in media_dirs:
        full_path = os.path.join(settings.MEDIA_ROOT, dir_path)
        os.makedirs(full_path, exist_ok=True)
    
    return True

def save_recorded_video(video_data_base64, filename_prefix="video"):
    """Sauvegarde une vidéo enregistrée directement depuis le navigateur"""
    try:
        # Extraire les données de la vidéo
        if video_data_base64.startswith('data:video/'):
            header, encoded = video_data_base64.split(",", 1)
            video_data = base64.b64decode(encoded)
            
            # Générer un nom de fichier unique
            filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.webm"
            
            # Créer le fichier vidéo
            return ContentFile(video_data, name=filename)
        else:
            return None
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la vidéo: {e}")
        return None

def copy_file_to_service(file_field, destination_folder, filename_prefix=""):
    """Copie un fichier d'une demande vers un service"""
    try:
        if file_field and file_field.name:
            # Vérifier que le fichier existe physiquement
            if os.path.exists(file_field.path):
                # Créer le dossier de destination s'il n'existe pas
                os.makedirs(os.path.join(settings.MEDIA_ROOT, destination_folder), exist_ok=True)
                
                # Générer un nom de fichier unique
                base_name = os.path.basename(file_field.name)
                unique_filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}_{base_name}"
                destination_path = os.path.join(settings.MEDIA_ROOT, destination_folder, unique_filename)
                
                # Copier le fichier
                shutil.copy2(file_field.path, destination_path)
                
                # Retourner le chemin relatif pour la base de données
                return f'{destination_folder}/{unique_filename}'
            else:
                print(f"Fichier non trouvé: {file_field.path}")
                return None
        else:
            return None
    except Exception as e:
        print(f"Erreur lors de la copie du fichier: {e}")
        return None

def get_file_size_mb(file_path):
    """Retourne la taille d'un fichier en MB"""
    try:
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            return round(size_bytes / (1024 * 1024), 2)
        return 0
    except Exception:
        return 0

def cleanup_old_files(directory, max_age_days=30):
    """Nettoie les anciens fichiers temporaires"""
    try:
        current_time = time.time()
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > (max_age_days * 24 * 3600):
                    os.remove(file_path)
                    print(f"Fichier supprimé: {filename}")
    except Exception as e:
        print(f"Erreur lors du nettoyage: {e}")

def resize_image_to_standard_size(image_field, target_size=(300, 300), quality=85):
    """
    Redimensionne une image à une taille standard définie
    Args:
        image_field: Le champ ImageField Django
        target_size: Tuple (largeur, hauteur) en pixels
        quality: Qualité JPEG (1-100)
    Returns:
        ContentFile: L'image redimensionnée
    """
    try:
        if not image_field or not image_field.name:
            return None
            
        # Ouvrir l'image avec Pillow
        with Image.open(image_field) as img:
            # Convertir en RGB si nécessaire (pour les PNG avec transparence)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Calculer les nouvelles dimensions en gardant le ratio
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # Créer une nouvelle image avec la taille cible
            new_img = Image.new('RGB', target_size, (255, 255, 255))
            
            # Centrer l'image redimensionnée
            paste_x = (target_size[0] - img.width) // 2
            paste_y = (target_size[1] - img.height) // 2
            new_img.paste(img, (paste_x, paste_y))
            
            # Convertir en bytes
            output = io.BytesIO()
            new_img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            # Générer un nom de fichier unique
            base_name = os.path.splitext(os.path.basename(image_field.name))[0]
            new_filename = f"{base_name}_resized_{uuid.uuid4().hex[:8]}.jpg"
            
            return ContentFile(output.getvalue(), name=new_filename)
            
    except Exception as e:
        print(f"Erreur lors du redimensionnement de l'image: {e}")
        return None

def process_participant_photo(photo_field):
    """
    Traite la photo d'un participant pour la standardiser
    """
    if not photo_field:
        return None
    
    # Redimensionner à 300x300 pixels (format carré)
    resized_photo = resize_image_to_standard_size(photo_field, target_size=(300, 300))
    
    if resized_photo:
        return resized_photo
    else:
        # Si le redimensionnement échoue, retourner l'original
        return photo_field

def process_trophee_photo(photo_field):
    """
    Traite la photo d'un trophée pour la standardiser
    """
    if not photo_field:
        return None
    
    # Redimensionner à 400x400 pixels (format carré plus grand pour les trophées)
    resized_photo = resize_image_to_standard_size(photo_field, target_size=(400, 400))
    
    if resized_photo:
        return resized_photo
    else:
        # Si le redimensionnement échoue, retourner l'original
        return photo_field

def ensure_photo_directories():
    """S'assure que tous les dossiers photos nécessaires existent"""
    photo_dirs = [
        'photos/participants',
        'trophees',
        'miniatures/photos'
    ]
    
    for dir_path in photo_dirs:
        full_path = os.path.join(settings.MEDIA_ROOT, dir_path)
        os.makedirs(full_path, exist_ok=True)
    
    return True
