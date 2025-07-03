import os
from django.http import Http404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import CSS, HTML
from gestion.models import Facture

@login_required
def facture_pdf_view(request, pk):
    try:
        facture = Facture.objects.get(pk=pk)
    except Facture.DoesNotExist:
        raise Http404("Facture non trouvée")

    html_string = render_to_string('gestion/factures/pdf_template.html', {'facture': facture})

    css_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'core', 'css', 'pdf.css')

    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(css_path)])

    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"{facture.numero_facture}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
