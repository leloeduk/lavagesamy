from django import forms
from .models import Facture, Service
from django.contrib.auth import get_user_model

User = get_user_model()

class FactureForm(forms.ModelForm):
    class Meta:
        model = Facture
        fields = ['nom_client', 'service', 'laveur', 'statut', 'commentaire']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['laveur'].queryset = User.objects.filter(role='laveur')

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['nom', 'prix_total', 'commission_laveur', 'description']
