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


# Formulaire pour la mise à jour (Update)
class CustomUserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    nom_complet = forms.CharField(max_length=100, required=True)
    role = forms.ChoiceField(choices=User.ROLES, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'nom_complet', 'role')  # Pas de password ici
    
    def clean_email(self):
        email = self.cleaned_data['email']
        # Vérifie si un autre user a cet email
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Cet email est déjà utilisé par un autre utilisateur.")
        return email
    
    # Optionnel : si tu veux permettre la modif du username, ajouter une validation similaire

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.nom_complet = self.cleaned_data['nom_complet']
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user