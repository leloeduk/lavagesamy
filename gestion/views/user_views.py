from django.views.generic import ListView, CreateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from core.models import User
from core.forms import CustomUserCreationForm

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
