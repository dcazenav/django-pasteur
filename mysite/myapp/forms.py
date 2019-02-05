from django import forms
from .models import *


class ConnexionForm(forms.Form) :
    username = forms.CharField(label="Nom d'utilisateur", max_length=30)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)


class ImportForm(forms.Form):
    file = forms.FileField()

class Feuille_paillasseForm(forms.ModelForm):
    class Meta:
        model=Feuille_paillasse
        fields=('numero_paillasse','poste')

class DateInput(forms.DateInput):
    input_type = 'date'

class TimeInput(forms.TimeInput):
    input_type = 'time'

class Feuille_calculForm(forms.ModelForm):

    class Meta:
        model = Feuille_calcul
        exclude = ['feuille_paillasse','type_analyse']
        widgets = {
            'date_analyse': DateInput(),
            'heure_mise_sous_essai':TimeInput(),
        }











