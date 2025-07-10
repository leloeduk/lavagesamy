from django.views.generic import ListView,  DetailView,UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from core.models import User
from core.forms import CustomUserUpdateForm
from django.views.generic.edit import FormMixin
from core.forms import CustomUserCreationForm , CustomUserUpdateForm
from django.views.generic.edit import DeleteView



class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'gestion/utilisateurs/list.html'
    context_object_name = 'utilisateurs'

    def test_func(self):
        return self.request.user.role == 'admin'

class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, FormMixin, DetailView):
    model = User
    template_name = 'gestion/utilisateurs/detail_update.html'
    context_object_name = 'user_detail'
    form_class = CustomUserUpdateForm

    def test_func(self):
        return self.request.user.role in ['admin','superviseur','caissier', 'laveur']

    def get_success_url(self):
        return reverse_lazy('gestion:utilisateur-detail-update', kwargs={'pk': self.object.pk})

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(instance=self.get_object(), **self.get_form_kwargs())

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        form = self.form_class(request.POST, instance=self.object)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilisateur mis à jour avec succès.")
            return super().form_valid(form)
        else:
            return self.form_invalid(form)  
    
class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'gestion/utilisateurs/confirm_delete.html'
    success_url = reverse_lazy('gestion:utilisateur-list')
  

    def test_func(self):
        return self.request.user.role in ['admin','superviseur','caissier', 'laveur']

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Utilisateur supprimé avec succès!")
        return super().delete(request, *args, **kwargs)
