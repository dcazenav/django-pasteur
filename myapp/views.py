from django.shortcuts import render,redirect
from .forms import ConnexionForm,Feuille_calculForm,AnalyseForm
from django.forms import modelformset_factory,modelform_factory
from django.contrib.auth import authenticate,login,logout
from django import forms
import os.path,errno
import numpy as np
import matplotlib.pyplot as plt
from .utils import *
import xlrd


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
    #Supression des feuilles de calcul vide
    profil = Profil.objects.filter(user=request.user)
    feuille_calcul = Feuille_calcul.objects.filter(profil=profil[0])
    for elmt in feuille_calcul:
        analyses = Analyse.objects.filter(feuille_calcul=elmt)
        if not analyses.exists():
            elmt.delete()

    #Nettoyage de la session
    key_session = ['type_analyses', 'choix', 'type_analyses_echantillon', 'parametres_externe', 'feuille_calcul_id',
                   'les_parametres']
    key_delete = []
    for key in request.session.keys():
        if key in key_session:
            key_delete.append(key)
    for elmnt in key_delete:
        del request.session[elmnt]

    logout(request)
    return redirect(connexion)


def index_feuille_calcul(request):
    #Supression des feuilles de calcul vide et ajout des feuille de calcul contenant de l'information dans un array
    # pour l'afficher à l'utilisateur. Les feuilles de calculs sont spécifiques à l'utilisateur courant.
    profil=Profil.objects.filter(user=request.user)
    feuille_calcul = Feuille_calcul.objects.filter(profil=profil[0])
    array_feuille_calcul=[]

    for elmt in feuille_calcul:
        analyses = Analyse.objects.filter(feuille_calcul=elmt)
        if not analyses.exists():
            elmt.delete()
        else:
            array_feuille_calcul.append(elmt)
    return render(request,'myapp/index_feuille_calcul.html',{'feuille_calcul':array_feuille_calcul})


def import_data(request):


    container_type = []
    dico1 = []
    dico3 = {'oxydab. kmno4 en mil. ac. à chaud': 'kmno4',
             'taux de siccité (%)': 'siccite',
             'matières volatiles sèches': 'matiere seche et mvs',
             'matières en suspension (filtre what': 'MES',
             'dem. chim. en oxygène': 'dco',
             'azote kjeldahl (en n)': 'ntk',
             'silicates solubles (en mg/l de sio2)': 'SIL',
             'oxygène dissous (méthode iodométrique)': 'oxygene dissous',
             'chlorophylle alpha': 'chlorophylle',
             'agents de surface': 'sabm',
             'résidu sec à 180°c': 'residu sec',
             'silicates solubles (µmol/l sio2)': 'SIL-BC',
             'dbo5': 'dbo5'}

    if 'valider' in request.POST:
        #Teste si myfile existe
        myfile = request.FILES["myfile"] if 'myfile' in request.FILES else False

        if myfile!= False:
            if myfile.name.endswith('.TXT'):
                paillasse_data = request.FILES['myfile'].read().decode('cp1252').split("\n")[:-1]

                for line in paillasse_data:
                    ls = line.split(';')
                    tmp = []
                    ls[5] = ls[5].lower()
                    for cle2 in dico3.keys():
                        if cle2 in ls[5]:
                            tmp.extend((ls[1], dico3[cle2]))
                            dico1.append(tmp)
                            if dico3[cle2] not in container_type:
                                container_type.append(dico3[cle2])

            elif myfile.name.endswith('.xls') or myfile.name.endswith('.XLS') :
                unique = []
                workbook = xlrd.open_workbook(file_contents=myfile.read())
                sheet = workbook.sheet_by_index(0)
                index_echantillon = -1
                index_element = -1
                dico2={}
                for i in range(sheet.nrows):
                    data = []
                    row = sheet.row_values(i)
                    add= False
                    for j in range(len(row)):
                        if row[j] == "Echantillon":
                            index_echantillon = j
                        if row[j] == "Nom Elément":
                            index_element = j
                    if index_echantillon != -1 and index_element != -1:
                        type = row[index_element].lower()
                        for cle in dico3.keys():
                            if cle in type:
                                if index_echantillon in dico2:
                                    if cle not in dico2[index_echantillon]:
                                        dico2[index_echantillon] +=[cle]
                                        add = True
                                else:
                                    dico2[index_echantillon] = [cle]

                                if row[index_echantillon] not in unique or add == True :
                                    data.extend(([row[index_echantillon], dico3[cle]]))
                                    dico1.append(data)
                                    if not add:
                                        unique.append(row[index_echantillon])
                                    if dico3[cle] not in container_type:
                                        container_type.append(dico3[cle])

            request.session['type_analyses'] = container_type
            request.session['type_analyses_echantillon'] = dico1
            request.session['type_analyses_echantillon_save'] = dico1
            return redirect(choix_analyse)

    return render(request, 'myapp/import_data.html')


