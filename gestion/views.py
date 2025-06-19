from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
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
    success_url = '/gestion/factures/'

    def test_func(self):
        return self.request.user.role in ['admin', 'caissier']
    
    def form_valid(self, form):
        form.instance.auteur = self.request.user
        form.instance.montant_total = form.instance.service.prix_total
        form.instance.commission_laveur = form.instance.service.commission_laveur
        messages.success(self.request, "Facture créée avec succès!")
        return super().form_valid(form)
class FactureDetailView(DetailView):
    model = Facture
    template_name = 'gestion/factures/detail.html'     

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