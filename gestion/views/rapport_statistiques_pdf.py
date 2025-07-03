import os
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import CSS, HTML
from django.utils import timezone
from datetime import datetime, timedelta
from gestion.models import Facture, Service
from core.models import User
from django.db.models import Sum, Count, F, Case, When, FloatField, Q


def is_admin_or_supervisor(user):
    return user.is_authenticated and user.role in ['admin', 'superviseur']


@login_required
@user_passes_test(is_admin_or_supervisor)
def rapport_statistiques_pdf_view(request):
    today = timezone.localdate()

    # --- Filtrage de la période ---
    # Tu peux réutiliser ta logique get_date_filters ici:
    def get_date_filters():
        # Date spécifique journalière
        if request.GET.get('specific_date'):
            try:
                specific_date = datetime.strptime(request.GET.get('specific_date'), '%Y-%m-%d').date()
            except ValueError:
                specific_date = today
            start_date = timezone.make_aware(datetime.combine(specific_date, datetime.min.time()))
            end_date = start_date + timedelta(days=1)
            period_name = f"Journée du {specific_date.strftime('%d/%m/%Y')}"
            return start_date, end_date, period_name

        # Filtrage par mois
        if request.GET.get('month'):
            try:
                year = int(request.GET.get('year', today.year))
                month = int(request.GET.get('month'))
            except ValueError:
                year = today.year
                month = today.month
            start_date = timezone.make_aware(datetime(year, month, 1))
            if month == 12:
                end_date = timezone.make_aware(datetime(year + 1, 1, 1))
            else:
                end_date = timezone.make_aware(datetime(year, month + 1, 1))
            period_name = f"Mois de {start_date.strftime('%B %Y')}"
            return start_date, end_date, period_name

        # Filtrage par année
        if request.GET.get('year'):
            try:
                year = int(request.GET.get('year'))
            except ValueError:
                year = today.year
            start_date = timezone.make_aware(datetime(year, 1, 1))
            end_date = timezone.make_aware(datetime(year + 1, 1, 1))
            period_name = f"Année {year}"
            return start_date, end_date, period_name

        # Par défaut : mois en cours
        start_date = timezone.make_aware(datetime(today.year, today.month, 1))
        if today.month == 12:
            end_date = timezone.make_aware(datetime(today.year + 1, 1, 1))
        else:
            end_date = timezone.make_aware(datetime(today.year, today.month + 1, 1))
        period_name = "Mois en cours"
        return start_date, end_date, period_name

    start_date, end_date, period_name = get_date_filters()

    factures = Facture.objects.filter(date_heure__range=(start_date, end_date))

    stats = factures.aggregate(
        total_factures=Count('id'),
        total_revenue=Sum('montant_total'),
        total_commissions=Sum('commission_laveur'),
        net_profit=Sum(F('montant_total') - F('commission_laveur'))
    )

    # Top laveurs
    top_washers = (
        User.objects.filter(role='laveur')
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

    # Top services
    top_services = (
        Service.objects
        .annotate(
            factures_count=Count('facture', filter=Q(facture__date_heure__range=(start_date, end_date))),
            total_revenue=Sum('facture__montant_total', filter=Q(facture__date_heure__range=(start_date, end_date)))
        )
        .order_by('-factures_count')
    )

    # Données journalières pour tableau
    days = []
    current_day = start_date
    while current_day < end_date:
        next_day = current_day + timedelta(days=1)
        daily_factures = Facture.objects.filter(date_heure__range=(current_day, next_day))
        days.append({
            'date': current_day.date(),
            'count': daily_factures.count(),
            'revenue': daily_factures.aggregate(total=Sum('montant_total'))['total'] or 0
        })
        current_day = next_day

    # Génération du HTML
    html_string = render_to_string('gestion/statistiques/pdf_rapport.html', {
        'period_name': period_name,
        'stats': stats,
        'top_washers': top_washers,
        'top_services': top_services,
        'daily_stats': days,
    })

    css_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'core', 'css', 'pdf.css')

    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(css_path)])

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_statistiques_{period_name.replace(" ", "_")}.pdf"'
    return response
