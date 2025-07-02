from django import forms
from .models import Facture, Service, User

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['nom', 'prix_total', 'commission_laveur', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_nom'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'id': 'id_description', 'rows': 3}),
            'prix_total': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_prix_total', 'min': '0'}),
            'commission_laveur': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_commission_laveur', 'min': '0'}),
        }

class FactureForm(forms.ModelForm):
    class Meta:
        model = Facture
        fields = [
            'nom_client',
            'service',
            'laveur',
            'montant',  # ✅ Ajout ici
            'statut',
            'mode_paiement',
            'commentaire',
        ]
        widgets = {
            'commentaire': forms.Textarea(attrs={'rows': 2}),
            'service': forms.Select(attrs={'class': 'form-select'}),
            'laveur': forms.Select(attrs={'class': 'form-select'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-select'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),  # ✅ Widget propre
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['laveur'].queryset = User.objects.filter(role='laveur')
        self.fields['service'].queryset = Service.objects.all()
    
    def clean_numero_facture(self):
        numero = self.cleaned_data['numero_facture']
        if Facture.objects.filter(numero_facture=numero).exists():
            raise forms.ValidationError("Ce numéro de facture existe déjà")
        return numero
