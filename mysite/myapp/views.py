from django.shortcuts import render,redirect
from .forms import ConnexionForm,ImportForm,Feuille_paillasseForm,Feuille_calculForm
from django.forms import modelformset_factory,modelform_factory
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django import forms
from .models import *
from django.http import HttpResponse
import xlwt
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from datetime import datetime,time



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
        paillasse_data = request.FILES['file'].read().decode('cp1252').split("\n")[:-1]
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
            cle=cle.lower()
            tmp_type = Type_analyse.objects.all().values_list('nom',flat=True)
            for tp in tmp_type:
                if tp in cle:
                    container_type.append(tp)

        request.session['type_analyses'] = container_type
        request.session['type_analyses_echantillon']= dico1

        return redirect(creation_paillasse)

    else:
        form = ImportForm()

    return render(request, 'myapp/import_data.html',{'form': form} )


def creation_paillasse(request):

    form = Feuille_paillasseForm(request.POST)
    profil=Profil.objects.filter(user=request.user)
    if request.method == "POST":
        if form.is_valid():
            paillasse=form.save(commit=False)
            paillasse.profil=profil[0]
            paillasse.save()
            request.session['paillasse_id'] = paillasse.id
            return redirect(choix_analyse)

    return render(request, 'myapp/paillasse.html', {'form': form} )


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
                return redirect(feuille_calcul_data)

        return render(request, 'myapp/externe_data.html',{'form': form})


def feuille_calcul_data(request):

    num_echantillon=[]
    nb_echantillon=0
    if 'type_analyses_echantillon' in request.session and 'les_parametres' in request.session and 'choix' in request.session and 'feuille_calcul_id' in request.session:
        type_analyses_echantillon = request.session['type_analyses_echantillon']
        param_interne_analyse= request.session['les_parametres']
        choix= request.session['choix']
        feuille_calcul = Feuille_calcul.objects.filter(id=request.session['feuille_calcul_id'])

        if choix == "kmno4":
            num_echantillon.insert(0, "resorcinol")
            Echantillon.objects.get_or_create(numero="resorcinol")
            nb_echantillon += 1

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
                                              widgets={'nEchantillon': forms.TextInput(attrs={'readonly': True})}
                                              )
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

        return render(request,'myapp/feuille_calcul.html',{'formset': analyseFormset,'nb_echantillon':nb_echantillon,'parametre_interne':param_interne_analyse,'choix': choix })


def export_analyse(request,id_feuille_calcul):

    if request.method == 'POST':

        if 'XLS' in request.POST:
            response = HttpResponse(content_type='application/ms-excel')
            response['Content-Disposition'] = 'attachment; filename="analyse.xls"'
            wb = xlwt.Workbook(encoding='utf-8')
            ws = wb.add_sheet('Analyse')
            row_num = 0

            gras = xlwt.XFStyle()
            gras.font.bold = True
            # Sheet body, remaining rows
            font_style = xlwt.XFStyle()
            date_format = xlwt.XFStyle()
            date_format.num_format_str = 'DD/MM/YY'
            time_format = xlwt.XFStyle()
            time_format.num_format_str ='hh:mm'

            feuille_calcul = Feuille_calcul.objects.filter(id=id_feuille_calcul)
            param_externe_analyse = feuille_calcul[0].type_analyse.parametre_externe.all().values_list('nom', flat=True)
            feuille_calcul_trie = Feuille_calcul.objects.filter(id=id_feuille_calcul).values_list(
                *param_externe_analyse)
            feuille_calcul_trie = feuille_calcul_trie[0]

            dico2 = {}
            for cpt in range(len(param_externe_analyse)):
                dico2[param_externe_analyse[cpt]] = feuille_calcul_trie[cpt]

            for key,value in dico2.items():
                ws.write(row_num, 0,key, gras)
                if key == "date_analyse":
                    ws.write(row_num, 1, value, date_format)
                elif key == "heure_mise_sous_essai":
                    ws.write(row_num, 1, value, time_format)
                else:
                    ws.write(row_num, 1,value, font_style)
                row_num += 1

            row_num += 2
            #On veut obtenir le vrais nom des paramètre tel que renseigné sur une feuille de calcul classique
            columns = feuille_calcul[0].type_analyse.parametre_interne.all().values_list('valeur', flat=True)

            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num], gras)

            # On trie par nom et ce nom est spécifique au varible présent dans feuille de calcul
            param_interne_analyse = feuille_calcul[0].type_analyse.parametre_interne.all().values_list('nom',
                                                                                                       flat=True)
            # l'opérateur * permet à la fonction values_list d'interpréter un array
            rows = Analyse.objects.filter(feuille_calcul=feuille_calcul[0]).values_list(*param_interne_analyse)
            for row in rows:
                row_num += 1
                for col_num in range(len(row)):
                    ws.write(row_num, col_num, row[col_num], font_style)

            wb.save(response)

            return response

        else:
            # Model data
            feuille_calcul = Feuille_calcul.objects.filter(id=id_feuille_calcul)
            # Entete
            param_externe_analyse = feuille_calcul[0].type_analyse.parametre_externe.all().values_list('nom', flat=True)
            # valeur
            valeur_externe_feuille = Feuille_calcul.objects.filter(id=id_feuille_calcul).values_list(
                *param_externe_analyse)
            feuille=valeur_externe_feuille[0]
            dico1 = {}
            for cpt in range(len(param_externe_analyse)):
                dico1[param_externe_analyse[cpt]] = feuille[cpt]

            # Entete
            param_interne_analyse = feuille_calcul[0].type_analyse.parametre_interne.all().values_list('nom', flat=True)
            # Valeur
            valeur_interne_feuille = Analyse.objects.filter(feuille_calcul=feuille_calcul[0]).values_list(
                *param_interne_analyse)
            fullname_param_interne= feuille_calcul[0].type_analyse.parametre_interne.all().values_list('valeur', flat=True)
            # Create a Django response object, and specify content_type as pdf
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="report.pdf"'
            # find the template and render it.
            html = render_to_string('myapp/rendu_analyse_pdf.html',
                                    {'data_externe': dico1, 'param_interne_analyse': fullname_param_interne,
                                     'valeur_interne_feuille': valeur_interne_feuille})

            # create a pdf
            pisaStatus = pisa.CreatePDF(
                html, dest=response,
            )
            # if error then show some funy view
            if pisaStatus.err:
                return HttpResponse('We had some errors <pre>' + html + '</pre>')
            return response
    return render(request, 'myapp/export_data.html', locals())












