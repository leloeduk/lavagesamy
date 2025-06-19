from django.utils import timezone
import uuid
from django.db import models
from core.models import User


class Service(models.Model):
    nom = models.CharField(max_length=100)
    prix_total = models.DecimalField(max_digits=10, decimal_places=2)
    commission_laveur = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self):
        return f"{self.nom} - {self.prix_total} FCFA"

class Facture(models.Model):
    STATUTS = (
        ('payé', 'Payé'),
        ('non_payé', 'Non payé'),
        ('en_cours', 'En cours'),
    )
    
    MODES_PAIEMENT = (
        ('espèce', 'Espèce'),
        ('mobile', 'Mobile Money'),
        ('carte', 'Carte Bancaire'),
    )

    numero_facture = models.CharField(max_length=20, unique=True)
    nom_client = models.CharField(max_length=100, blank=True)
    auteur = models.ForeignKey(User, related_name="factures_creees", on_delete=models.PROTECT)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    laveur = models.ForeignKey(User, related_name="factures_realisees", 
                              limit_choices_to={'role': 'laveur'},
                              on_delete=models.PROTECT)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2)
    commission_laveur = models.DecimalField(max_digits=10, decimal_places=2)
    part_entreprise = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_cours')
    mode_paiement = models.CharField(max_length=20, choices=MODES_PAIEMENT, default='espèce')
    date_heure = models.DateTimeField(auto_now_add=True)
    commentaire = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_heure']
        verbose_name = "Facture"
        verbose_name_plural = "Factures"

    def save(self, *args, **kwargs):
        if not self.numero_facture:
            # Génère un numéro unique basé sur la date et un UUID
            date_part = timezone.now().strftime("%Y%m%d")
            unique_part = uuid.uuid4().hex[:6].upper()
            self.numero_facture = f"FACT-{date_part}-{unique_part}"
        
        # Calcul de la part entreprise
        self.part_entreprise = self.montant_total - self.commission_laveur
        super().save(*args, **kwargs)
    

    def __str__(self):
        return f"Facture {self.numero_facture} - {self.get_statut_display()}"