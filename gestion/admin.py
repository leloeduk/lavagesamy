from django.contrib import admin

# Register your models here.
from .models import Facture, Service, User

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('numero_facture', 'nom_client', 'montant_total', 'statut', 'date_heure')
    list_filter = ('statut', 'date_heure', 'service')
    search_fields = ('numero_facture', 'nom_client')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prix_total', 'commission_laveur')
    search_fields = ('nom',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'is_staff')
    list_filter = ('role',)
    search_fields = ('username', 'email')
