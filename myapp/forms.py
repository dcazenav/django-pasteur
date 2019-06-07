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

class AnalyseForm(forms.ModelForm):
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '10'})},
    }
    class Meta:
        model = Analyse
        exclude = ['echantillon', 'feuille_calcul']
        widgets = {
            'nEchantillon': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var1_kmno4': forms.TextInput(attrs={'size': '12'}),
            'var2_kmno4': forms.TextInput(attrs={'size': '12'}),
            'var3_kmno4': forms.TextInput(attrs={'size': '12'}),
            'var4_kmno4': forms.TextInput(attrs={'size': '12'}),
            'var5_kmno4': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var1_siccite': forms.TextInput(attrs={'size': '12'}),
            'var2_siccite': forms.TextInput(attrs={'size': '12'}),
            'var3_siccite': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var4_siccite': forms.TextInput(attrs={'size': '12',}),
            'var5_siccite': forms.TextInput(attrs={'size': '12'}),
            'var6_siccite': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var7_siccite': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var8_siccite': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var1_mvs': forms.TextInput(attrs={'size': '12'}),
            'var2_mvs': forms.TextInput(attrs={'size': '12'}),
            'var3_mvs': forms.TextInput(attrs={'size': '12'}),
            'var4_mvs': forms.TextInput(attrs={'size': '12'}),
            'var5_mvs': forms.TextInput(attrs={'size': '12'}),
            'var6_mvs': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var7_mvs': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var8_mvs': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var9_mvs': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var4_mest': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var1_dco': forms.TextInput(attrs={'size': '12'}),
            'var2_dco': forms.TextInput(attrs={'size': '12'}),
            'var3_dco': forms.TextInput(attrs={'size': '12'}),
            'var4_dco': forms.TextInput(attrs={'size': '12'}),
            'var5_dco': forms.TextInput(attrs={'size': '12'}),
            'var1_ntk': forms.TextInput(attrs={'size': '12'}),
            'var2_ntk': forms.TextInput(attrs={'size': '12'}),
            'var3_ntk': forms.TextInput(attrs={'size': '12'}),
            'var4_ntk': forms.TextInput(attrs={'size': '12'}),
            'var5_ntk': forms.TextInput(attrs={'size': '12'}),
            'var6_ntk': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var1_dbo_avec_dilution': forms.TextInput(attrs={'size': '12'}),
            'var2_dbo_avec_dilution': forms.TextInput(attrs={'size': '12'}),
            'var3_dbo_avec_dilution': forms.TextInput(attrs={'size': '12'}),
            'var4_dbo_avec_dilution': forms.TextInput(attrs={'size': '12'}),
            'var5_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var6_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var7_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var8_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var9_dbo_avec_dilution': forms.TextInput(attrs={'size': '12'}),
            'var10_dbo_avec_dilution': forms.TextInput(attrs={'size': '12'}),
            'var11_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var12_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var13_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var14_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var15_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var16_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var17_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var1_dbo_sans_dilution': forms.TextInput(attrs={'size': '12'}),
            'var2_dbo_sans_dilution': forms.TextInput(attrs={'size': '12'}),
            'var3_dbo_sans_dilution': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var4_dbo_sans_dilution': forms.TextInput(attrs={'size': '12'}),
            'var5_dbo_sans_dilution': forms.TextInput(attrs={'size': '12'}),
            'var6_dbo_sans_dilution': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var7_dbo_sans_dilution': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var8_dbo_sans_dilution': forms.TextInput(attrs={'size': '12'}),
            'var9_dbo_sans_dilution': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var10_dbo_sans_dilution': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var1_sil_650': forms.TextInput(attrs={'size': '12'}),
            'var2_sil_650': forms.TextInput(attrs={'size': '12'}),
            'var3_sil_650': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var1_sil_815': forms.TextInput(attrs={'size': '12'}),
            'var2_sil_815': forms.TextInput(attrs={'size': '12'}),
            'var3_sil_815': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var1_oxygene_dissous': forms.TextInput(attrs={'size': '12'}),
            'var2_oxygene_dissous': forms.TextInput(attrs={'size': '12'}),
            'var3_oxygene_dissous': forms.TextInput(attrs={'size': '12'}),
            'var4_oxygene_dissous': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var1_chlorophylle_scor_unesco': forms.TextInput(attrs={'size': '12'}),
            'var2_chlorophylle_scor_unesco': forms.TextInput(attrs={'size': '12'}),
            'var3_chlorophylle_scor_unesco': forms.TextInput(attrs={'size': '12'}),
            'var4_chlorophylle_scor_unesco': forms.TextInput(attrs={'size': '12'}),
            'var5_chlorophylle_scor_unesco': forms.TextInput(attrs={'size': '12'}),
            'var6_chlorophylle_scor_unesco': forms.TextInput(attrs={'size': '12'}),
            'var7_chlorophylle_scor_unesco': forms.TextInput(attrs={'size': '12'}),
            'var8_chlorophylle_scor_unesco': forms.TextInput(attrs={'size': '12'}),
            'var9_chlorophylle_scor_unesco': forms.TextInput(attrs={'size': '12'}),
            'var10_chlorophylle_scor_unesco': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var11_chlorophylle_scor_unesco': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var1_sabm': forms.TextInput(attrs={'size': '12'}),
            'var2_sabm': forms.TextInput(attrs={'size': '12'}),
            'var3_sabm': forms.TextInput(attrs={'size': '12'}),
            'var4_sabm': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var1_residu_sec': forms.TextInput(attrs={'size': '12'}),
            'var2_residu_sec': forms.TextInput(attrs={'size': '12'}),
            'var3_residu_sec': forms.TextInput(attrs={'size': '12'}),
            'var4_residu_sec': forms.TextInput(attrs={'size': '12'}),
            'var5_residu_sec': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var6_residu_sec': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var1_sil_bc': forms.TextInput(attrs={'size': '12'}),
            'var2_sil_bc': forms.TextInput(attrs={'size': '12'}),
            'var3_sil_bc': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var1_chlorophylle_lorenzen': forms.TextInput(attrs={'size': '12'}),
            'var2_chlorophylle_lorenzen': forms.TextInput(attrs={'size': '12'}),
            'var3_chlorophylle_lorenzen': forms.TextInput(attrs={'size': '12'}),
            'var4_chlorophylle_lorenzen': forms.TextInput(attrs={'size': '12'}),
            'var5_chlorophylle_lorenzen': forms.TextInput(attrs={'size': '12'}),
            'var6_chlorophylle_lorenzen': forms.TextInput(attrs={'size': '12'}),
            'var7_chlorophylle_lorenzen': forms.TextInput(attrs={'size': '12'}),
            'var8_chlorophylle_lorenzen': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var9_chlorophylle_lorenzen': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var10_chlorophylle_lorenzen': forms.TextInput(attrs={'readonly': True,'size': '12'}),
            'var11_chlorophylle_lorenzen': forms.TextInput(attrs={'readonly': True,'size': '12'})

        }












