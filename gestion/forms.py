from django import forms
from .models import Facture, Service, User

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['nom', 'prix_total', 'commission_laveur', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class FactureForm(forms.ModelForm):
    class Meta:
        model = Facture
        fields = ['nom_client', 'service', 'laveur', 'statut', 'mode_paiement', 'commentaire']
        widgets = {
            'commentaire': forms.Textarea(attrs={'rows': 2}),
            'service': forms.Select(attrs={'class': 'form-select'}),
            'laveur': forms.Select(attrs={'class': 'form-select'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-select'}
                                          ),
                                          
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtre les laveurs seulement
        self.fields['laveur'].queryset = User.objects.filter(role='laveur')
    
    def clean_numero_facture(self):
        numero = self.cleaned_data['numero_facture']
        if Facture.objects.filter(numero_facture=numero).exists():
            raise forms.ValidationError("Ce numéro de facture existe déjà")
        return numero
