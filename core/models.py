from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    ROLES = (
        ('admin', 'Admin'),
        ('caissier', 'Caissier'),
        ('laveur', 'Laveur'),
        ('superviseur', 'Superviseur'),
    )
    
    # Définir email comme unique
    email = models.EmailField(unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # username est toujours requis pour AbstractUser
    
    nom_complet = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLES)
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']


    def __str__(self):
        return f"{self.nom_complet} ({self.get_role_display()})"
