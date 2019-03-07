from django.shortcuts import render,redirect
from .forms import ConnexionForm,ImportForm,Feuille_calculForm
from django.forms import modelformset_factory,modelform_factory
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
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
    form = ConnexionForm(request.POST)
    if request.user.is_authenticated:
        return redirect(import_data)
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


def index_paillasse(request):

    profil=Profil.objects.filter(user=request.user)
    paillasse = Feuille_paillasse.objects.filter(profil=profil[0])
    return render(request,'myapp/index_paillasse.html', locals())


def view_paillasse(request,id_feuille_paillasse):
    paillasse = Feuille_paillasse.objects.filter(id=id_feuille_paillasse)
    feuille_calcul=Feuille_calcul.objects.filter(feuille_paillasse=paillasse[0])
    return render(request,'myapp/view_paillasse.html', locals())



def import_data(request):
    if request.method == 'POST':
        paillasse_data = request.FILES['file'].read().decode('cp1252').split("\n")[:-1]
        fullname=request.FILES['file'].name
        dico1 = []
        dico2 = {}
        container_type = []
        for line in paillasse_data:
            ls = line.split(';')
            tmp = []
            ls[5]=ls[5].lower()
            tmp.append(ls[1])
            tmp.append(ls[5])
            dico1.append(tmp)
            dico2[ls[5]] = ls[7]
        for cle in dico2.keys():
            cle = cle.lower()
            tmp_type = Type_analyse.objects.all().values_list('nom',flat=True)
            for tp in tmp_type:
                if tp in cle:
                    container_type.append(tp)
        request.session['fullname'] = fullname
        request.session['type_analyses'] = container_type
        request.session['type_analyses_echantillon']= dico1
        return redirect(creation_paillasse)
    else:
        form = ImportForm()

    return render(request, 'myapp/import_data.html',{'form': form})


def creation_paillasse(request):
    if 'fullname' in request.session:
        profil = Profil.objects.filter(user=request.user)
        fullname=request.session['fullname']
        les_postes=["CHIM1","IKMNO4","SABM","SILICE","OXYGENE"]
        if request.method == "POST":
            poste=request.POST['poste']
            paillasse, created = Feuille_paillasse.objects.get_or_create(profil=profil[0], numero_paillasse=fullname,poste=poste)
            request.session['paillasse_id'] = paillasse.id
            return redirect(choix_analyse)

        return render(request, 'myapp/paillasse.html',{'les_postes':les_postes})

def choix_analyse(request):

    if 'type_analyses' in request.session:
        les_types = request.session['type_analyses']
        if request.method == 'POST':
            choix=request.POST['choix']
            type_analyse = Type_analyse.objects.filter(nom=choix)
            les_parametres=[]
            parametres_externe=[]
            param_interne_analyse = type_analyse[0].parametre_interne.all().values_list('nom', flat=True)
            param_externe_analyse = type_analyse[0].parametre_externe.all().values_list('nom', flat=True)

            for elmt in param_interne_analyse:
                les_parametres.append(elmt)
            for elmt in param_externe_analyse:
                parametres_externe.append(elmt)
            request.session['les_parametres'] = les_parametres
            request.session['parametres_externe'] = parametres_externe
            request.session['choix'] = choix


            return redirect(externe_data_feuille_calcul)
    else:
        les_types=""

    return render(request,'myapp/choix_analyse.html',{'les_types':les_types})



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

        return render(request, 'myapp/externe_data.html',{'form': form})


