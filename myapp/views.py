from django.shortcuts import render,redirect
from .forms import ConnexionForm,ImportForm,Feuille_calculForm
from django.forms import modelformset_factory,modelform_factory
from django.contrib.auth import authenticate,login,logout
from django import forms
from .models import *
from django.http import HttpResponse
import xlwt
from xhtml2pdf import pisa
from django.template.loader import render_to_string
import os.path,errno
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt


def connexion(request):
    error = False

    if request.user.is_authenticated:
        return redirect(import_data)
    if request.method == "POST":
        form = ConnexionForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)  # Nous vérifions si les données sont correctes
            if user:  # Si l'objet renvoyé n'est pas None
                login(request, user)  # nous connectons l'utilisateur
                return redirect('myapp_import')
            else: # sinon une erreur sera affichée
                error = True
    else:
        form = ConnexionForm()

    return render(request, 'myapp/connexion.html', locals())


def deconnexion(request):
    #Supression des paillasse et feuille de calcul vide
    profil = Profil.objects.filter(user=request.user)
    paillasse = Feuille_paillasse.objects.filter(profil=profil[0])
    for elmt1 in paillasse:
        verif = 0
        feuille_calcul = Feuille_calcul.objects.filter(feuille_paillasse=elmt1)
        for elmt2 in feuille_calcul:
            analyses = Analyse.objects.filter(feuille_calcul=elmt2)
            if analyses.exists():
                verif = 1
            else:
                elmt2.delete()
        if verif == 0:
            elmt1.delete()

    logout(request)
    return redirect(connexion)


def index_paillasse(request):
    #Supression des paillasses et feuilles de calcul vide et ajout des paillasses contenant de l'information dans un array
    # pour l'afficher à l'utilisateur. Les feuilles de paillasses sont spécifiques à l'utilisateur courant.
    profil=Profil.objects.filter(user=request.user)
    paillasse = Feuille_paillasse.objects.filter(profil=profil[0])
    array_paillasse=[]

    for elmt1 in paillasse:
        verif = 0
        feuille_calcul= Feuille_calcul.objects.filter(feuille_paillasse=elmt1)
        for elmt2 in feuille_calcul:
            analyses=Analyse.objects.filter(feuille_calcul=elmt2)
            if analyses.exists():
               verif=1
            else:
                elmt2.delete()
        if verif==0:
            elmt1.delete()
        else:
            array_paillasse.append(elmt1)
    return render(request,'myapp/index_paillasse.html',{'paillasse':array_paillasse})


def view_paillasse(request,id_feuille_paillasse):
    paillasse = Feuille_paillasse.objects.filter(id=id_feuille_paillasse)
    feuille_calcul=Feuille_calcul.objects.filter(feuille_paillasse=paillasse[0])
    return render(request,'myapp/view_paillasse.html', locals())



def import_data(request):
    profil = Profil.objects.filter(user=request.user)
    if request.method == 'POST':
        paillasse_data = request.FILES['file'].read().decode('cp1252').split("\n")[:-1]
        fullname=request.FILES['file'].name
        dico1 = []
        dico2 = {}
        dico3 ={'oxydab. kmno4 en mil. ac. à chaud': 'kmno4',
                'taux de siccité (%)': 'siccite',
                'matières volatiles sèches': 'mvs',
                'matières en suspension (filtre whatman': 'mest',
                'dem. chim. en oxygène': 'dco', 'azote kjeldahl (en n)': 'ntk',
                'silicates (en mg/l de sio2)': 'silicate',
                'oxygène dissous % saturation': 'oxygene dissous',
                'chlorophylle alpha': 'chlorophylle',
                'agents de surface': 'sabm',
                'résidu sec à 180°c': 'residu sec',
                'silice(µmol/l sio2)': 'silice',
                'dbo5': 'dbo5'}

        container_type = []
        for line in paillasse_data:
            ls = line.split(';')
            tmp = []
            ls[5] = ls[5].lower()
            for cle2 in dico3.keys():
                if cle2 in ls[5]:
                    tmp.append(ls[1])
                    tmp.append(dico3[cle2])
                    dico1.append(tmp)
                    dico2[ls[5]] = ls[7]
                    if dico3[cle2] not in container_type:
                        container_type.append(dico3[cle2])

        paillasse, created = Feuille_paillasse.objects.get_or_create(profil=profil[0], numero_paillasse=fullname)
        request.session['paillasse_id'] = paillasse.id
        request.session['type_analyses'] = container_type
        request.session['type_analyses_echantillon']= dico1
        return redirect(choix_analyse)
    else:
        form = ImportForm()

    return render(request, 'myapp/import_data.html',{'form': form})


