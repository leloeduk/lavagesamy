from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from django.db.models import Sum, Count, F, Case, When, FloatField, Q
from datetime import datetime, timedelta
from gestion.models import Facture, Service
from core.models import User

class StatistiquesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'gestion/statistiques/statistiques.html'

    def test_func(self):
        return self.request.user.role in ['admin', 'superviseur']

    def get_date_filters(self):
        today = timezone.localdate()

        # Date spécifique journalière
        if self.request.GET.get('specific_date'):
            try:
                specific_date = datetime.strptime(self.request.GET.get('specific_date'), '%Y-%m-%d').date()
            except ValueError:
                specific_date = today
            start_date = timezone.make_aware(datetime.combine(specific_date, datetime.min.time()))
            end_date = start_date + timedelta(days=1)
            period_name = f"Journée du {specific_date.strftime('%d/%m/%Y')}"
            return start_date, end_date, period_name, 'daily'

        # Filtrage par mois
        if self.request.GET.get('month'):
            try:
                year = int(self.request.GET.get('year', today.year))
                month = int(self.request.GET.get('month'))
            except ValueError:
                year = today.year
                month = today.month
            start_date = timezone.make_aware(datetime(year, month, 1))
            # calcul fin du mois
            if month == 12:
                end_date = timezone.make_aware(datetime(year + 1, 1, 1))
            else:
                end_date = timezone.make_aware(datetime(year, month + 1, 1))
            period_name = f"Mois de {start_date.strftime('%B %Y')}"
            return start_date, end_date, period_name, 'monthly'

        # Filtrage par année
        if self.request.GET.get('year'):
            try:
                year = int(self.request.GET.get('year'))
            except ValueError:
                year = today.year
            start_date = timezone.make_aware(datetime(year, 1, 1))
            end_date = timezone.make_aware(datetime(year + 1, 1, 1))
            period_name = f"Année {year}"
            return start_date, end_date, period_name, 'yearly'

        # Par défaut, mois en cours
        start_date = timezone.make_aware(datetime(today.year, today.month, 1))
        if today.month == 12:
            end_date = timezone.make_aware(datetime(today.year + 1, 1, 1))
        else:
            end_date = timezone.make_aware(datetime(today.year, today.month + 1, 1))
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
            'current_year': int(self.request.GET.get('year', timezone.now().year)),
            'current_month': int(self.request.GET.get('month', timezone.now().month)),
            'specific_date': self.request.GET.get('specific_date'),
        })

        return context
