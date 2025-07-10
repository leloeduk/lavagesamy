from django.utils import timezone
from django.views import View
from django.http import HttpResponse
from django.template.loader import render_to_string
from gestion.models import Facture, Service
from core.models import User
from django.db.models import Sum
from weasyprint import HTML, CSS
import os
from django.conf import settings

class StatistiquePDFJourView(View):
    def get(self, request):
        today = timezone.localdate()
        specific_date = request.GET.get('specific_date')
        try:
            date = timezone.datetime.strptime(specific_date, '%Y-%m-%d').date() if specific_date else today
        except:
            date = today

        start = timezone.make_aware(timezone.datetime.combine(date, timezone.datetime.min.time()))
        end = start + timezone.timedelta(days=1)

        factures = Facture.objects.filter(date_heure__range=(start, end))
        stats = factures.aggregate(
            total=Sum('montant_total') or 0,
            commissions=Sum('commission_laveur') or 0,
            part=Sum('part_entreprise') or 0
        )

        context = {
            'period_name': f"Journée du {date.strftime('%d/%m/%Y')}",
            'now': timezone.now(),
            'factures_count': factures.count(),
            'services_count': Service.objects.count(),
            'total_encaisse': stats['total'] or 0,
            'total_commissions': stats['commissions'] or 0,
            'benefice_net': (stats['total'] or 0) - (stats['commissions'] or 0),
            'part_entreprise': stats['part'] or 0,
            'pending_factures': factures.filter(statut='en_cours').count(),
            'daily_stats': [{
                'date': date,
                'count': factures.count(),
                'revenue': stats['total'] or 0
            }],
        }

        html_string = render_to_string('gestion/statistiques/pdf_rapport_jour.html', context)
        css_path = os.path.join(settings.BASE_DIR, 'core/static/core/css/pdf.css')
        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(css_path)])

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_jour_{date.strftime('%Y_%m_%d')}.pdf"'
        return response