def choix_analyse(request):

    if 'type_analyses' in request.session:
        les_types = request.session['type_analyses']
        if request.method == 'POST':
            choix = request.POST['choix']
            request.session['choix'] = choix
            if choix in ["dbo5","chlorophylle"]:
                return redirect(choix_specifique)

            type_analyse = Type_analyse.objects.filter(nom=choix)
            les_parametres = []
            parametres_externe = []
            param_interne_analyse = type_analyse[0].parametre_interne.all().values_list('nom', flat=True)
            param_externe_analyse = type_analyse[0].parametre_externe.all().values_list('nom', flat=True)

            for elmt in param_interne_analyse:
                les_parametres.append(elmt)
            for elmt in param_externe_analyse:
                parametres_externe.append(elmt)
            request.session['les_parametres'] = les_parametres
            request.session['parametres_externe'] = parametres_externe


            return redirect(externe_data_feuille_calcul)
    else:
        les_types=""

    return render(request,'myapp/choix_analyse.html',{'les_types':les_types})

def choix_specifique(request):
    if 'choix' in request.session and 'type_analyses_echantillon' in request.session:
        choix = request.session['choix']
        echantillon = request.session['type_analyses_echantillon']
        echantillon_specifique=[]
        choix_multiple=[]
        echantillon_selected_and_analyse=[]
        les_parametres = []
        parametres_externe = []

        if choix =="dbo5":
            choix_multiple=['dbo avec dilution','dbo sans dilution']
        if choix == "chlorophylle":
            choix_multiple=['chlorophylle lorenzen','chlorophylle scor unesco']
        for elmt in echantillon:
            if choix in elmt[1]:
                echantillon_specifique.append(elmt[0])
        if request.method == 'POST':
            choix_analyse= request.POST['radio_check']
            choix_echantillons = request.POST.getlist('checks')
            for elmt in choix_echantillons:
                couple = [elmt, choix_analyse]
                echantillon_selected_and_analyse.append(couple)

            type_analyse = Type_analyse.objects.filter(nom=choix_analyse)
            param_interne_analyse = type_analyse[0].parametre_interne.all().values_list('nom', flat=True)
            param_externe_analyse = type_analyse[0].parametre_externe.all().values_list('nom', flat=True)

            for elmt in param_interne_analyse:
                les_parametres.append(elmt)
            for elmt in param_externe_analyse:
                parametres_externe.append(elmt)
            request.session['les_parametres'] = les_parametres
            request.session['parametres_externe'] = parametres_externe
            request.session['type_analyses_echantillon'] = echantillon_selected_and_analyse
            request.session['choix']=choix_analyse
            return redirect(externe_data_feuille_calcul)

        return render(request,'myapp/choix_specifique.html',{'choix_multiple':choix_multiple,'echantillon': echantillon_specifique})


def externe_data_feuille_calcul(request):

    if 'parametres_externe' in request.session and 'paillasse_id' in request.session and 'choix' in request.session :
        paillasse= Feuille_paillasse.objects.filter(id=request.session['paillasse_id'])
        param_externe_analyse= request.session['parametres_externe']
        choix=request.session['choix']
        type_analyse = Type_analyse.objects.filter(nom=choix)
        feuille_calculForm = modelform_factory(Feuille_calcul,
                                               form=Feuille_calculForm,
                                               fields=param_externe_analyse,
                                               )
        form = feuille_calculForm(request.POST, request.FILES)
        if request.method == "POST":
            form = feuille_calculForm(request.POST, request.FILES)
            if form.is_valid():
                feuille_calcul = form.save(commit=False)
                feuille_calcul.feuille_paillasse=paillasse[0]
                feuille_calcul.type_analyse =type_analyse[0]
                feuille_calcul.save()
                request.session['feuille_calcul_id'] = feuille_calcul.id
                if choix in ['sabm','silice','silice ifremer','silicate'] :
                    return redirect(fix_etalonnage)
                else:
                    return redirect(feuille_calcul_data)
        else:
            form = feuille_calculForm()
        return render(request, 'myapp/externe_data.html',{'form': form})


