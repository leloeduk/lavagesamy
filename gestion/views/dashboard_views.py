from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models import Count, Sum
import calendar
from gestion.models import Facture, Service

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'gestion/dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        factures = Facture.objects.select_related('service', 'laveur', 'auteur')
        services = Service.objects.all()

        current_year = timezone.now().year
        # Récupérer l'année sélectionnée, sinon année en cours
        selected_year = int(self.request.GET.get('year', current_year))
        # Récupérer le mois sélectionné, sinon 0 = "tout" (pas filtré sur le mois)
        selected_month = int(self.request.GET.get('month', 0))

        # Filtrer les factures par année et éventuellement par mois
        if selected_month and 1 <= selected_month <= 12:
            factures_filtered = factures.filter(
                date_heure__year=selected_year,
                date_heure__month=selected_month
            )
        else:
            factures_filtered = factures.filter(date_heure__year=selected_year)

        totaux = factures_filtered.aggregate(
            total_encaisse=Sum('montant_total'),
            total_commissions=Sum('commission_laveur'),
            part_entreprise=Sum('part_entreprise')
        )

        total = totaux['total_encaisse'] or 0
        commissions = totaux['total_commissions'] or 0
        part_entreprise = totaux['part_entreprise'] or 0

        # Statistiques mensuelles pour l'année sélectionnée
        monthly_stats = self.get_monthly_stats(factures, selected_year)

        # Liste années pour le filtre (exemple 5 dernières années)
        year_list = list(range(current_year - 5, current_year + 1))

        # Liste mois pour le filtre (index 0 = Tout)
        month_list = [(0, "Tous")] + [(i, calendar.month_name[i]) for i in range(1, 13)]

        context.update({
            'factures_count': factures_filtered.count(),
            'services_count': services.count(),
            'total_encaisse': total,
            'total_commissions': commissions,
            'benefice_net': total - commissions,
            'part_entreprise': part_entreprise,
            'recent_factures': factures_filtered.order_by('-date_heure')[:5],
            'pending_factures': factures_filtered.filter(statut='en_cours').count(),
            'facture_status_distribution': self.get_status_distribution(factures_filtered),
            'payment_method_distribution': self.get_payment_method_distribution(factures_filtered),
            'monthly_stats': monthly_stats,
            'months_labels': [stat['month'] for stat in monthly_stats],
            'chart_total': [stat['total'] for stat in monthly_stats],
            'chart_profit': [stat['profit'] for stat in monthly_stats],
            'chart_commissions': [stat['commissions'] for stat in monthly_stats],
            'chart_part': [stat['part_entreprise'] for stat in monthly_stats],
            'selected_year': selected_year,
            'year_list': year_list,
            'selected_month': selected_month,
            'month_list': month_list,
        })

        return context

    def get_status_distribution(self, factures):
        return factures.values('statut').annotate(count=Count('id')).order_by('-count')

    def get_payment_method_distribution(self, factures):
        return factures.values('mode_paiement').annotate(
            count=Count('id'),
            total=Sum('montant_total')
        ).order_by('-total')

    def get_monthly_stats(self, factures, year):
        stats = []
        for month in range(1, 13):
            data = factures.filter(
                date_heure__year=year,
                date_heure__month=month
            ).aggregate(
                count=Count('id'),
                total=Sum('montant_total'),
                commissions=Sum('commission_laveur'),
                part=Sum('part_entreprise'),
            )
            stats.append({
                'month': calendar.month_name[month],
                'count': data['count'] or 0,
                'total': data['total'] or 0,
                'commissions': data['commissions'] or 0,
                'profit': (data['total'] or 0) - (data['commissions'] or 0),
                'part_entreprise': data['part'] or 0,
            })
        return stats