def choix_analyse(request):

    if 'type_analyses' in request.session:
        les_types = request.session['type_analyses']
        if request.method == 'POST':
            choix = request.POST['choix']
            request.session['choix'] = choix
            if choix in ["dbo5","chlorophylle","SIL"]:
                return redirect(choix_specifique2)

            type_analyse = Type_analyse.objects.filter(nom=choix)
            les_parametres = []
            parametres_externe = []
            param_interne_analyse = list(type_analyse[0].parametre_interne.all().values_list('nom', flat=True))
            index_param_interne_analyse = list(type_analyse[0].parametre_interne.all().values_list('rang', flat=True))
            for i in range(len(index_param_interne_analyse)):
                for j in range (len(index_param_interne_analyse)-1):
                    if index_param_interne_analyse[i]<index_param_interne_analyse[j] :
                        tmp1=index_param_interne_analyse[i]
                        tmp2=param_interne_analyse[i]
                        index_param_interne_analyse[i]=index_param_interne_analyse[j]
                        param_interne_analyse[i]=param_interne_analyse[j]
                        index_param_interne_analyse[j]=tmp1
                        param_interne_analyse[j]=tmp2

            param_externe_analyse = type_analyse[0].parametre_externe.all().values_list('nom', flat=True)

            for elmt in param_interne_analyse:
                les_parametres.append(elmt)
            for elmt in param_externe_analyse:
                parametres_externe.append(elmt)
            request.session['les_parametres'] = les_parametres
            request.session['parametres_externe'] = parametres_externe

            return redirect(choix_specifique1)
    else:
        les_types=""

    return render(request,'myapp/choix_analyse.html',{'les_types':les_types})


def choix_specifique1(request):
    if 'choix' in request.session and 'type_analyses_echantillon' in request.session:
        choix = request.session['choix']
        echantillon = request.session['type_analyses_echantillon']
        echantillon_specifique = []
        echantillon_selected_and_analyse=[]

        for elmt in echantillon:
            if choix == elmt[1]:
                echantillon_specifique.append(elmt[0])
        if request.method == 'POST':
            choix_echantillons = request.POST.getlist('checks')
            for elmt in choix_echantillons:
                couple = [elmt, choix]
                echantillon_selected_and_analyse.append(couple)

            request.session['type_analyses_echantillon'] = echantillon_selected_and_analyse
            return redirect(externe_data_feuille_calcul)
        return render(request,'myapp/choix_specifique1.html',{'echantillon': echantillon_specifique})

def choix_specifique2(request):
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
        if choix == "SIL":
            choix_multiple=['SIL 650','SIL 815']
        for elmt in echantillon:
            if choix == elmt[1]:
                echantillon_specifique.append(elmt[0])
        if request.method == 'POST':
            choix_analyse= request.POST['radio_check']
            choix_echantillons = request.POST.getlist('checks')
            for elmt in choix_echantillons:
                couple = [elmt, choix_analyse]
                echantillon_selected_and_analyse.append(couple)

            type_analyse = Type_analyse.objects.filter(nom=choix_analyse)
            param_interne_analyse = list(type_analyse[0].parametre_interne.all().values_list('nom', flat=True))
            index_param_interne_analyse = list(type_analyse[0].parametre_interne.all().values_list('rang', flat=True))

            #Trie des parametres selon leur rang
            for i in range(len(index_param_interne_analyse)):
                for j in range(len(index_param_interne_analyse) - 1):
                    if index_param_interne_analyse[i] < index_param_interne_analyse[j]:
                        tmp1 = index_param_interne_analyse[i]
                        tmp2 = param_interne_analyse[i]
                        index_param_interne_analyse[i] = index_param_interne_analyse[j]
                        param_interne_analyse[i] = param_interne_analyse[j]
                        index_param_interne_analyse[j] = tmp1
                        param_interne_analyse[j] = tmp2

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

        return render(request,'myapp/choix_specifique2.html',{'choix_multiple':choix_multiple,'echantillon': echantillon_specifique})