def feuille_calcul_data(request):

    num_echantillon=[]
    num_echantillon2=[]
    nb_echantillon=0
    array_concentration=[]
    array_absorbance=[]
    parametre_etalonnage=""
    concentration_and_absorbance = {}
    static_name_fig=""
    error = False
    if 'type_analyses_echantillon' in request.session and 'les_parametres' in request.session and 'choix' in request.session and 'feuille_calcul_id' in request.session:
        type_analyses_echantillon = request.session['type_analyses_echantillon']
        param_interne_analyse= request.session['les_parametres']
        choix= request.session['choix']
        feuille_calcul = Feuille_calcul.objects.filter(id=request.session['feuille_calcul_id'])
        profil = Profil.objects.filter(user=request.user)
        nom_user= request.user.username
        path = os.path.abspath(os.path.dirname(__file__)) + "\static\myapp"+"\\"+nom_user
        static_name_fig="myapp/"+nom_user

        for nEchantillon in type_analyses_echantillon:
            if choix in nEchantillon[1]:
                num_echantillon.append(nEchantillon[0])
                #Renvoie un tuple (objet, créé) où objet est l’objet chargé ou créé et créé est une valeur booléenne indiquant si un nouvel objet a été créé.
                Echantillon.objects.get_or_create(numero=nEchantillon[0])
                nb_echantillon+=1

        if choix == "kmno4":
            for i in range(len(num_echantillon)):
                if i==0:
                    num_echantillon2.append("resorcinol")
                    num_echantillon2.append("BLANC")
                    Echantillon.objects.get_or_create(numero="resorcinol")
                    Echantillon.objects.get_or_create(numero="BLANC")
                    nb_echantillon += 2
                num_echantillon2.append(num_echantillon[i])
        elif choix=="mest" or choix == "dbo avec dilution":
            for i in range(len(num_echantillon)):
                if i == 0:
                    num_echantillon2.append("CTRL")
                    num_echantillon2.append("BLANC")
                    Echantillon.objects.get_or_create(numero="CTRL")
                    Echantillon.objects.get_or_create(numero="BLANC")
                    nb_echantillon += 2
                num_echantillon2.append(num_echantillon[i])
        elif choix == "dco":
            for i in range(len(num_echantillon)):
                if i == 0:
                    num_echantillon2.append("CTRL")
                    Echantillon.objects.get_or_create(numero="CTRL")
                    nb_echantillon += 1
                num_echantillon2.append(num_echantillon[i])
        elif choix == "ntk":
            for i in range(len(num_echantillon)):
                if i == 0:
                    num_echantillon2.append("nh4cl")
                    num_echantillon2.append("Glycine")
                    Echantillon.objects.get_or_create(numero="nh4cl")
                    Echantillon.objects.get_or_create(numero="Glycine")
                    nb_echantillon += 2
                num_echantillon2.append(num_echantillon[i])

        elif choix == "sabm":
            set_etalonnage= Etalonnage.objects.filter(profil=profil[0],type_analyse=feuille_calcul[0].type_analyse)[::-1]
            for etalonnage in set_etalonnage:
                array_concentration.append(float(etalonnage.c_lauryl.replace(',','.')))
                array_absorbance.append(float(etalonnage.absorbance.replace(',','.')))

            for i in range(len(num_echantillon)):
                if i == 0:
                    num_echantillon2.append("BLANC")
                    num_echantillon2.append("LQ")
                    num_echantillon2.append("CTRL")
                    Echantillon.objects.get_or_create(numero="BLANC")
                    Echantillon.objects.get_or_create(numero="LQ")
                    Echantillon.objects.get_or_create(numero="CTRL")
                nb_echantillon += 3
                num_echantillon2.append(num_echantillon[i])

        elif choix == "silice" or choix == "silicate" :
            set_etalonnage = Etalonnage.objects.filter(profil=profil[0],
                                                       type_analyse=feuille_calcul[0].type_analyse)[::-1]
            if choix =="silice":
                for etalonnage in set_etalonnage:
                    array_concentration.append(float((etalonnage.c_micromol_l).replace(',','.')))
                    array_absorbance.append(float((etalonnage.absorbance).replace(',','.')))
            else:
                for etalonnage in set_etalonnage:
                    array_concentration.append(float((etalonnage.c_mg).replace(',', '.')))
                    array_absorbance.append(float((etalonnage.absorbance).replace(',', '.')))
                    
            for i in range(len(num_echantillon)):
                if i % 10 == 0:
                    num_echantillon2.append("BLANC")
                    num_echantillon2.append("LQ")
                    num_echantillon2.append("CTRL")
                    if i == 0:
                        Echantillon.objects.get_or_create(numero="BLANC")
                        Echantillon.objects.get_or_create(numero="LQ")
                        Echantillon.objects.get_or_create(numero="CTRL")
                    nb_echantillon += 3

                num_echantillon2.append(num_echantillon[i])
        else:
            num_echantillon2 = num_echantillon

        # création du graphique d'absorbance
        if len(array_concentration) !=0 and len(array_absorbance)!=0:
            for i in range(len(array_concentration)):
                concentration_and_absorbance[array_concentration[i]] = array_absorbance[i]
            parametre_etalonnage = feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('valeur', flat=True)
            try:
                os.makedirs(path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            nom_fig = path+"\\"+feuille_calcul[0].type_analyse.nom+".png"
            static_name_fig=static_name_fig+"/"+ feuille_calcul[0].type_analyse.nom+".png"
            # regression linéaire
            x = np.array(array_concentration)
            A = np.vstack([x, np.ones(len(x))]).T
            y = np.array(array_absorbance)
            m, c = np.linalg.lstsq(A, y, rcond=None)[0]
            # coeeficient de corrélation
            cor = np.corrcoef(x, y)[-1, 0]
            plt.plot(x, y, 'kD', label='Observations', markersize=7)
            plt.plot(x, m * x + c, 'b', label='regression line')
            plt.xlabel(parametre_etalonnage[0])
            plt.ylabel(parametre_etalonnage[1])
            info = "Y= " + str(round(m, 4)) + "x"
            if c > 0:
                info = info + "+" + str(round(c, 4)) + "\n" + "R²= " + str(round(pow(cor, 2), 4))
            else:
                info = info +" "+ str(round(c, 4)) + "\n" + "R²= " + str(round(pow(cor, 2), 4))
            plt.suptitle(info, fontsize=12)
            plt.legend()
            plt.savefig(nom_fig)
            #on efface le graphe pour ne pas réécrire dessus
            plt.clf()

        analyseFormset = modelformset_factory(Analyse,
                                              fields=param_interne_analyse,
                                              max_num=nb_echantillon,
                                              min_num=nb_echantillon,
                                              widgets=
                                                {
                                                    'nEchantillon': forms.TextInput(attrs={'readonly': True}),
                                                    'var5_kmno4': forms.TextInput(attrs={'readonly': True}),
                                                    'var3_siccite':forms.TextInput(attrs={'readonly': True}),
                                                    'var6_siccite': forms.TextInput(attrs={'readonly': True}),
                                                    'var7_siccite':forms.TextInput(attrs={'readonly': True}),
                                                    'var8_siccite': forms.TextInput(attrs={'readonly': True}),
                                                    'var6_mvs' : forms.TextInput(attrs={'readonly': True}),
                                                    'var7_mvs': forms.TextInput(attrs={'readonly': True}),
                                                    'var8_mvs': forms.TextInput(attrs={'readonly': True}),
                                                    'var9_mvs': forms.TextInput(attrs={'readonly': True}),
                                                    'var4_mest': forms.TextInput(attrs={'readonly': True}),
                                                    'var4_dco' : forms.TextInput(attrs={'readonly': True}),
                                                    'var6_ntk' : forms.TextInput(attrs={'readonly': True}),
                                                    'var5_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True}),
                                                    'var6_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True}),
                                                    'var7_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True}),
                                                    'var8_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True}),
                                                    'var11_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True}),
                                                    'var12_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True}),
                                                    'var13_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True}),
                                                    'var14_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True}),
                                                    'var15_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True}),
                                                    'var16_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True}),
                                                    'var17_dbo_avec_dilution': forms.TextInput(attrs={'readonly': True}),
                                                    'var3_dbo_sans_dilution': forms.TextInput(attrs={'readonly': True}),
                                                    'var6_dbo_sans_dilution': forms.TextInput(attrs={'readonly': True}),
                                                    'var7_dbo_sans_dilution': forms.TextInput(attrs={'readonly': True}),
                                                    'var9_dbo_sans_dilution': forms.TextInput(attrs={'readonly': True}),
                                                    'var10_dbo_sans_dilution': forms.TextInput(attrs={'readonly': True}),
                                                    'var3_silicate': forms.TextInput(attrs={'readonly': True}),
                                                    'var4_oxygene_dissous': forms.TextInput(attrs={'readonly': True}),
                                                    'var10_chlorophylle_scor_unesco': forms.TextInput(attrs={'readonly': True}),
                                                    'var11_chlorophylle_scor_unesco': forms.TextInput(attrs={'readonly': True}),
                                                    'var4_sabm':forms.TextInput(attrs={'readonly': True}),
                                                    'var5_residu_sec':forms.TextInput(attrs={'readonly': True}),
                                                    'var6_residu_sec': forms.TextInput(attrs={'readonly': True}),
                                                    'var3_silice_ifremer': forms.TextInput(attrs={'readonly': True}),
                                                    'var3_silice': forms.TextInput(attrs={'readonly': True}),
                                                    'var8_chlorophylle_lorenzen': forms.TextInput(attrs={'readonly': True}),
                                                    'var9_chlorophylle_lorenzen': forms.TextInput(attrs={'readonly': True}),
                                                    'var10_chlorophylle_lorenzen': forms.TextInput(attrs={'readonly': True}),
                                                    'var11_chlorophylle_lorenzen': forms.TextInput(attrs={'readonly': True}),

                                                })


        #If you want to return a formset that doesn’t include any pre-existing instances of the model, you can specify an empty QuerySet thanks to queryset=Analyse.objects.none()
        formset = analyseFormset(initial=[{'nEchantillon': x} for x in num_echantillon2],queryset=Analyse.objects.none())

        if request.method == 'POST':
            formset = analyseFormset(request.POST, request.FILES)
            if formset.is_valid():
                    for form in formset:
                        numero = form.cleaned_data.get('nEchantillon')
                        analyse=form.save(commit=False)
                        if numero:
                            echantillon= Echantillon.objects.filter(numero=numero)
                            analyse.echantillon= echantillon[0]
                            analyse.feuille_calcul= feuille_calcul[0]
                            analyse.save()
                    return redirect(export_analyse,id_feuille_calcul=request.session['feuille_calcul_id'])

            else:
                error = True
                return render(request, 'myapp/feuille_calcul.html',
                              {'formset': formset, 'nb_echantillon': nb_echantillon,
                               'parametre_interne': param_interne_analyse, 'choix': choix,
                               'feuille_calcul': feuille_calcul[0], 'array_concentration': array_concentration,
                               'array_absorbance': array_absorbance,
                               'static_name_fig': static_name_fig,
                               'parametre_etalonnage': parametre_etalonnage,
                               'concentration_and_absorbance': concentration_and_absorbance,
                               'error': error
                               })

        return render(request,'myapp/feuille_calcul.html',{'formset': formset,'nb_echantillon':nb_echantillon,
                                                           'parametre_interne':param_interne_analyse,'choix': choix,
                                                           'feuille_calcul':feuille_calcul[0],'array_concentration':array_concentration,
                                                           'array_absorbance':array_absorbance,
                                                           'static_name_fig':static_name_fig,
                                                           'parametre_etalonnage':parametre_etalonnage,
                                                           'concentration_and_absorbance':concentration_and_absorbance,
                                                           'error':error
                                                           })


def export_analyse(request,id_feuille_calcul):

    if request.method == 'POST':
        feuille_calcul = Feuille_calcul.objects.filter(id=id_feuille_calcul)
        profil=feuille_calcul[0].feuille_paillasse.profil
        param_externe_analyse = feuille_calcul[0].type_analyse.parametre_externe.all().values_list('nom', flat=True)
        liste_param_externe = feuille_calcul[0].type_analyse.parametre_externe.all().values_list('valeur', flat=True)
        feuille_calcul_trie = Feuille_calcul.objects.filter(id=id_feuille_calcul).values_list(
            *param_externe_analyse)
        feuille_calcul_trie = feuille_calcul_trie[0]

        filename=profil.user.username+"_"+feuille_calcul[0].feuille_paillasse.numero_paillasse+"_"+feuille_calcul[0].type_analyse.nom
        dico = {}
        entete_data_externe= []
        parametre_etalonnage=""
        concentration_and_absorbance = {}
        info_data_extern_pdf=[]
        codification={
                    "kmno4": "ETE8/01-C",
                    "siccite": "DE/TE8/Ceau 49",
                    "mest": "ETE8/05-C",
                    "dco": "ETE8/09-C",
                    "ntk": "ETE8/10-C",
                    "residu sec": "ETE8/69-C",
                    "chlorophylle lorenzen": "ETE8/42-C",
                    "dbo avec dilution": "ETE8/13-C",
                    "dbo sans dilution": "ETE8/14-C",
                    "chlorophylle scor unesco": "ETE8/42-C",
                    "oxygene dissous": "ETE8/38-C",
                    "sabm": "ETE8/56-C",
                    "silicate":"ETE8/16-C",
                    "silice":"ETE8/70-C",
                    "mvs":"DE/TE08/Ceau/91"
        }
        # On veut obtenir le vrais nom des paramètre tel que renseigné sur une feuille de calcul classique pour les entêtes dans le tableau
        liste_param_interne = feuille_calcul[0].type_analyse.parametre_interne.all().values_list('valeur', flat=True)
        # On récupère le nom des variable du type d'analyse les nom sont tel que var1_dco, etc car ce son ces noms la qu'on retrouve dans l'entité feuille de calcul
        param_interne_analyse = feuille_calcul[0].type_analyse.parametre_interne.all().values_list('nom',flat=True)
        # l'opérateur * permet à la fonction values_list d'interpréter un array
        liste_analyses = Analyse.objects.filter(feuille_calcul=feuille_calcul[0]).values_list(*param_interne_analyse)
        for cpt in range(len(param_externe_analyse)):
            dico[param_externe_analyse[cpt]] = feuille_calcul_trie[cpt]
            entete_data_externe.append(liste_param_externe[cpt])
            info_data_extern_pdf.append([liste_param_externe[cpt],feuille_calcul_trie[cpt]])
        dico["N° feuille paillasse"]=feuille_calcul[0].feuille_paillasse.numero_paillasse
        dico["Analyse réalisé par"]=profil.user.first_name+" "+profil.user.last_name
        entete_data_externe.extend(("N° feuille paillasse","Analyse réalisé par"))
        info_data_extern_pdf.extend((["N° feuille paillasse",feuille_calcul[0].feuille_paillasse.numero_paillasse],["Analyse réalisé par",profil.user.first_name+" "+profil.user.last_name]))
        nested = []
        #array d'array composé de couple de deux array
        for x in range(0,len(info_data_extern_pdf) -1,2):
            nested.append(info_data_extern_pdf[x:x + 2])

        path = ""
        if feuille_calcul[0].type_analyse.nom in ["sabm","silice","silice ifremer","silicate"]:
            path = os.path.abspath(os.path.dirname(__file__)) + "\static\myapp\\"+profil.user.username+"\\"+feuille_calcul[0].type_analyse.nom+".png"
            parametre_etalonnage = feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('valeur', flat=True)
            parametre_etalonnage_nom = feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('nom',flat=True)
            les_etalonnages=Etalonnage.objects.filter(profil=profil,type_analyse=feuille_calcul[0].type_analyse).values_list(*parametre_etalonnage_nom)[::-1]
            for etalonnage in les_etalonnages:
                concentration_and_absorbance[etalonnage[0]] = etalonnage[1]


        if 'XLS' in request.POST:
            response = HttpResponse(content_type='application/ms-excel')
            response['Content-Disposition'] = 'attachment; filename="'+filename +'.xls"'
            wb = xlwt.Workbook(encoding='utf-8')
            ws = wb.add_sheet('Analyse')
            row_num = 0

            # Sheet body, remaining rows
            col_width = 256 * 30
            ws.col(2).width = col_width
            ws.col(3).width = col_width
            ws.col(4).width = col_width
            ws.col(5).width = col_width
            ws.col(6).width = col_width
            base_style = xlwt.easyxf("align:wrap on,vert centre,horiz centre;")
            font_style = xlwt.easyxf("align:wrap on,vert centre,horiz centre;border: left thin,right thin,top thin,bottom thin")
            gras_base = xlwt.easyxf("align:wrap on,vert centre,horiz centre ;font: bold on;")
            gras = xlwt.easyxf("align:wrap on,vert centre,horiz centre ;font: bold on;border: left thin,right thin,top thin,bottom thin")
            date_format=xlwt.easyxf('align: wrap yes,vert centre,horiz centre;', num_format_str='DD/MM/YY')
            time_format =xlwt.easyxf('align: wrap yes,vert centre,horiz centre;', num_format_str='hh:mm')

            tab_date=['date_analyse','date_etalonnage','var4_mest','var1_ntk','var1_dbo_avec_dilution','var1_dbo_sans_dilution','var3_chlorophylle_lorenzen','var1_dco','var2_dco']
            cpt=0
            num_col=2

            ws.write(row_num,3,"Feuille de calcul "+feuille_calcul[0].type_analyse.nom,gras_base)
            ws.write(row_num,5,"Codification: "+codification[feuille_calcul[0].type_analyse.nom],gras_base)
            row_num+=2
            for key,value in dico.items():
                if num_col > 6 :
                    num_col=2
                ws.write(row_num, num_col,entete_data_externe[cpt], gras_base)
                num_col+=1
                if key in tab_date:
                    ws.write(row_num, num_col, value, date_format)
                elif key == "heure_mise_sous_essai":
                    ws.write(row_num, num_col, value, time_format)
                else:
                    ws.write(row_num, num_col,value, base_style)
                num_col+=2
                cpt+=1
                if num_col > 6:
                    row_num += 1

            row_num += 2
            cpt = 0
            for key,value in concentration_and_absorbance.items():
                if cpt==0:
                    ws.write(row_num, 2, parametre_etalonnage[0], gras)
                    ws.write(row_num, 3, parametre_etalonnage[1], gras)
                    row_num+=1
                ws.write(row_num,2,key,gras)
                ws.write(row_num,3,value,font_style)
                row_num+=1
                cpt += 1


            if path != "" :
                img = Image.open(path).convert("RGB")
                path_bmp=path.replace("png","bmp")
                #transforme l'image png en bmp
                img.save(path_bmp)
                ws.insert_bitmap(path_bmp, row_num-cpt-1, 5, scale_x=0.7, scale_y=0.7)
                row_num +=15

            for col_num in range(len(liste_param_interne)):
                ws.write(row_num, col_num+2, liste_param_interne[col_num], gras)


            for row in liste_analyses:
                row_num += 1
                for col_num in range(len(row)):
                    ws.write(row_num, col_num+2, row[col_num], font_style)

            wb.save(response)

            return response

        else:
            # Create a Django response object, and specify content_type as pdf
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="'+filename+'.pdf"'
            # find the template and render it.
            html = render_to_string('myapp/rendu_analyse_pdf.html',
                                    {'data_externe': nested,'param_interne_analyse': liste_param_interne,
                                     'valeur_interne_feuille': liste_analyses,'path': path,
                                     'parametre_etalonnage':parametre_etalonnage,
                                     'concentration_and_absorbance':concentration_and_absorbance,
                                     'nom_analyse':feuille_calcul[0].type_analyse.nom,
                                     'codification':codification[feuille_calcul[0].type_analyse.nom]
                                     })

            # create a pdf
            pisaStatus = pisa.CreatePDF(
                html, dest=response
            )
            # if error then show some funy view
            if pisaStatus.err:
                return HttpResponse('We had some errors <pre>' + html + '</pre>')
            return response
    return render(request, 'myapp/export_data.html', locals())


def fix_etalonnage(request):
    if 'choix' in request.session and 'feuille_calcul_id' in request.session :
        choix= request.session['choix']
        nb_etalonnage=6
        profil=Profil.objects.filter(user=request.user)
        type_analyse = Type_analyse.objects.filter(nom=choix)
        param_etalonnage=type_analyse[0].parametre_etalonnage.all().values_list('nom',flat=True)
        #tableau contenant les parametre de l'étalonnage mais pour le javascript
        param_etalonnage_js=[]
        for param in param_etalonnage:
            param_etalonnage_js.append(param)
        etalonnageFormset= modelformset_factory(Etalonnage,
                                                fields=param_etalonnage,
                                                max_num=nb_etalonnage,
                                                min_num=nb_etalonnage,
                                                widgets=
                                                {
                                                    'c_lauryl': forms.TextInput(attrs={'readonly': True}),
                                                    'c_mg': forms.TextInput(attrs={'readonly': True}),
                                                    'c_micromol_l' : forms.TextInput(attrs={'readonly': True}),
                                                })
        formset = etalonnageFormset(request.POST, request.FILES)
        #la requête dans le queryset permet de créer un ensemble d'étalonnage par profil et analyse
        if choix == "sabm":
            etalonnageFormset = etalonnageFormset(initial=[{'c_lauryl': x} for x in ['0','0.1','0.4','1','2','4']],
                                              queryset=Etalonnage.objects.filter(profil=profil[0],type_analyse=type_analyse[0]))
        elif choix == "silicate":
            etalonnageFormset = etalonnageFormset(initial=[{'c_mg': x} for x in ['0', '0.1', '0.5', '1', '2', '5']],
                                                  queryset=Etalonnage.objects.filter(profil=profil[0],
                                                                                     type_analyse=type_analyse[0]))
        elif choix == "silice":
            etalonnageFormset = etalonnageFormset(initial=[{'c_micromol_l': x} for x in ['0', '0.5', '1', '5', '10', '20']],
                                                  queryset=Etalonnage.objects.filter(profil=profil[0],
                                                                                     type_analyse=type_analyse[0]))
        elif choix == "silice ifremer":
            etalonnageFormset = etalonnageFormset(initial=[{'c_micromol_l': x} for x in ['0', '0.4', '0.5', '1', '5', '10']],
                                                  queryset=Etalonnage.objects.filter(profil=profil[0],
                                                                                     type_analyse=type_analyse[0]))


        if request.method == 'POST':
            if formset.is_valid():
                feuille_calcul = Feuille_calcul.objects.filter(id=request.session['feuille_calcul_id']).update(etalonnage=request.POST['etalonnage'])
                for form in formset:
                    etalonnage = form.save(commit=False)
                    etalonnage.type_analyse = type_analyse[0]
                    etalonnage.profil = profil[0]
                    etalonnage.save()
                return redirect(feuille_calcul_data)

        return render(request,'myapp/fix_etalonnage.html',{'formset':etalonnageFormset,'param_etalonnage':param_etalonnage_js})








