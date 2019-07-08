from django.shortcuts import render,redirect
from .forms import ConnexionForm,Feuille_calculForm,AnalyseForm
from django.forms import modelformset_factory,modelform_factory
from django.contrib.auth import authenticate,login,logout
from django import forms
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
                profil = Profil.objects.filter(user=request.user)
                feuille_calcul = Feuille_calcul.objects.filter(profil=profil[0])
                for elmt in feuille_calcul:
                    analyses = Analyse.objects.filter(feuille_calcul=elmt)
                    if not analyses.exists():
                        elmt.delete()
                return redirect('myapp_import')
            else: # sinon une erreur sera affichée
                error = True
    else:
        form = ConnexionForm()

    return render(request, 'myapp/connexion.html', locals())


def deconnexion(request):
    # Supression des feuilles de calcul vide
    profil = Profil.objects.filter(user=request.user)
    feuille_calcul = Feuille_calcul.objects.filter(profil=profil[0])
    for elmt in feuille_calcul:
        analyses = Analyse.objects.filter(feuille_calcul=elmt)
        if not analyses.exists():
            elmt.delete()

    # Nettoyage de la session
    key_session = ["_auth_user_id","_auth_user_backend","_auth_user_hash"]
    key_delete = []
    for key in request.session.keys():
        if key not in key_session:
            key_delete.append(key)
    for key in key_delete:
        del request.session[key]

    logout(request)
    return redirect(connexion)


def index_feuille_calcul(request,username):
    user=User.objects.filter(username=username)
    profil=Profil.objects.filter(user=user[0])
    feuille_calcul = list(Feuille_calcul.objects.filter(profil=profil[0]).order_by('-date_creation'))
    return render(request,'myapp/index_feuille_calcul.html',{'feuille_calcul':feuille_calcul})


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
             'détergents anioniques':'sabm',
             'résidu sec à 180°c': 'residu sec',
             'silicates solubles (µmol/l sio2)': 'SIL-BC',
             'dbo5': 'dbo5'}
    error1 = False
    error2 = False

    if 'valider' in request.POST:
        session_id = request.POST['session']
        #Teste si myfile existe
        myfile = request.FILES["myfile"] if 'myfile' in request.FILES else False

        if myfile!= False:
            if myfile.name.endswith('.TXT') or myfile.name.endswith('.txt'):
                dico2={}
                paillasse_data = request.FILES['myfile'].read().decode('cp1252').split("\n")[:-1]

                for line in paillasse_data:
                    ls = line.split(';')
                    tmp = []
                    ls[5] = ls[5].lower()
                    for cle2 in dico3.keys():
                        if cle2 in ls[5]:
                            if ls[1] not in dico2:
                                dico2[ls[1]]= [dico3[cle2]]
                                tmp.extend((ls[1], dico3[cle2]))
                                dico1.append(tmp)
                            else:
                                if dico3[cle2] not in dico2[ls[1]]:
                                    dico2[ls[1]] += [dico3[cle2]]
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
                                if row[index_echantillon] in dico2:
                                    if cle not in dico2[row[index_echantillon]]:
                                        dico2[row[index_echantillon]] +=[cle]
                                        add = True
                                else:
                                    dico2[row[index_echantillon]] = [cle]

                                if row[index_echantillon] not in unique or add == True :
                                    data.extend(([row[index_echantillon], dico3[cle]]))
                                    dico1.append(data)
                                    if not add:
                                        unique.append(row[index_echantillon])
                                    if dico3[cle] not in container_type:
                                        container_type.append(dico3[cle])
            else:
                error1= True
                return render(request, 'myapp/import_data.html',locals())

            if len(dico1) == 0:
                error2 = True
                return render(request, 'myapp/import_data.html', locals())
            else:
                request.session['type_analyses_%s' % session_id] = container_type
                request.session['type_analyses_echantillon_%s' % session_id] = dico1
                request.session['type_analyses_echantillon_save_%s' % session_id] = dico1
                return redirect(choix_analyse,session_id=session_id)

    return render(request, 'myapp/import_data.html',locals())