def externe_data_feuille_calcul(request):
    profil = Profil.objects.filter(user=request.user)
    if 'parametres_externe' in request.session and 'choix' in request.session :
        param_externe_analyse= list(request.session['parametres_externe'])
        choix=request.session['choix']
        #Placement des paramètres qui génère des résultat à la première place
        if choix=="dco":
            for i in range(len(param_externe_analyse)):
                if param_externe_analyse[i] == "var5_dco":
                    k=param_externe_analyse[i]
                    param_externe_analyse[i]=param_externe_analyse[0]
                    param_externe_analyse[0]=k
                if param_externe_analyse[i] == "var7_dco":
                    k = param_externe_analyse[i]
                    param_externe_analyse[i] = param_externe_analyse[1]
                    param_externe_analyse[1] = k
        type_analyse = Type_analyse.objects.filter(nom=choix)
        feuille_calculForm = modelform_factory(Feuille_calcul,
                                               form=Feuille_calculForm,
                                               fields=param_externe_analyse,
                                               )
        last_date_etalonnage=""
        if choix in ['sabm', 'SIL-BC', 'SIL 650', 'SIL 815']:
            last_feuille=Feuille_calcul.objects.filter(profil=profil[0],type_analyse=type_analyse[0])
            if last_feuille.exists():
                last_date_etalonnage=last_feuille[0].date_etalonnage
        if request.method == "POST":
            form = feuille_calculForm(request.POST, request.FILES)
            if form.is_valid():
                feuille_calcul = form.save(commit=False)
                feuille_calcul.profil= profil[0]
                feuille_calcul.type_analyse =type_analyse[0]
                feuille_calcul.save()
                request.session['feuille_calcul_id'] = feuille_calcul.id
                if choix in ['sabm','SIL-BC','SIL 650','SIL 815']:
                    return redirect(fix_etalonnage)
                else:
                    return redirect(feuille_calcul_data)
        else:
            form=feuille_calculForm()
        return render(request, 'myapp/externe_data.html',{'form': form,"date_etalonnage":last_date_etalonnage})


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
        change=""
        if "change" in request.session:
            change=request.session["change"]


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
        elif choix == "MES" :
            for i in range(len(num_echantillon)):
                if i == 0:
                    num_echantillon2.append("CTRL")
                    num_echantillon2.append("BLANC")
                    Echantillon.objects.get_or_create(numero="CTRL")
                    Echantillon.objects.get_or_create(numero="BLANC")
                    nb_echantillon += 2
                num_echantillon2.append(num_echantillon[i])
        elif choix == "dco" or choix == "dbo avec dilution":
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

        elif choix == "SIL-BC" or choix == "SIL 650" or choix == "SIL 815":
            set_etalonnage = Etalonnage.objects.filter(profil=profil[0],
                                                       type_analyse=feuille_calcul[0].type_analyse)[::-1]
            if choix =="SIL-BC":
                for etalonnage in set_etalonnage:
                    array_concentration.append(float((etalonnage.c_micromol_l).replace(',','.')))
                    array_absorbance.append(float((etalonnage.absorbance).replace(',','.')))
            elif choix == "SIL 815":
                for etalonnage in set_etalonnage:
                    array_concentration.append(float((etalonnage.c_micro_gl).replace(',','.')))
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

        #Correspondance des indexes pour qu'à la ligne sélectionner l'ajout ou la suppression se passe bien
        localisation=[-1 for i in range(len(num_echantillon2))]
        cpt1,cpt2=0,0
        while cpt1< len(num_echantillon) and cpt2 <len(num_echantillon2):
            if num_echantillon[cpt1]==num_echantillon2[cpt2]:
                localisation[cpt2]=cpt1
                cpt1+=1
            cpt2+=1
        request.session['localisation'] = localisation
        # création du graphique d'absorbance
        if len(array_concentration) !=0 and len(array_absorbance)!=0:
            for i in range(len(array_concentration)):
                concentration_and_absorbance[array_concentration[i]] = array_absorbance[i]
            parametre_etalonnage = list(feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('valeur', flat=True))
            if parametre_etalonnage[0] == "Absorbance":
                k = parametre_etalonnage[0]
                parametre_etalonnage[0] = parametre_etalonnage[1]
                parametre_etalonnage[1] = k
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
                                              form=AnalyseForm,
                                              fields=param_interne_analyse,
                                              max_num=nb_echantillon,
                                              min_num=nb_echantillon,
                                              )


        #If you want to return a formset that doesn’t include any pre-existing instances of the model, you can specify an empty QuerySet thanks to queryset=Analyse.objects.none()
        formset = analyseFormset(initial=[{'nEchantillon': x} for x in num_echantillon2],queryset=Analyse.objects.none())

        if 'analyse' in request.POST:
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
                               'error': error,
                               'change':change
                               })

        return render(request,'myapp/feuille_calcul.html',{'formset': formset,'nb_echantillon':nb_echantillon,
                                                           'parametre_interne':param_interne_analyse,'choix': choix,
                                                           'feuille_calcul':feuille_calcul[0],'array_concentration':array_concentration,
                                                           'array_absorbance':array_absorbance,
                                                           'static_name_fig':static_name_fig,
                                                           'parametre_etalonnage':parametre_etalonnage,
                                                           'concentration_and_absorbance':concentration_and_absorbance,
                                                           'error':error,
                                                           'change':change
                                                           })


