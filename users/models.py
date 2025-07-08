from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
import os

def validate_profile_image(value):
    """Validar imagen de perfil"""
    filesize = value.size
    if filesize > 5 * 1024 * 1024:  # 5MB
        raise ValidationError("La imagen de perfil no puede ser mayor a 5MB.")
    
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Solo se permiten archivos de imagen (jpg, jpeg, png, gif, webp).')

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Estudiante'),
        ('instructor', 'Instructor'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student')
    profile_picture = models.ImageField(
        upload_to='profiles/', 
        null=True, 
        blank=True,
        validators=[validate_profile_image]
    )
    
    def __str__(self):
        return self.username