def choix_analyse(request,session_id):
    if not request.user.is_authenticated:
        return redirect(connexion)
    if 'type_analyses_%s' % session_id in request.session:
        les_types = request.session['type_analyses_%s' % session_id]
        if request.method == 'POST':
            choix = request.POST['choix']
            request.session['choix_%s' % session_id] = choix
            if choix in ["dbo5","chlorophylle","SIL"]:
                return redirect(choix_specifique2,session_id=session_id)

            type_analyse = Type_analyse.objects.filter(nom=choix)
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
            for elmt in param_externe_analyse:
                parametres_externe.append(elmt)
            request.session['parametres_externe_%s' % session_id] = parametres_externe

            return redirect(choix_specifique1,session_id=session_id)
    else:
        les_types=""

    return render(request,'myapp/choix_analyse.html',{'les_types':les_types})


def choix_specifique1(request,session_id):
    if not request.user.is_authenticated:
        return redirect(connexion)
    if 'choix_%s' % session_id in request.session and 'type_analyses_echantillon_%s' %session_id in request.session:
        choix = request.session['choix_%s' % session_id]
        echantillon = request.session['type_analyses_echantillon_%s' % session_id]
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

            request.session['type_analyses_echantillon_%s' %session_id] = echantillon_selected_and_analyse
            return redirect(externe_data_feuille_calcul,session_id=session_id)
        return render(request,'myapp/choix_specifique1.html',{'echantillon': echantillon_specifique})


def choix_specifique2(request,session_id):
    if not request.user.is_authenticated:
        return redirect(connexion)
    if 'choix_%s' % session_id in request.session and 'type_analyses_echantillon_%s' % session_id in request.session:
        choix = request.session['choix_%s' % session_id]
        echantillon = request.session['type_analyses_echantillon_%s' % session_id]
        echantillon_specifique=[]
        choix_multiple=[]
        echantillon_selected_and_analyse=[]
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

            param_externe_analyse = type_analyse[0].parametre_externe.all().values_list('nom', flat=True)

            for elmt in param_externe_analyse:
                parametres_externe.append(elmt)

            request.session['parametres_externe_%s' % session_id] = parametres_externe
            request.session['type_analyses_echantillon_%s' % session_id] = echantillon_selected_and_analyse
            request.session['choix_%s' % session_id]=choix_analyse
            return redirect(externe_data_feuille_calcul,session_id=session_id)

        return render(request,'myapp/choix_specifique2.html',{'choix_multiple':choix_multiple,'echantillon': echantillon_specifique})


def externe_data_feuille_calcul(request,session_id):
    if not request.user.is_authenticated:
        return redirect(connexion)
    profil = Profil.objects.filter(user=request.user)
    if 'parametres_externe_%s' % session_id in request.session and 'choix_%s' % session_id in request.session :
        param_externe_analyse= list(request.session['parametres_externe_%s' % session_id])
        choix=request.session['choix_%s' % session_id]
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
                request.session['feuille_calcul_id_%s' % session_id] = feuille_calcul.id
                if choix in ['sabm','SIL-BC','SIL 650','SIL 815']:
                    return redirect(fix_etalonnage,session_id=session_id)
                else:
                    return redirect(feuille_calcul_data,session_id=session_id)
        else:
            form=feuille_calculForm()
        return render(request, 'myapp/externe_data.html',{'form': form,"date_etalonnage":last_date_etalonnage})