def ajax_echantillon_add(request):
    if request.method == 'POST':
        numero = request.POST['ajax']
        pos= int(request.POST['pos'])
        Echantillon.objects.get_or_create(numero= numero)
        if 'type_analyses_echantillon' in request.session and 'choix' in request.session and 'localisation' in request.session:
            choix=request.session['choix']
            echantillon_and_type =request.session['type_analyses_echantillon']
            localisation=request.session['localisation']
            request.session["change"] = "Faux"
            if localisation[pos] != -1:
                if pos !=300:
                    echantillon_and_type.insert(localisation[pos]+1,[numero,choix])
                else:
                    echantillon_and_type.append([numero, choix])

                request.session["change"]="Vrai"
            request.session['type_analyses_echantillon']= echantillon_and_type
            return HttpResponse('')


def ajax_echantillon_del(request):
    pos = int(request.GET.get('pos', None))
    if 'type_analyses_echantillon' in request.session and 'localisation' in request.session:
        echantillon_and_type = request.session['type_analyses_echantillon']
        localisation = request.session['localisation']
        request.session["change"] = "Faux"
        if pos != -10:
            if localisation[pos] != -1:
                del echantillon_and_type[localisation[pos]]
                request.session["change"] = "Vrai"
                request.session['type_analyses_echantillon']= echantillon_and_type
        return HttpResponse('')


def export_analyse(request,id_feuille_calcul):

    if 'type_analyses_echantillon' in request.session and 'type_analyses_echantillon_save' in request.session:
        request.session['type_analyses_echantillon'] = request.session['type_analyses_echantillon_save']
    if request.method == 'POST':

        if 'XLS' in request.POST:
            return export_xls_f(id_feuille_calcul)
        if 'PDF' in request.POST:
            return export_pdf_f(id_feuille_calcul)
        if 'choix' in request.POST:
            return redirect(choix_analyse)
        if 'import' in request.POST:
            return redirect(import_data)


    return render(request, 'myapp/export_data.html', locals())


def export_xls(request,id_feuille_calcul):
    return export_xls_f(id_feuille_calcul)


def export_pdf(request,id_feuille_calcul):
    return export_pdf_f(id_feuille_calcul)


def fix_etalonnage(request):
    if 'choix' in request.session and 'feuille_calcul_id' in request.session :
        choix= request.session['choix']
        nb_etalonnage=6
        profil=Profil.objects.filter(user=request.user)
        type_analyse = Type_analyse.objects.filter(nom=choix)
        param_etalonnage=list(type_analyse[0].parametre_etalonnage.all().values_list('nom',flat=True))
        if param_etalonnage[0]=="absorbance":
            k=param_etalonnage[0]
            param_etalonnage[0]=param_etalonnage[1]
            param_etalonnage[1]=k
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
                                                    'c_micro_gl': forms.TextInput(attrs={'readonly': True})
                                                })
        formset = etalonnageFormset(request.POST, request.FILES)
        #la requête dans le queryset permet de créer un ensemble d'étalonnage par profil et analyse
        if choix == "sabm":
            etalonnageFormset = etalonnageFormset(initial=[{'c_lauryl': x} for x in ['0','0.1','0.4','1','2','4']],
                                              queryset=Etalonnage.objects.filter(profil=profil[0],type_analyse=type_analyse[0]))
        elif choix == "SIL 650":
            etalonnageFormset = etalonnageFormset(initial=[{'c_mg': x} for x in ['0', '0.1', '0.5', '1', '2', '5']],
                                                  queryset=Etalonnage.objects.filter(profil=profil[0],
                                                                                     type_analyse=type_analyse[0]))
        elif choix == "SIL 815":
            etalonnageFormset = etalonnageFormset(initial=[{'c_micro_gl': x} for x in ['0', '20', '50', '100', '500', '1000']],
                                                  queryset=Etalonnage.objects.filter(profil=profil[0],
                                                                                     type_analyse=type_analyse[0]))
        elif choix == "SIL-BC":
            etalonnageFormset = etalonnageFormset(initial=[{'c_micromol_l': x} for x in ['0', '0.5', '1', '5', '10', '20']],
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




def test(request):
    return render (request,'myapp/test.html')



