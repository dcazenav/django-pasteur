from django import forms
from .models import *


#class ProfilForm(forms.ModelForm) :
class ConnexionForm(forms.Form) :
    username = forms.CharField(label="Nom d'utilisateur", max_length=30)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)

class ImportForm(forms.Form):
    file = forms.FileField()