def feuille_calcul_data(request,session_id):
    if not request.user.is_authenticated:
        return redirect(connexion)

    num_echantillon=[]
    num_echantillon2=[]
    nb_echantillon=0
    array_concentration=[]
    array_absorbance=[]
    parametre_etalonnage=""
    static_name_fig=""
    concentration_and_absorbance={}
    error = False
    if 'type_analyses_echantillon_%s' % session_id in request.session and 'choix_%s' % session_id in request.session and 'feuille_calcul_id_%s' % session_id in request.session:
        change=""
        if "change_%s" %session_id in request.session:
            change=request.session["change_%s" %session_id]


        type_analyses_echantillon = request.session['type_analyses_echantillon_%s' % session_id]
        choix= request.session['choix_%s' %session_id]
        feuille_calcul = Feuille_calcul.objects.filter(id=request.session['feuille_calcul_id_%s' %session_id])
        param_interne_analyse = list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('nom', flat=True))
        index_param_interne_analyse = list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('rang', flat=True))
        param_interne_analyse= Trie(param_interne_analyse,index_param_interne_analyse)
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
            set_etalonnage= Etalonnage.objects.filter(profil=profil[0],
                                                      type_analyse=feuille_calcul[0].type_analyse,
                                                      date_etalonnage=feuille_calcul[0].date_etalonnage)[::-1]
            for etalonnage in set_etalonnage:
                array_concentration.append(float(etalonnage.c_lauryl))
                array_absorbance.append(float(etalonnage.absorbance))

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
                                                       type_analyse=feuille_calcul[0].type_analyse,
                                                       date_etalonnage=feuille_calcul[0].date_etalonnage)[::-1]
            if choix =="SIL-BC":
                for etalonnage in set_etalonnage:
                    array_concentration.append(float((etalonnage.c_micromol_l)))
                    array_absorbance.append(float((etalonnage.absorbance)))
            elif choix == "SIL 815":
                for etalonnage in set_etalonnage:
                    array_concentration.append(float((etalonnage.c_micro_gl)))
                    array_absorbance.append(float((etalonnage.absorbance)))
            else:
                for etalonnage in set_etalonnage:
                    array_concentration.append(float((etalonnage.c_mg)))
                    array_absorbance.append(float((etalonnage.absorbance)))
                    
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
        request.session['localisation_%s' % session_id] = localisation
        # création du graphique d'absorbance
        if len(array_concentration) !=0 and len(array_absorbance)!=0:
            parametre_etalonnage = list(feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('valeur', flat=True))
            if parametre_etalonnage[0] == "Absorbance":
                k = parametre_etalonnage[0]
                parametre_etalonnage[0] = parametre_etalonnage[1]
                parametre_etalonnage[1] = k
            nom_fig = path+"\\"+feuille_calcul[0].type_analyse.nom+".png"
            static_name_fig=static_name_fig+"/"+ feuille_calcul[0].type_analyse.nom+".png"
            concentration_and_absorbance=create_figure(array_concentration, array_absorbance, parametre_etalonnage, path, nom_fig)

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
                    return redirect(export_analyse,id_feuille_calcul=request.session['feuille_calcul_id_%s' % session_id],session_id=session_id)

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
                               'change':change,
                               'session_id':session_id
                               })

        return render(request,'myapp/feuille_calcul.html',{'formset': formset,'nb_echantillon':nb_echantillon,
                                                           'parametre_interne':param_interne_analyse,'choix': choix,
                                                           'feuille_calcul':feuille_calcul[0],'array_concentration':array_concentration,
                                                           'array_absorbance':array_absorbance,
                                                           'static_name_fig':static_name_fig,
                                                           'parametre_etalonnage':parametre_etalonnage,
                                                           'concentration_and_absorbance':concentration_and_absorbance,
                                                           'error':error,
                                                           'change':change,
                                                           'session_id':session_id
                                                           })


def ajax_echantillon_add(request,session_id):
    if request.method == 'POST':
        numero = request.POST['ajax']
        pos= int(request.POST['pos'])
        Echantillon.objects.get_or_create(numero= numero)
        if 'type_analyses_echantillon_%s' % session_id in request.session and 'choix_%s' % session_id in request.session and 'localisation_%s' %session_id in request.session:
            choix=request.session['choix_%s' % session_id]
            echantillon_and_type =request.session['type_analyses_echantillon_%s' % session_id]
            localisation=request.session['localisation_%s' % session_id]
            request.session["change_%s" % session_id] = "Faux"
            if localisation[pos] != -1:
                if pos !=300:
                    echantillon_and_type.insert(localisation[pos]+1,[numero,choix])
                else:
                    echantillon_and_type.append([numero, choix])

                request.session["change_%s" % session_id]="Vrai"
            request.session['type_analyses_echantillon_%s' % session_id]= echantillon_and_type
            return HttpResponse('')


