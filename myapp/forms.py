from django import forms
from .models import *


class ConnexionForm(forms.Form) :
    username = forms.CharField(label="Nom d'utilisateur", max_length=30)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)


class DateInput(forms.DateInput):
    input_type = 'date'


class TimeInput(forms.TimeInput):
    input_type = 'time'


class Feuille_calculForm(forms.ModelForm):

    class Meta:
        model = Feuille_calcul
        exclude = ['profil','type_analyse','etalonnage']
        widgets = {
            'date_analyse': DateInput(),
            'heure_mise_sous_essai':TimeInput(),
            'date_etalonnage': DateInput(),
            'var4_mest': DateInput(),
            'var1_ntk' :DateInput(),
            'var1_dbo_avec_dilution':DateInput(),
            'var1_dbo_sans_dilution': DateInput(),
            'var3_chlorophylle_lorenzen': DateInput(),
            'var1_dco': DateInput(),
            'var2_dco': DateInput(),
            'var1_oxygene_dissous':forms.TextInput(attrs={'id':'id_ox_1'}),
            'var2_oxygene_dissous':forms.TextInput(attrs={'id':'id_ox_2','readonly': True}),
            'var5_dco':forms.TextInput(attrs={'id':'id_dco_1'}),
            'var6_dco':forms.TextInput(attrs={'id':'id_dco_2','readonly': True}),
            'var7_dco': forms.TextInput(attrs={'id': 'id_dco_3'}),
            'var10_dco': forms.TextInput(attrs={'id': 'id_dco_4', 'readonly': True})

        }













