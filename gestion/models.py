from django.db import models

# Create your models here.
# gestion/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

# --- Utilisateur avec rôles ---
class User(AbstractUser):
    ROLES = (
        ('admin', 'Admin'),
        ('caissier', 'Caissier'),
        ('laveur', 'Laveur'),
        ('superviseur', 'Superviseur'),
    )
    nom_complet = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLES)
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.nom_complet} ({self.role})"

# --- Service de lavage ---
class Service(models.Model):
    nom = models.CharField(max_length=100)
    prix_total = models.DecimalField(max_digits=10, decimal_places=2)
    commission_laveur = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.nom

# --- Facture ---
class Facture(models.Model):
    STATUTS = (
        ('payé', 'Payé'),
        ('non_payé', 'Non payé'),
        ('en_cours', 'En cours'),
    )

    numero_facture = models.CharField(max_length=20, unique=True)
    nom_client = models.CharField(max_length=100, blank=True)
    auteur = models.ForeignKey(User, related_name="factures_creees", on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    laveur = models.ForeignKey(User, related_name="factures_realisees", on_delete=models.CASCADE)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2)
    commission_laveur = models.DecimalField(max_digits=10, decimal_places=2)
    part_entreprise = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_cours')
    mode_paiement = models.CharField(max_length=50, default='Espèce')
    date_heure = models.DateTimeField(auto_now_add=True)
    commentaire = models.TextField(blank=True)

    def __str__(self):
        return f"Facture {self.numero_facture} - {self.statut}"