def ajax_echantillon_del(request,session_id):
    pos = int(request.GET.get('pos', None))
    if 'type_analyses_echantillon_%s' % session_id in request.session and 'localisation_%s' % session_id in request.session:
        echantillon_and_type = request.session['type_analyses_echantillon_%s' % session_id]
        localisation = request.session['localisation_%s' % session_id]
        request.session["change_%s" % session_id] = "Faux"
        if pos != -10:
            if localisation[pos] != -1:
                del echantillon_and_type[localisation[pos]]
                request.session["change_%s" % session_id] = "Vrai"
                request.session['type_analyses_echantillon_%s' % session_id]= echantillon_and_type
        return HttpResponse('')


def export_analyse(request,id_feuille_calcul,session_id):
    if not request.user.is_authenticated:
        return redirect(connexion)
    if request.method == 'POST':

        if 'XLS' in request.POST:
            return Export_xls_f(id_feuille_calcul)
        if 'PDF' in request.POST:
            return Export_pdf_f(id_feuille_calcul)
        if 'choix' in request.POST:
            if 'type_analyses_echantillon_%s' % session_id in request.session and 'type_analyses_echantillon_save_%s' % session_id in request.session:
                request.session['type_analyses_echantillon_%s' % session_id] = request.session[
                    'type_analyses_echantillon_save_%s' % session_id]
            return redirect(choix_analyse,session_id=session_id)
        if 'import' in request.POST:
            return redirect(import_data)

    return render(request, 'myapp/export_data.html', locals())


def export_xls(request,id_feuille_calcul):
    if not request.user.is_authenticated:
        return redirect(connexion)
    return Export_xls_f(id_feuille_calcul)


def export_pdf(request,id_feuille_calcul):
    if not request.user.is_authenticated:
        return redirect(connexion)
    return Export_pdf_f(id_feuille_calcul)


def fix_etalonnage(request,session_id):
    if not request.user.is_authenticated:
        return redirect(connexion)
    if 'choix_%s' % session_id in request.session and 'feuille_calcul_id_%s' % session_id in request.session :
        choix= request.session['choix_%s' % session_id]
        nb_etalonnage=6
        profil=Profil.objects.filter(user=request.user)
        type_analyse = Type_analyse.objects.filter(nom=choix)
        feuille_calcul = Feuille_calcul.objects.filter(id=request.session['feuille_calcul_id_%s' % session_id])
        date_etalonnage=feuille_calcul[0].date_etalonnage
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
                                                  queryset=Etalonnage.objects.filter(profil=profil[0],type_analyse=type_analyse[0],date_etalonnage=feuille_calcul[0].date_etalonnage))
        elif choix == "SIL 650":
            etalonnageFormset = etalonnageFormset(initial=[{'c_mg': x} for x in ['0', '0.1', '0.5', '1', '2', '5']],
                                                  queryset=Etalonnage.objects.filter(profil=profil[0],type_analyse=type_analyse[0],date_etalonnage=feuille_calcul[0].date_etalonnage))
        elif choix == "SIL 815":
            etalonnageFormset = etalonnageFormset(initial=[{'c_micro_gl': x} for x in ['0', '20', '50', '100', '500', '1000']],
                                                  queryset=Etalonnage.objects.filter(profil=profil[0],type_analyse=type_analyse[0],date_etalonnage=feuille_calcul[0].date_etalonnage))
        elif choix == "SIL-BC":
            etalonnageFormset = etalonnageFormset(initial=[{'c_micromol_l': x} for x in ['0', '0.5', '1', '5', '10', '20']],
                                                  queryset=Etalonnage.objects.filter(profil=profil[0],type_analyse=type_analyse[0],date_etalonnage=feuille_calcul[0].date_etalonnage))


        if request.method == 'POST':
            if formset.is_valid():
                feuille_calcul = feuille_calcul.update(etalonnage=request.POST['etalonnage'])
                for form in formset:
                    etalonnage = form.save(commit=False)
                    if etalonnage.c_lauryl != "":
                        etalonnage.c_lauryl = etalonnage.c_lauryl.replace(',','.')
                    elif etalonnage.c_mg != "":
                        etalonnage.c_mg = etalonnage.c_mg.replace(',','.')
                    elif etalonnage.c_micro_gl != "":
                        etalonnage.c_micro_gl = etalonnage.c_micro_gl.replace(',','.')
                    elif etalonnage.c_micromol_l != "":
                        etalonnage.c_micromol_l = etalonnage.c_micromol_l.replace(',','.')

                    etalonnage.type_analyse = type_analyse[0]
                    etalonnage.profil = profil[0]
                    etalonnage.date_etalonnage= date_etalonnage
                    etalonnage.save()
                return redirect(feuille_calcul_data,session_id=session_id)

        return render(request,'myapp/fix_etalonnage.html',{'formset':etalonnageFormset,'param_etalonnage':param_etalonnage_js})