def feuille_calcul_data(request):

    num_echantillon=[]
    nb_echantillon=0
    array_concentration=[]
    array_absorbance=[]
    parametre_etalonnage=""
    concentration_and_absorbance = {}
    static_name_fig=""
    if 'type_analyses_echantillon' in request.session and 'les_parametres' in request.session and 'choix' in request.session and 'feuille_calcul_id' in request.session:
        type_analyses_echantillon = request.session['type_analyses_echantillon']
        param_interne_analyse= request.session['les_parametres']
        choix= request.session['choix']
        feuille_calcul = Feuille_calcul.objects.filter(id=request.session['feuille_calcul_id'])
        profil = Profil.objects.filter(user=request.user)
        nom_user= request.user.username
        path = os.path.abspath(os.path.dirname(__file__)) + "\static\myapp"+"\\"+nom_user
        static_name_fig="myapp/"+nom_user
        if choix == "kmno4":
            num_echantillon.insert(0, "resorcinol")
            Echantillon.objects.get_or_create(numero="resorcinol")
            nb_echantillon += 1

        if choix == "sabm":
            set_etalonnage= Etalonnage.objects.filter(profil=profil[0],type_analyse=feuille_calcul[0].type_analyse)
            for etalonnage in set_etalonnage:
                array_concentration.append(float((etalonnage.c_lauryl).replace(',','.')))
                array_absorbance.append(float((etalonnage.absorbance).replace(',','.')))

        if choix == "silice":
            set_etalonnage= Etalonnage.objects.filter(profil=profil[0],type_analyse=feuille_calcul[0].type_analyse)
            for etalonnage in set_etalonnage:
                array_concentration.append(float((etalonnage.c_micromol_l).replace(',','.')))
                array_absorbance.append(float((etalonnage.absorbance).replace(',','.')))

        if choix == "silice ifremer":
            set_etalonnage= Etalonnage.objects.filter(profil=profil[0],type_analyse=feuille_calcul[0].type_analyse)
            for etalonnage in set_etalonnage:
                array_concentration.append(float((etalonnage.c_micromol_l).replace(',','.')))
                array_absorbance.append(float(etalonnage.absorbance))
        if choix == "silicate":
            set_etalonnage= Etalonnage.objects.filter(profil=profil[0],type_analyse=feuille_calcul[0].type_analyse)
            for etalonnage in set_etalonnage:
                array_concentration.append(float((etalonnage.c_mg).replace(',','.')))
                array_absorbance.append(float((etalonnage.absorbance).replace(',','.')))
        #création du graphique d'absorbance
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
            #regression linéaire
            x = np.array(array_concentration)
            A = np.vstack([x, np.ones(len(x))]).T
            y = np.array(array_absorbance)
            m, c = np.linalg.lstsq(A, y, rcond=None)[0]
            #coeeficient de corrélation
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




        for nEchantillon in type_analyses_echantillon:
            if choix in nEchantillon[1]:
                num_echantillon.append(nEchantillon[0])
                #Renvoie un tuple (objet, créé) où objet est l’objet chargé ou créé et créé est une valeur booléenne indiquant si un nouvel objet a été créé.
                Echantillon.objects.get_or_create(numero=nEchantillon[0])
                nb_echantillon+=1
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
        formset = analyseFormset(request.POST, request.FILES)


        #If you want to return a formset that doesn’t include any pre-existing instances of the model, you can specify an empty QuerySet thanks to queryset=Analyse.objects.none()
        analyseFormset= analyseFormset(initial=[{'nEchantillon': x} for x in num_echantillon],queryset=Analyse.objects.none())

        if request.method == 'POST':
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
                    messages.error(request, "Formset not Valid")

        return render(request,'myapp/feuille_calcul.html',{'formset': analyseFormset,'nb_echantillon':nb_echantillon,
                                                           'parametre_interne':param_interne_analyse,'choix': choix,
                                                           'feuille_calcul':feuille_calcul[0],'array_concentration':array_concentration,
                                                           'array_absorbance':array_absorbance,
                                                           'static_name_fig':static_name_fig,
                                                           'parametre_etalonnage':parametre_etalonnage,
                                                           'concentration_and_absorbance':concentration_and_absorbance
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
        dico2= {}
        # On veut obtenir le vrais nom des paramètre tel que renseigné sur une feuille de calcul classique pour les entêtes dans le tableau
        liste_param_interne = feuille_calcul[0].type_analyse.parametre_interne.all().values_list('valeur', flat=True)
        # On récupère le nom des variable du type d'analyse les nom sont tel que var1_dco, etc car ce son ces noms la qu'on retrouve dans l'entité feuille de calcul
        param_interne_analyse = feuille_calcul[0].type_analyse.parametre_interne.all().values_list('nom',flat=True)
        parametre_etalonnage=""
        concentration_and_absorbance = {}
        # l'opérateur * permet à la fonction values_list d'interpréter un array
        liste_analyses = Analyse.objects.filter(feuille_calcul=feuille_calcul[0]).values_list(*param_interne_analyse)
        for cpt in range(len(param_externe_analyse)):
            dico[param_externe_analyse[cpt]] = feuille_calcul_trie[cpt]
            dico2[liste_param_externe[cpt]] = feuille_calcul_trie[cpt]
        dico["N° feuille paillasse"]=feuille_calcul[0].feuille_paillasse.numero_paillasse
        dico["Analyse réalisé par"]=profil.user.username
        dico2["N° feuille paillasse"] = feuille_calcul[0].feuille_paillasse.numero_paillasse
        dico2["Analyse réalisé par"] = profil.user.username


        path = ""
        if feuille_calcul[0].type_analyse.nom in ["sabm","silice","silice ifremer","silicate"]:
            path = os.path.abspath(os.path.dirname(__file__)) + "\static\myapp\\"+profil.user.username+"\\"+feuille_calcul[0].type_analyse.nom+".png"
            parametre_etalonnage = feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('valeur', flat=True)
            parametre_etalonnage_nom = feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('nom',flat=True)
            les_etalonnages=Etalonnage.objects.filter(profil=profil,type_analyse=feuille_calcul[0].type_analyse).values_list(*parametre_etalonnage_nom)
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
            font_style =  xlwt.easyxf("align:wrap on,vert centre,horiz centre;border: left thin,right thin,top thin,bottom thin")
            gras_base = xlwt.easyxf("align:wrap on,vert centre,horiz centre ;font: bold on;")
            gras = xlwt.easyxf("align:wrap on,vert centre,horiz centre ;font: bold on;border: left thin,right thin,top thin,bottom thin")
            #date_format = xlwt.XFStyle()
            #date_format.num_format_str = 'DD/MM/YY'
            date_format=xlwt.easyxf('align: wrap yes,vert centre,horiz centre; pattern: pattern solid,fore-colour light_yellow;', num_format_str='DD/MM/YY')
            time_format =xlwt.easyxf('align: wrap yes,vert centre,horiz centre; pattern: pattern solid,fore-colour light_yellow;', num_format_str='hh:mm')
            # xlwt.XFStyle()
            # time_format.num_format_str ='hh:mm'

            tab_date=['date_analyse','date_etalonnage','var4_mest','var1_ntk','var1_dbo_avec_dilution','var1_dbo_sans_dilution','var3_chlorophylle_lorenzen','var1_dco','var2_dco']
            cpt=0
            num_col=2
            for key,value in dico.items():
                #obtenir les bon key dans dico2
                if num_col > 6 :
                    num_col=2
                ws.write(row_num, num_col,list(dico2)[cpt], gras_base)
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
                                    {'data_externe': dico2,'param_externe_analyse':list(dico2), 'param_interne_analyse': liste_param_interne,
                                     'valeur_interne_feuille': liste_analyses,'path': path,
                                     'parametre_etalonnage':parametre_etalonnage,
                                     'concentration_and_absorbance':concentration_and_absorbance
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




def test(request):
    profil=Profil.objects.filter(user=request.user)
    feuille_calcul = Feuille_calcul.objects.filter(id=104)
    concentration_and_absorbance = {}
    parametre_etalonnage_valeur = feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('valeur', flat=True)
    parametre_etalonnage_nom = feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('nom', flat=True)
    les_etalonnages = Etalonnage.objects.filter(profil=profil[0], type_analyse=feuille_calcul[0].type_analyse).values_list(*parametre_etalonnage_nom)
    for etalonnage in les_etalonnages:
        concentration_and_absorbance[etalonnage[0]]=etalonnage[1]
    return render(request,'myapp/test.html',{'les_etalonnages':concentration_and_absorbance})





