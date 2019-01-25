from django.shortcuts import render,redirect,reverse
from .forms import ConnexionForm,ImportForm
from django.forms import modelformset_factory
from django.contrib.auth import authenticate,login,logout
from tkinter.filedialog import askopenfilename
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
                return redirect('myapp_import')
            else: # sinon une erreur sera affichée
                error = True

    return render(request, 'myapp/connexion.html', locals())

def deconnexion(request):
    logout(request)
    return redirect(connexion)

def import_data(request):

    if request.method == 'POST':
        paillasse = request.FILES['file'].read().decode('cp1252').split("\n")[:-1]
        dico1 = []
        dico2 = {}
        liste_echantillon = []
        container_type = []
        nb_echantillon = 0
        for line in paillasse:
            ls = line.split(';')
            tmp = []
            ls[5]=ls[5].lower()
            tmp.append(ls[1])
            tmp.append(ls[5])
            dico1.append(tmp)
            dico2[ls[5]] = ls[7]
        for cle in dico2.keys():
            cle=cle.lower()
            tmp_type = Type_analyse.objects.all().values_list('nom',flat=True)
            for tp in tmp_type:
                if tp in cle:
                    container_type.append(tp)

        request.session['type_analyses'] = container_type
        request.session['type_analyses_echantillon']= dico1

        return redirect(choix_analyse)

    else :
        form=  ImportForm()



    return render(request, 'myapp/import_data.html',{'form': form} )

def choix_analyse(request):
    if 'type_analyses' in request.session:
        les_types = request.session['type_analyses']
        if request.method == 'POST':
            choix=request.POST['choix']
            type_analyse = Type_analyse.objects.filter(nom=choix)
            les_parametres=[]
            param_interne_analyse = type_analyse[0].parametre_interne.all().values_list('nom', flat=True)
            for elmt in param_interne_analyse:
                les_parametres.append(elmt)
            request.session['les_parametres'] = les_parametres
            request.session['choix'] = choix


            return redirect(feuille_calcul_data)
    else:
        les_types=""

    return render(request,'myapp/choix_analyse.html',{'les_types':les_types})

def feuille_calcul_data(request):
    num_echantillon=[]
    nb_echantillon=0
    type_analyses_echantillon = request.session['type_analyses_echantillon']
    param_interne_analyse= request.session['les_parametres']
    choix= request.session['choix']
    for nEchantillon in type_analyses_echantillon:
        if choix in nEchantillon[1]:
            num_echantillon.append(nEchantillon[0])
            nb_echantillon+=1
    analyseFormset = modelformset_factory(Analyse, fields=param_interne_analyse, max_num=nb_echantillon, min_num=nb_echantillon)
    if request.method == 'POST':
        formset = analyseFormset(request.POST, request.FILES)
        if formset.is_valid():
            for form in formset:
                numero = form.cleaned_data.get('nEchantillon')
                if numero:
                    echantillon= Echantillon.objects.filter(numero=numero)
                    Analyse(nEchantillon=numero, echantillon=echantillon, feuille_calcul=feuille).save()
        else:
            messages.error(request, "Formset not Valid")
    else:
        formset = analyseFormset()

    return render(request,'myapp/feuille_calcul.html',{'formset': analyseFormset})