def gestion_admin(request):
    if request.user.is_superuser:
        profil=list(Profil.objects.all())
        return render(request, 'myapp/gestion_admin.html', {'profil': profil})
    else:
        return redirect(connexion)

def feuille_calcul_admin(request,id_feuille_calcul):
    if request.user.is_superuser:
        array_concentration=[]
        array_absorbance=[]
        feuille_calcul=Feuille_calcul.objects.filter(id=id_feuille_calcul)
        analyse=Analyse.objects.filter(feuille_calcul=feuille_calcul[0])
        nb_echantillon= len(analyse)
        parametre_interne=list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('nom', flat=True))
        index_param_interne = list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('rang', flat=True))
        parametre_interne = Trie(parametre_interne, index_param_interne)
        analyseFormset= modelformset_factory(Analyse,form=AnalyseForm,fields=parametre_interne,max_num=nb_echantillon,min_num=nb_echantillon)
        formset= analyseFormset(queryset=Analyse.objects.filter(feuille_calcul=feuille_calcul[0]))
        choix= feuille_calcul[0].type_analyse.nom
        if choix in ["SIL 815","sabm","SIL 650","SIL-BC"]:
            nom_user= feuille_calcul[0].profil.user.username
            path = os.path.abspath(os.path.dirname(__file__)) + "\static\myapp" + "\\" + nom_user
            nom_fig = path + "\\" + feuille_calcul[0].type_analyse.nom + ".png"
            static_name_fig = "myapp/" + nom_user + "/" + feuille_calcul[0].type_analyse.nom + ".png"
            parametre_etalonnage_nom = list(feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('nom',flat=True))
            if parametre_etalonnage_nom[0] == "absorbance":
                k = parametre_etalonnage_nom[0]
                parametre_etalonnage_nom[0] = parametre_etalonnage_nom[1]
                parametre_etalonnage_nom[1] = k

            les_etalonnages = Etalonnage.objects.filter(profil=feuille_calcul[0].profil,
                                                        type_analyse=feuille_calcul[0].type_analyse,
                                                        date_etalonnage=feuille_calcul[0].date_etalonnage).values_list(
                *parametre_etalonnage_nom)[::-1]
            for etalonnage in les_etalonnages:
                array_concentration.append(float(etalonnage[0]))
                array_absorbance.append(float(etalonnage[1]))

            parametre_etalonnage = list(feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('valeur', flat=True))
            if parametre_etalonnage[0] == "Absorbance":
                k = parametre_etalonnage[0]
                parametre_etalonnage[0] = parametre_etalonnage[1]
                parametre_etalonnage[1] = k

            concentration_and_absorbance = create_figure(array_concentration, array_absorbance, parametre_etalonnage, path,
                                                         nom_fig)
        if request.method == 'POST':
            formset = analyseFormset(request.POST, request.FILES)
            if formset.is_valid():
                for form in formset:
                    form.save()
                return redirect(gestion_admin)
    else:
        return redirect(connexion)

    return render(request, 'myapp/feuille_calcul_admin.html',locals())

def test(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="test.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Users')

    # Sheet header, first row
    row_num = 0
    top_row = 0
    bottom_row = 0
    left_column = 1
    right_column = 3
    ws.write_merge(top_row, bottom_row, left_column, right_column, 'Long Cell')
    style = xlwt.XFStyle()
    style.alignment.wrap = 1
    ws.write(2, 2, 'Hello\nWorld', style)
    wb.save(response)
    return response