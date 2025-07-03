from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from gestion.models import Facture
from gestion.forms import FactureForm

class FactureListView(LoginRequiredMixin, ListView):
    model = Facture
    template_name = 'gestion/factures/list.html'
    context_object_name = 'factures'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)

        if self.request.user.role in ['laveur', 'superviseur']:
            queryset = queryset.filter(laveur=self.request.user)

        return queryset.select_related('service', 'laveur', 'auteur')

class FactureCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Facture
    form_class = FactureForm
    template_name = 'gestion/factures/create.html'
    success_url = reverse_lazy('gestion:facture-list')

    def test_func(self):
        return self.request.user.role in ['admin', 'caissier']

    def form_valid(self, form):
        form.instance.auteur = self.request.user
        service = form.cleaned_data['service']
        montant_personnalise = form.cleaned_data.get('montant')

        if montant_personnalise:
            form.instance.montant_total = montant_personnalise
        else:
            form.instance.montant_total = service.prix_total

        form.instance.commission_laveur = service.commission_laveur
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
    success_url = reverse_lazy('gestion:facture-list')

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
    success_url = reverse_lazy('gestion:facture-list')

    def test_func(self):
        return self.request.user.role in ['admin', 'caissier']

    def delete(self, request, *args, **kwargs):
        messages.success(request, "🗑️ Facture supprimée avec succès.")
        return super().delete(request, *args, **kwargs)
