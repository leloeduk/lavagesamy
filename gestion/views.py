import os
from django.http import Http404, HttpResponse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from weasyprint import CSS, HTML
from django.template.loader import render_to_string
from django.conf import settings
from .models import Facture, Service
from core.models import User
from .forms import FactureForm, ServiceForm
from core.forms import CustomUserCreationForm
from django.views.generic import TemplateView
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta
# from django.db.models import Q
from django.utils.timezone import now

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'gestion/dashboard/dashboard.html'
    
    def get_date_ranges(self):
        """Helper method to generate date ranges for statistics"""
        today = timezone.now().date()
        return {
            'today': today,
            'week_ago': today - timedelta(days=7),
            'month_ago': today - timedelta(days=30),
            'year_ago': today - timedelta(days=365),
        }

    def get_period_comparison(self, current_period_data, previous_period_data, field):
        """Calculate percentage change between periods"""
        current = current_period_data.get(field, 0) or 0
        previous = previous_period_data.get(field, 0) or 0
        if previous == 0:
            return 0
        return ((current - previous) / previous) * 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dates = self.get_date_ranges()
        
        # Base querysets
        factures = Facture.objects.select_related('service', 'laveur', 'auteur')
        services = Service.objects.all()
        
        # Current period stats
        current_month = now().month
        current_year = now().year
        
        # Performance metrics
        context.update({
            # Real-time counts
            'factures_count': factures.count(),
            'services_count': services.count(),
            
            # Financial totals
            'total_encaisse': factures.aggregate(
                total=Sum('montant_total')
            )['total'] or 0,
            'total_commissions': factures.aggregate(
                total=Sum('commission_laveur')
            )['total'] or 0,
            'benefice_net': factures.aggregate(
                net=Sum('montant_total') - Sum('commission_laveur')
            )['net'] or 0,
            
            # Recent activity
            'recent_factures': factures.order_by('-date_heure')[:5],
            'pending_factures': factures.filter(
                statut='en_cours'
            ).count(),
            
            # Status distribution
            'facture_status_distribution': self.get_status_distribution(factures),
            
            # Payment method distribution
            'payment_method_distribution': self.get_payment_method_distribution(factures),
        })
        
        # Time-based comparisons
        monthly_stats = self.get_monthly_stats(factures, current_year)
        context['monthly_stats'] = monthly_stats
        context['current_month_stats'] = next(
            (m for m in monthly_stats if m['month'] == f"{current_year}-{current_month:02d}"),
            {}
        )
        
        return context

    def get_status_distribution(self, factures):
        """Get count of factures by status"""
        return (
            factures.values('statut')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

    def get_payment_method_distribution(self, factures):
        """Get count of factures by payment method"""
        return (
            factures.values('mode_paiement')
            .annotate(count=Count('id'), total=Sum('montant_total'))
            .order_by('-total')
        )

    def get_monthly_stats(self, factures, current_year):
        """Generate monthly statistics for the current year"""
        monthly_stats = []
        
        for month in range(1, 13):
            month_data = factures.filter(
                date_heure__year=current_year,
                date_heure__month=month
            ).aggregate(
                count=Count('id'),
                total=Sum('montant_total'),
                commissions=Sum('commission_laveur'),
            )
            
            monthly_stats.append({
                'month': f"{current_year}-{month:02d}",
                'count': month_data['count'] or 0,
                'total': month_data['total'] or 0,
                'commissions': month_data['commissions'] or 0,
                'profit': (month_data['total'] or 0) - (month_data['commissions'] or 0),
            })
        
        return monthly_stats

# === Factures ===
class FactureListView(LoginRequiredMixin, ListView):
    model = Facture
    template_name = 'gestion/factures/list.html'
    context_object_name = 'factures'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrage par statut
        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
            
        # Filtrage par laveur (pour les superviseurs/laveurs)
        if self.request.user.role in ['laveur', 'superviseur']:
            queryset = queryset.filter(laveur=self.request.user)
            
        return queryset.select_related('service', 'laveur', 'auteur')


class FactureCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Facture
    form_class = FactureForm
    template_name = 'gestion/factures/create.html'
    success_url = '/gestion/factures/'  # ✨ Plus propre à mettre dans un reverse_lazy à long terme

    def test_func(self):
        # Seuls les admins et caissiers peuvent accéder à cette vue
        return self.request.user.role in ['admin', 'caissier']

    def form_valid(self, form):
        # Attribue l'auteur
        form.instance.auteur = self.request.user

        service = form.cleaned_data['service']
        montant_personnalise = form.cleaned_data.get('montant')

        if montant_personnalise:
            form.instance.montant_total = montant_personnalise
        else:
            form.instance.montant_total = service.prix_total

        # Toujours utiliser la commission du service
        form.instance.commission_laveur = service.commission_laveur

        # Calcul automatique de la part entreprise
        form.instance.part_entreprise = form.instance.montant_total - form.instance.commission_laveur

        messages.success(self.request, "✅ Facture créée avec succès !")
        return super().form_valid(form)

    def handle_no_permission(self):
        messages.error(self.request, "⛔ Vous n'avez pas la permission d'accéder à cette page.")
        return super().handle_no_permission()
    
class FactureDetailView(LoginRequiredMixin, DetailView):
    model = Facture
    template_name = 'gestion/factures/detail.html'
    context_object_name = 'facture'

    def get_queryset(self):
        return Facture.objects.all()    
class FactureUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Facture
    form_class = FactureForm
    template_name = 'gestion/factures/update.html'
    success_url = '/gestion/factures/'

    def test_func(self):
        return self.request.user.role in ['admin', 'caissier']

    def form_valid(self, form):
        service = form.cleaned_data['service']
        montant_personnalise = form.cleaned_data.get('montant')

        if montant_personnalise:
            form.instance.montant_total = montant_personnalise
        else:
            form.instance.montant_total = service.prix_total

        form.instance.commission_laveur = service.commission_laveur
        form.instance.part_entreprise = form.instance.montant_total - form.instance.commission_laveur

        messages.success(self.request, "✏️ Facture modifiée avec succès.")
        return super().form_valid(form)

class FactureDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Facture
    template_name = 'gestion/factures/confirm_delete.html'
    success_url = reverse_lazy('facture-list')  # à adapter selon tes noms d’URL

    def test_func(self):
        return self.request.user.role in ['admin', 'caissier']

    def delete(self, request, *args, **kwargs):
        messages.success(request, "🗑️ Facture supprimée avec succès.")
        return super().delete(request, *args, **kwargs)
   
# === Services ===
class ServiceListView(LoginRequiredMixin, ListView):
    model = Service
    template_name = 'gestion/services/list.html'
    context_object_name = 'services'

class ServiceCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'gestion/services/create.html'
    success_url = '/gestion/services/'
    
    def test_func(self):
        return self.request.user.role == 'admin'

# === Statistiques ===
class StatistiquesMensuellesView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Facture
    template_name = 'gestion/statistiques/mensuelles.html'
    
    def test_func(self):
        return self.request.user.role in ['admin', 'superviseur']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajoutez ici vos calculs de statistiques
        return context

# === Utilisateurs ===
class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'gestion/utilisateurs/list.html'
    context_object_name = 'users'
    
    def test_func(self):
        return self.request.user.role == 'admin'

class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'gestion/utilisateurs/create.html'
    success_url = reverse_lazy('utilisateur-list')
    
    def test_func(self):
        return self.request.user.role == 'admin'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Utilisateur créé avec succès!")
        return response
    
class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    template_name = 'gestion/utilisateurs/detail.html'
    context_object_name = 'user_detail'
    
    def test_func(self):
        return self.request.user.role == 'admin'

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'gestion/utilisateurs/confirm_delete.html'
    success_url = reverse_lazy('gestion:utilisateur-list')
    
    def test_func(self):
        return self.request.user.role == 'admin'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Utilisateur supprimé avec succès!")
        return super().delete(request, *args, **kwargs)
    

def facture_pdf_view(request, pk):
    try:
        facture = Facture.objects.get(pk=pk)
    except Facture.DoesNotExist:
        raise Http404("Facture non trouvée")

    # Render HTML template avec les données
    html_string = render_to_string('gestion/factures/pdf_template.html', {'facture': facture})

    # Chemin vers le CSS (dans static)
    css_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'core', 'css', 'pdf.css')  # ✅ correction ici

    # Génération PDF
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(css_path)])

    # Réponse HTTP avec le PDF
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"{facture.numero_facture}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

