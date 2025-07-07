from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from gestion.models import Facture, Service
from gestion.forms import ServiceForm
from django.db import transaction 

class ServiceListView(LoginRequiredMixin, ListView):
    model = Service
    template_name = 'gestion/services/list.html'
    context_object_name = 'services'
    

class ServiceCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'gestion/services/create.html'
    success_url = reverse_lazy('gestion:service-list')

    def test_func(self):
        return self.request.user.role in ['admin', 'superviseur' , 'caissier']

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
        context['factures_associees'] = self.object.facture_set.all()[:5]
        return context

class ServiceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'gestion/services/update.html'
    success_url = reverse_lazy('gestion:service-list')

    def test_func(self):
        return self.request.user.role in ['admin', 'superviseur' , 'caissier']

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Service mis à jour avec succès!")
        return response

class ServiceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Service
    template_name = 'gestion/services/confirm_delete.html'
    success_url = reverse_lazy('gestion:service-list')

    def test_func(self):
        return self.request.user.role in ['admin', 'superviseur' , 'caissier']

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        service = self.get_object()
        
        # 1. D'abord, mettre à jour toutes les factures liées
        Facture.objects.filter(service=service).update(service=None)
        
        # 2. Ensuite supprimer le service
        response = super().delete(request, *args, **kwargs)
        
        messages.success(request, "Service supprimé, les factures associées ont été conservées.")
        return response