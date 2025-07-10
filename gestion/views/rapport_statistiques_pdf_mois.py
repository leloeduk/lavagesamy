import os
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import CSS, HTML
from django.utils import timezone
from datetime import datetime, timedelta
from gestion.models import Facture, Service
from core.models import User
from django.db.models import Sum, Count, F, Q


def is_admin_or_supervisor(user):
    return user.is_authenticated and user.role in ['admin', 'superviseur', 'caissier']


@login_required
@user_passes_test(is_admin_or_supervisor)
def rapport_statistiques_pdf_mois(request):
    today = timezone.localdate()

    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year = today.year
        month = today.month

    start_date = timezone.make_aware(datetime(year, month, 1))
    if month == 12:
        end_date = timezone.make_aware(datetime(year + 1, 1, 1))
    else:
        end_date = timezone.make_aware(datetime(year, month + 1, 1))

    period_name = f"Mois de {start_date.strftime('%B %Y')}"

    factures = Facture.objects.filter(date_heure__range=(start_date, end_date))

    stats = factures.aggregate(
        total_factures=Count('id'),
        total_revenue=Sum('montant_total'),
        total_commissions=Sum('commission_laveur'),
        net_profit=Sum(F('montant_total') - F('commission_laveur')),
        part_entreprise=Sum('part_entreprise')
    )

    # Résumé journalier
    daily_stats = []
    current_day = start_date
    while current_day < end_date:
        next_day = current_day + timedelta(days=1)
        daily_factures = factures.filter(date_heure__range=(current_day, next_day))
        if daily_factures.exists():
            daily_stats.append({
                'date': current_day.date(),
                'count': daily_factures.count(),
                'revenue': daily_factures.aggregate(total=Sum('montant_total'))['total'] or 0
            })
        current_day = next_day

    services_count = Service.objects.count()
    pending_factures = factures.filter(statut='en_cours').count()

    month_names = [
    (1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'), (5, 'Mai'), (6, 'Juin'),
    (7, 'Juillet'), (8, 'Août'), (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre')
]

    html_string = render_to_string('gestion/statistiques/pdf_rapport_mois.html', {
    'period_name': period_name,
    'stats': stats,
    'services_count': services_count,
    'pending_factures': pending_factures,
    'now': timezone.now(),
    'daily_stats': daily_stats,
    'current_month': month,
    'current_year': year,
    'month_names': month_names,
    })

    css_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'core', 'css', 'pdf.css')

    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(css_path)])

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_mensuel_{month_names[month-1][1]}_{year}.pdf"'
    return response