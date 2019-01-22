from django.shortcuts import render,redirect
from .forms import ConnexionForm
from django.forms import modelformset_factory
from django.contrib.auth import authenticate,login,logout
from tkinter.filedialog import askopenfilename
from django.db.utils import DatabaseError
from django.contrib import messages
from django import forms
from .models import *


def connexion(request):
    error = False
    form = ConnexionForm(request.POST)
    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)  # Nous vérifions si les données sont correctes
            if user:  # Si l'objet renvoyé n'est pas None
                login(request, user)  # nous connectons l'utilisateur
                redirect()
            else: # sinon une erreur sera affichée
                error = True

    return render(request, 'myapp/connexion.html', locals())

def deconnexion(request):
    logout(request)
    return redirect(connexion)

def import_data(request):
    if request.method == "POST":
        filename = askopenfilename()
        file= open(filename)
        paillasse=file.read().split('\n')[:-1]
        file.close()
        dico1=[]
        dico2={}
        liste_echantillon=[]
        container_type=[]
        nb_echantillon=0
        for line in paillasse:
            ls=line.split(';')
            tmp=[]
            tmp.append(ls[1])
            tmp.append(ls[5])
            dico1.append(tmp)
            dico2[ls[5]]=ls[7]

        for cle in dico2.keys():
            tmp_type= Type_analyse.objects.filter(nom=cle)
            if tmp_type.exist():
                for tp in tmp_type :
                    container_type.append(tp)
        if len(container_type) !=0 :
            #Proposer quel analyse doit être faite#
            choix="siccite"
            type_analyse=Type_analyse.objects.filter(nom=choix)
            #Récupérer les échantillons correspondant à l'analyse #
            for elmt in dico1:
                if  choix in elmt[1] :
                    liste_echantillon.append(elmt[0])
                    nb_echantillon+=1

            #Récupérer les paramètre de l'analyse dans queryset
            param_interne_analyse= type_analyse[0].parametre_interne.all().values_list('nom',flat=True)
            param_externe_analyse= type_analyse[0].parametre_externe.all().values_list('nom',flat=True)
            array_param=()
            for elmt in param_interne_analyse:
                array_param.add(elmt)

            #Grâce au parametre trouver former le formulaire
            analyseFormset= modelformset_factory(Analyse,
                                                         fields=param_interne_analyse,
                                                         min_num=nb_echantillon,
                                                         max_num=nb_echantillon,
                                                         widgets = {'echantillon': forms.TextInput(attrs={'readonly': True})}
                                                         )
            analyseFormset = analyseFormset(initial=[{'echantillon': x} for x in liste_echantillon])
            #Passer les echantillons à la vue feuille de calcul
            return (request, 'myapp/feuille_calcul.html', {'formset': analyseFormset})
       # else
            #Il n'y a pas de technique manuelle trouvé dans cette feuille de paillasse




    return(request,'myapp/page_import.html',locals())

def test_form(request):
    feuilles= Feuille_calcul.objects.all()
    feuille= feuilles[0]
    choix = "siccite"
    type_analyse = Type_analyse.objects.filter(nom=choix)
    param_interne_analyse = type_analyse[0].parametre_interne.all().values_list('nom', flat=True)
    array_num=['E99945601','E99945602','E99945603','E99945604','E99945605']
    analyseFormset = modelformset_factory(Analyse, fields=param_interne_analyse, max_num=4,min_num=4)
    analyseFormset=analyseFormset(initial=[{'nEchantillon': x } for x in array_num])

    if request.method=="POST":
            for form in analyseFormset:
                    try:
                        analyse=form.save(commit=False)
                        echantillon=Echantillon.objects.filter(numero='E99945601')
                        analyse.echantillon=echantillon[0]
                        analyse.feuille_calcul=feuille
                        analyse.save()
                    except DatabaseError:
                            messages.error(request, "Database error. Please try again")

            analyseFormset.save()


    return render(request, 'myapp/test.html', {'formset': analyseFormset})
