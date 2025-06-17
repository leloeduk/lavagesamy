from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count
from .models import Facture, Service, User
from .forms import FactureForm, ServiceForm

def home(request):
    """Vue pour la page d'accueil publique"""
    return render(request, 'home.html')

@login_required
def service_list(request):
    """Liste tous les services disponibles"""
    services = Service.objects.all().order_by('nom')
    return render(request, 'gestion/service_list.html', {'services': services})

@login_required
def facture_list(request):
    """Affiche la liste de toutes les factures"""
    factures = Facture.objects.select_related('auteur', 'service', 'laveur').order_by('-date_heure')
    return render(request, 'gestion/factures/facture_list.html', {'factures': factures})

@login_required
def facture_detail(request, pk):
    """Vue détaillée d'une facture spécifique"""
    facture = get_object_or_404(Facture.objects.select_related('auteur', 'service', 'laveur'), pk=pk)

    if not (request.user == facture.auteur or request.user.is_superuser):
        messages.error(request, "Vous n'avez pas accès à cette facture.")
        return redirect('gestion:facture_list')

    return render(request, 'gestion/factures/facture_detail.html', {
        'facture': facture,
        'can_edit': request.user == facture.auteur or request.user.is_superuser
    })

@login_required
def facture_create(request):
    """Crée une nouvelle facture"""
    if request.method == 'POST':
        form = FactureForm(request.POST)
        if form.is_valid():
            try:
                facture = form.save(commit=False)
                facture.auteur = request.user
                service = facture.service

                # Calculs financiers automatiques
                facture.montant_total = service.prix_total
                facture.commission_laveur = service.commission_laveur
                facture.part_entreprise = service.prix_total - service.commission_laveur

                # Génération du numéro de facture incrémental
                last_facture = Facture.objects.order_by('-id').first()
                new_id = last_facture.id + 1 if last_facture else 1
                facture.numero_facture = f"FAC{new_id:04}"

                facture.save()
                messages.success(request, "Facture créée avec succès.")
                return redirect('gestion:facture_list')

            except Exception as e:
                messages.error(request, f"Erreur lors de la création : {str(e)}")
    else:
        form = FactureForm()

    return render(request, 'gestion/factures/facture_form.html', {'form': form})

@login_required
def dashboard_view(request):
    """Tableau de bord avec statistiques principales"""
    stats = {
        'total_factures': Facture.objects.count(),
        'montant_total': Facture.objects.aggregate(total=Sum('montant_total'))['total'] or 0,
        'total_clients': Facture.objects.exclude(nom_client='').values('nom_client').distinct().count(),
        'total_laveurs': User.objects.filter(role='laveur').count(),
        'factures_recent': Facture.objects.select_related('service', 'laveur').order_by('-date_heure')[:10]
    }
    return render(request, 'dashboard.html', stats)

@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def service_create(request):
    """Création d'un nouveau service"""
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Service créé avec succès.")
            return redirect('gestion:service_list')
    else:
        form = ServiceForm()

    return render(request, 'gestion/services/service_form.html', {'form': form})

@login_required
def service_update(request, pk):
    """Modification d'un service existant"""
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service mis à jour avec succès.")
            return redirect('gestion:service_list')
    else:
        form = ServiceForm(instance=service)

    return render(request, 'gestion/services/service_form.html', {'form': form, 'service': service})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def service_delete(request, pk):
    """Suppression d'un service"""
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        service.delete()
        messages.success(request, "Service supprimé avec succès.")
        return redirect('gestion:service_list')

    return render(request, 'gestion/services/confirm_delete.html', {'object': service})
