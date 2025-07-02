import os
from django.http import Http404, HttpResponse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
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
from django.db.models import F, Sum, Count, Q, Case, When, FloatField
from datetime import datetime, timedelta
# from django.db.models import Q
from django.utils.timezone import now

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'gestion/dashboard/dashboard.html'
    
    def get_date_ranges(self):
        today = timezone.now().date()
        return {
            'today': today,
            'week_ago': today - timedelta(days=7),
            'month_ago': today - timedelta(days=30),
            'year_ago': today - timedelta(days=365),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dates = self.get_date_ranges()
        factures = Facture.objects.select_related('service', 'laveur', 'auteur')
        services = Service.objects.all()
        
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        context.update({
            'factures_count': factures.count(),
            'services_count': services.count(),
            'total_encaisse': factures.aggregate(total=Sum('montant_total'))['total'] or 0,
            'total_commissions': factures.aggregate(total=Sum('commission_laveur'))['total'] or 0,
            'benefice_net': factures.aggregate(net=Sum('montant_total') - Sum('commission_laveur'))['net'] or 0,
            'recent_factures': factures.order_by('-date_heure')[:5],
            'pending_factures': factures.filter(statut='en_cours').count(),
            'facture_status_distribution': self.get_status_distribution(factures),
            'payment_method_distribution': self.get_payment_method_distribution(factures),
            'monthly_stats': self.get_monthly_stats(factures, current_year),
        })
        
        return context

    def get_status_distribution(self, factures):
        return factures.values('statut').annotate(count=Count('id')).order_by('-count')

    def get_payment_method_distribution(self, factures):
        return factures.values('mode_paiement').annotate(
            count=Count('id'), 
            total=Sum('montant_total')
        ).order_by('-total')

    def get_monthly_stats(self, factures, current_year):
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
    success_url = reverse_lazy('service-list')
    
    def test_func(self):
        return self.request.user.role == 'admin'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Service créé avec succès!")
        return response

class ServiceDetailView(LoginRequiredMixin, DetailView):
    model = Service
    template_name = 'gestion/services/detail.html'
    context_object_name = 'service'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Vous pouvez ajouter des données supplémentaires ici si nécessaire
        # Par exemple, les factures associées à ce service
        context['factures_associees'] = self.object.facture_set.all()[:5]  # Les 5 dernières factures
        return context


class ServiceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'gestion/services/update.html'
    success_url = reverse_lazy('gestion:service-list')  # Assurez-vous d'utiliser le bon espace de noms

    def test_func(self):
        return self.request.user.role == 'admin'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Service mis à jour avec succès!")
        return response

class ServiceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Service
    template_name = 'gestion/services/confirm_delete.html'
    success_url = reverse_lazy('service-list')
    
    def test_func(self):
        return self.request.user.role == 'admin'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Service supprimé avec succès!")
        return super().delete(request, *args, **kwargs)
# === Statistiques ===
class StatistiquesMensuellesView(LoginRequiredMixin, UserPassesTestMixin, ListView):
   template_name = 'gestion/statistiques/statistiques.html'

   def test_func(self):
        return self.request.user.role in ['admin', 'superviseur']

   def get_date_filters(self):
        today = timezone.now().date()

        if self.request.GET.get('specific_date'):
            specific_date = datetime.strptime(self.request.GET.get('specific_date'), '%Y-%m-%d').date()
            start_date = timezone.make_aware(datetime.combine(specific_date, datetime.min.time()))
            end_date = start_date + timedelta(days=1)
            period_name = f"Journée du {specific_date.strftime('%d/%m/%Y')}"
            return start_date, end_date, period_name, 'daily'

        elif self.request.GET.get('month'):
            year = int(self.request.GET.get('year', today.year))
            month = int(self.request.GET.get('month'))
            start_date = timezone.make_aware(datetime(year, month, 1))
            end_date = timezone.make_aware(datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1))
            period_name = f"Mois de {start_date.strftime('%B %Y')}"
            return start_date, end_date, period_name, 'monthly'

        elif self.request.GET.get('year'):
            year = int(self.request.GET.get('year'))
            start_date = timezone.make_aware(datetime(year, 1, 1))
            end_date = timezone.make_aware(datetime(year + 1, 1, 1))
            period_name = f"Année {year}"
            return start_date, end_date, period_name, 'yearly'

        start_date = timezone.make_aware(datetime(today.year, today.month, 1))
        end_date = timezone.make_aware(datetime(today.year + 1, 1, 1) if today.month == 12 else datetime(today.year, today.month + 1, 1))
        period_name = "Mois en cours"
        return start_date, end_date, period_name, 'monthly'

   def get_washers_stats(self, start_date, end_date):
        return (
            User.objects
            .filter(role='laveur')
            .annotate(
                factures_count=Count('factures_realisees', filter=Q(factures_realisees__date_heure__range=(start_date, end_date))),
                total_commission=Sum('factures_realisees__commission_laveur', filter=Q(factures_realisees__date_heure__range=(start_date, end_date)))
            )
            .annotate(
                avg_per_facture=Case(
                    When(factures_count__gt=0, then=F('total_commission') / F('factures_count')),
                    default=0,
                    output_field=FloatField()
                )
            )
            .order_by('-total_commission')[:10]
        )

   def get_services_stats(self, start_date, end_date):
        return (
            Service.objects
            .annotate(
                factures_count=Count('facture', filter=Q(facture__date_heure__range=(start_date, end_date))),
                total_revenue=Sum('facture__montant_total', filter=Q(facture__date_heure__range=(start_date, end_date)))
            )
            .order_by('-factures_count')
        )

   def get_daily_stats(self, start_date, end_date):
        days = []
        current_day = start_date
        while current_day < end_date:
            next_day = current_day + timedelta(days=1)
            factures = Facture.objects.filter(date_heure__range=(current_day, next_day))
            days.append({
                'date': current_day.date(),
                'count': factures.count(),
                'revenue': factures.aggregate(total=Sum('montant_total'))['total'] or 0
            })
            current_day = next_day
        return days

   def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start_date, end_date, period_name, period_type = self.get_date_filters()
        factures = Facture.objects.filter(date_heure__range=(start_date, end_date))

        stats = factures.aggregate(
            total_factures=Count('id'),
            total_revenue=Sum('montant_total'),
            total_commissions=Sum('commission_laveur'),
            net_profit=Sum(F('montant_total') - F('commission_laveur'))
        )

        context.update({
            'period_name': period_name,
            'period_type': period_type,
            'start_date': start_date.date(),
            'end_date': (end_date - timedelta(seconds=1)).date(),
            'stats': {
                'factures': stats['total_factures'] or 0,
                'revenue': stats['total_revenue'] or 0,
                'commissions': stats['total_commissions'] or 0,
                'net_profit': stats['net_profit'] or 0,
                'avg_per_facture': (stats['total_revenue'] or 0) / (stats['total_factures'] or 1),
            },
            'top_washers': self.get_washers_stats(start_date, end_date),
            'top_services': self.get_services_stats(start_date, end_date),
            'daily_stats': self.get_daily_stats(start_date, end_date),
            'available_years': range(2020, timezone.now().year + 1),
            'available_months': [
                {'value': i, 'name': month}
                for i, month in enumerate([
                    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
                ], start=1)
            ],
            'current_year': self.request.GET.get('year', timezone.now().year),
            'current_month': self.request.GET.get('month', timezone.now().month),
            'specific_date': self.request.GET.get('specific_date'),
        })

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


class StatistiquesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'gestion/statistiques/statistiques.html'

    def test_func(self):
        return self.request.user.role in ['admin', 'superviseur']

    def get_date_filters(self):
        today = timezone.now().date()

        if self.request.GET.get('specific_date'):
            specific_date = datetime.strptime(self.request.GET.get('specific_date'), '%Y-%m-%d').date()
            start_date = timezone.make_aware(datetime.combine(specific_date, datetime.min.time()))
            end_date = start_date + timedelta(days=1)
            period_name = f"Journée du {specific_date.strftime('%d/%m/%Y')}"
            return start_date, end_date, period_name, 'daily'

        elif self.request.GET.get('month'):
            year = int(self.request.GET.get('year', today.year))
            month = int(self.request.GET.get('month'))
            start_date = timezone.make_aware(datetime(year, month, 1))
            end_date = timezone.make_aware(datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1))
            period_name = f"Mois de {start_date.strftime('%B %Y')}"
            return start_date, end_date, period_name, 'monthly'

        elif self.request.GET.get('year'):
            year = int(self.request.GET.get('year'))
            start_date = timezone.make_aware(datetime(year, 1, 1))
            end_date = timezone.make_aware(datetime(year + 1, 1, 1))
            period_name = f"Année {year}"
            return start_date, end_date, period_name, 'yearly'

        start_date = timezone.make_aware(datetime(today.year, today.month, 1))
        end_date = timezone.make_aware(datetime(today.year + 1, 1, 1) if today.month == 12 else datetime(today.year, today.month + 1, 1))
        period_name = "Mois en cours"
        return start_date, end_date, period_name, 'monthly'

    def get_washers_stats(self, start_date, end_date):
        return (
            User.objects
            .filter(role='laveur')
            .annotate(
                factures_count=Count('factures_realisees', filter=Q(factures_realisees__date_heure__range=(start_date, end_date))),
                total_commission=Sum('factures_realisees__commission_laveur', filter=Q(factures_realisees__date_heure__range=(start_date, end_date)))
            )
            .annotate(
                avg_per_facture=Case(
                    When(factures_count__gt=0, then=F('total_commission') / F('factures_count')),
                    default=0,
                    output_field=FloatField()
                )
            )
            .order_by('-total_commission')[:10]
        )

    def get_services_stats(self, start_date, end_date):
        return (
            Service.objects
            .annotate(
                factures_count=Count('facture', filter=Q(facture__date_heure__range=(start_date, end_date))),
                total_revenue=Sum('facture__montant_total', filter=Q(facture__date_heure__range=(start_date, end_date)))
            )
            .order_by('-factures_count')
        )

    def get_daily_stats(self, start_date, end_date):
        days = []
        current_day = start_date
        while current_day < end_date:
            next_day = current_day + timedelta(days=1)
            factures = Facture.objects.filter(date_heure__range=(current_day, next_day))
            days.append({
                'date': current_day.date(),
                'count': factures.count(),
                'revenue': factures.aggregate(total=Sum('montant_total'))['total'] or 0
            })
            current_day = next_day
        return days

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start_date, end_date, period_name, period_type = self.get_date_filters()
        factures = Facture.objects.filter(date_heure__range=(start_date, end_date))

        stats = factures.aggregate(
            total_factures=Count('id'),
            total_revenue=Sum('montant_total'),
            total_commissions=Sum('commission_laveur'),
            net_profit=Sum(F('montant_total') - F('commission_laveur'))
        )

        context.update({
            'period_name': period_name,
            'period_type': period_type,
            'start_date': start_date.date(),
            'end_date': (end_date - timedelta(seconds=1)).date(),
            'stats': {
                'factures': stats['total_factures'] or 0,
                'revenue': stats['total_revenue'] or 0,
                'commissions': stats['total_commissions'] or 0,
                'net_profit': stats['net_profit'] or 0,
                'avg_per_facture': (stats['total_revenue'] or 0) / (stats['total_factures'] or 1),
            },
            'top_washers': self.get_washers_stats(start_date, end_date),
            'top_services': self.get_services_stats(start_date, end_date),
            'daily_stats': self.get_daily_stats(start_date, end_date),
            'available_years': range(2020, timezone.now().year + 1),
            'available_months': [
                {'value': i, 'name': month}
                for i, month in enumerate([
                    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
                ], start=1)
            ],
            'current_year': self.request.GET.get('year', timezone.now().year),
            'current_month': self.request.GET.get('month', timezone.now().month),
            'specific_date': self.request.GET.get('specific_date'),
        })

        return context
