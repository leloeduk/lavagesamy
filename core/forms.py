# gestion/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from core.models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    nom_complet = forms.CharField(max_length=100, required=True)
    role = forms.ChoiceField(choices=User.ROLES, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'nom_complet', 'role', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.nom_complet = self.cleaned_data['nom_complet']
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user
    
def clean_email(self):
    email = self.cleaned_data['email']
    if User.objects.filter(email=email).exists():
        raise forms.ValidationError("Cet email est déjà utilisé. Veuillez en choisir un autre.")
    return email
