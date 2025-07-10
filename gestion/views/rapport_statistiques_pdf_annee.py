import os
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML, CSS
from django.utils import timezone
from datetime import datetime
from gestion.models import Facture, Service
from core.models import User
import calendar
from django.db.models import Sum, Count, Q

def is_admin_or_supervisor(user):
    return user.is_authenticated and user.role in ['admin', 'superviseur', 'caissier']


@login_required
@user_passes_test(is_admin_or_supervisor)
def rapport_statistiques_pdf_annee(request):
    today = timezone.localdate()
    now = timezone.now()

    # Déterminer l'année sélectionnée ou utiliser l'année actuelle
    year = int(request.GET.get('year', today.year))

    start_date = timezone.make_aware(datetime(year, 1, 1))
    end_date = timezone.make_aware(datetime(year + 1, 1, 1))

    factures = Facture.objects.filter(date_heure__range=(start_date, end_date))

    stats = factures.aggregate(
        total_factures=Count('id'),
        total_revenue=Sum('montant_total'),
        total_commissions=Sum('commission_laveur'),
        net_profit=Sum('part_entreprise')
    )

    # Top services (sur l'année)
    top_services = (
        Service.objects
        .annotate(
            factures_count=Count('facture', filter=Q(facture__date_heure__range=(start_date, end_date))),
            total_revenue=Sum('facture__montant_total', filter=Q(facture__date_heure__range=(start_date, end_date)))
        )
        .order_by('-factures_count')
    )

    # Regroupement par mois actif
    monthly_data = []
    for month in range(1, 13):
        start_month = timezone.make_aware(datetime(year, month, 1))
        if month == 12:
            end_month = timezone.make_aware(datetime(year + 1, 1, 1))
        else:
            end_month = timezone.make_aware(datetime(year, month + 1, 1))

        f_month = factures.filter(date_heure__range=(start_month, end_month))
        count = f_month.count()
        if count > 0:
            monthly_data.append({
                'month': calendar.month_name[month],
                'count': count,
                'revenue': f_month.aggregate(total=Sum('montant_total'))['total'] or 0,
            })

    html_string = render_to_string('gestion/statistiques/pdf_rapport_annee.html', {
        'period_name': f"Année {year}",
        'stats': stats,
        'monthly_data': monthly_data,
        'top_services': top_services,
        'now': now,
    })

    css_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'core', 'css', 'pdf.css')

    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(css_path)])

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_statistiques_annee_{year}.pdf"'
    return response
