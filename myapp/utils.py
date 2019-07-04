from .models import *
import xlwt
from xhtml2pdf import pisa
from PIL import Image
from django.http import HttpResponse
import os.path
from django.template.loader import render_to_string
import numpy as np
import matplotlib.pyplot as plt
import os.path,errno



def Trie(param,index):
    for i in range(len(index)):
        for j in range(len(index) - 1):
            if index[i] < index[j]:
                tmp1 = index[i]
                tmp2 = param[i]
                index[i] = index[j]
                param[i] = param[j]
                index[j] = tmp1
                param[j] = tmp2
    return param


def create_figure(array_concentration,array_absorbance,parametre_etalonnage,path,nom_fig):
    concentration_and_absorbance={}
    for i in range(len(array_concentration)):
        concentration_and_absorbance[array_concentration[i]] = array_absorbance[i]
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    x = np.array(array_concentration)
    A = np.vstack([x, np.ones(len(x))]).T
    y = np.array(array_absorbance)
    m, c = np.linalg.lstsq(A, y, rcond=None)[0]
    # coeficient de corrélation
    cor = np.corrcoef(x, y)[-1, 0]
    plt.plot(x, y, 'kD', label='Observations', markersize=7)
    plt.plot(x, m * x + c, 'b', label='Droite de regression')
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
    return concentration_and_absorbance

def Export_xls_f(id_feuille_calcul):
    feuille_calcul = Feuille_calcul.objects.filter(id=id_feuille_calcul)
    profil=feuille_calcul[0].profil
    param_externe_analyse = list(feuille_calcul[0].type_analyse.parametre_externe.all().values_list('nom', flat=True))
    liste_param_externe = list(feuille_calcul[0].type_analyse.parametre_externe.all().values_list('valeur', flat=True))
    index_param_externe1 =  list(feuille_calcul[0].type_analyse.parametre_externe.all().values_list('rang', flat=True))
    index_param_externe2 =  list(feuille_calcul[0].type_analyse.parametre_externe.all().values_list('rang', flat=True))
    param_externe_analyse= Trie(param_externe_analyse,index_param_externe1)
    liste_param_externe= Trie(liste_param_externe,index_param_externe2)
    feuille_calcul_trie = Feuille_calcul.objects.filter(id=id_feuille_calcul).values_list(
        *param_externe_analyse)
    feuille_calcul_trie = feuille_calcul_trie[0]

    filename=profil.user.first_name+"_"+str(feuille_calcul[0].id)+"_"+str(feuille_calcul[0].date_creation.date())+"_"+feuille_calcul[0].type_analyse.nom
    dico = {}
    entete_data_externe= []
    parametre_etalonnage=""
    nom_fig=""
    array_concentration=[]
    array_absorbance=[]
    concentration_and_absorbance = {}
    codification=feuille_calcul[0].type_analyse.codification
    # On veut obtenir le vrais nom des paramètre tel que renseigné sur une feuille de calcul classique pour les entêtes dans le tableau
    liste_param_interne = list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('valeur', flat=True))
    # On récupère le nom des variable du type d'analyse les nom sont tel que var1_dco, etc car ce son ces noms la qu'on retrouve dans l'entité feuille de calcul
    param_interne_analyse = list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('nom',flat=True))
    index_param_interne_analyse1 = list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('rang', flat=True))
    index_param_interne_analyse2 = list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('rang', flat=True))
    param_interne_analyse= Trie(param_interne_analyse,index_param_interne_analyse1)
    liste_param_interne = Trie(liste_param_interne,index_param_interne_analyse2)
    # l'opérateur * permet à la fonction values_list d'interpréter un array
    liste_analyses = Analyse.objects.filter(feuille_calcul=feuille_calcul[0]).values_list(*param_interne_analyse)[::-1]
    for cpt in range(len(param_externe_analyse)):
        dico[param_externe_analyse[cpt]] = feuille_calcul_trie[cpt]
        entete_data_externe.append(liste_param_externe[cpt])

    if feuille_calcul[0].type_analyse.nom in ["sabm","SIL 650","SIL 815","SIL-BC"]:
        dico["Etalonnage réalisé par"] = profil.user.first_name + " " + profil.user.last_name
        entete_data_externe.append( "Etalonnage réalisé par")

    dico["Analyse réalisé par"] = profil.user.first_name + " " + profil.user.last_name
    entete_data_externe.append( "Analyse réalisé par")

    path = ""
    if feuille_calcul[0].type_analyse.nom in ["sabm","SIL-BC","SIL 650","SIL 815"]:
        path = os.path.abspath(os.path.dirname(__file__)) + "\static\myapp\\"+profil.user.username
        nom_fig = path + "\\" + feuille_calcul[0].type_analyse.nom + ".png"
        parametre_etalonnage = list(feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('valeur', flat=True))
        if parametre_etalonnage[0] == "Absorbance":
            k = parametre_etalonnage[0]
            parametre_etalonnage[0] = parametre_etalonnage[1]
            parametre_etalonnage[1] = k
        parametre_etalonnage_nom = list(feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('nom',flat=True))
        if parametre_etalonnage_nom[0] == "absorbance":
            k = parametre_etalonnage_nom[0]
            parametre_etalonnage_nom[0] = parametre_etalonnage_nom[1]
            parametre_etalonnage_nom[1] = k
        les_etalonnages=Etalonnage.objects.filter(profil=profil,
                                                  type_analyse=feuille_calcul[0].type_analyse,
                                                  date_etalonnage=feuille_calcul[0].date_etalonnage).values_list(*parametre_etalonnage_nom)[::-1]
        for etalonnage in les_etalonnages:
            array_concentration.append(float(etalonnage[0]))
            array_absorbance.append(float(etalonnage[1]))
        concentration_and_absorbance=create_figure(array_concentration,array_absorbance,parametre_etalonnage,path,nom_fig)

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="'+filename +'.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Analyse')
    row_num = 0

    base_style = xlwt.easyxf("align:wrap on,vert centre,horiz centre;")
    font_style = xlwt.easyxf("align:wrap on,vert centre,horiz centre;border: left thin,right thin,top thin,bottom thin")
    gras_base = xlwt.easyxf("align:wrap on,vert centre,horiz centre ;font: bold on;")
    gras = xlwt.easyxf("align:wrap on,vert centre,horiz centre ;font: bold on;border: left thin,right thin,top thin,bottom thin")
    date_format=xlwt.easyxf('align: wrap yes,vert centre,horiz centre;', num_format_str='DD/MM/YY')
    time_format =xlwt.easyxf('align: wrap yes,vert centre,horiz centre;', num_format_str='hh:mm')

    tab_date=['date_analyse','date_etalonnage','var4_mest','var1_ntk','var1_dbo_avec_dilution','var1_dbo_sans_dilution','var3_chlorophylle_lorenzen','var1_dco','var2_dco']
    cpt=0
    num_col=2

    ws.write_merge(row_num,row_num+1,3,6,codification.intitule,gras_base)
    ws.write_merge(row_num,row_num+1,8,9,"Codification: "+codification.code,gras_base)
    ws.write_merge(row_num,row_num+1,11,13, "Date de révision: " + str(codification.date_rev.strftime("%d/%m/%Y")), gras_base)
    ws.write_merge(row_num,row_num+1,15,15,codification.revision, gras_base)
    row_num+=3
    for key,value in dico.items():
        if num_col > 6:
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
        img = Image.open(nom_fig).convert("RGB")
        path_bmp=nom_fig.replace("png","bmp")
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
    row_num += 3
    ws.write_merge(row_num, row_num + 1,6,13,"INSTITUT PASTEUR DE LA GUADELOUPE-LABORATOIRE D'HYGYENE ET DE L'ENVIRONNEMENT", gras_base)
    wb.save(response)

    return response

def Export_pdf_f(id_feuille_calcul):
    feuille_calcul = Feuille_calcul.objects.filter(id=id_feuille_calcul)
    profil = feuille_calcul[0].profil
    param_externe_analyse = list(feuille_calcul[0].type_analyse.parametre_externe.all().values_list('nom', flat=True))
    liste_param_externe = list(feuille_calcul[0].type_analyse.parametre_externe.all().values_list('valeur', flat=True))
    index_param_externe1 =  list(feuille_calcul[0].type_analyse.parametre_externe.all().values_list('rang', flat=True))
    index_param_externe2 =  list(feuille_calcul[0].type_analyse.parametre_externe.all().values_list('rang', flat=True))
    param_externe_analyse= Trie(param_externe_analyse,index_param_externe1)
    liste_param_externe= Trie(liste_param_externe,index_param_externe2)
    feuille_calcul_trie = Feuille_calcul.objects.filter(id=id_feuille_calcul).values_list(
        *param_externe_analyse)
    feuille_calcul_trie = feuille_calcul_trie[0]
    array_concentration=[]
    array_absorbance=[]
    filename = profil.user.first_name+"_"+str(feuille_calcul[0].id)+"_"+str(feuille_calcul[0].date_creation.date())+"_"+feuille_calcul[0].type_analyse.nom
    parametre_etalonnage = ""
    concentration_and_absorbance = {}
    nom_fig=""
    info_data_extern_pdf = []
    extra_data_extern_pdf=[]
    codification =feuille_calcul[0].type_analyse.codification
    # On veut obtenir le vrais nom des paramètre tel que renseigné sur une feuille de calcul classique pour les entêtes dans le tableau
    liste_param_interne = list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('valeur', flat=True))
    # On récupère le nom des variable du type d'analyse les nom sont tel que var1_dco, etc car ce son ces noms la qu'on retrouve dans l'entité feuille de calcul
    param_interne_analyse = list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('nom', flat=True))
    index_param_interne_analyse1 = list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('rang', flat=True))
    index_param_interne_analyse2 = list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('rang', flat=True))
    param_interne_analyse=Trie(param_interne_analyse,index_param_interne_analyse1)
    liste_param_interne = Trie(liste_param_interne,index_param_interne_analyse2)
    # l'opérateur * permet à la fonction values_list d'interpréter un array
    liste_analyses = Analyse.objects.filter(feuille_calcul=feuille_calcul[0]).values_list(*param_interne_analyse)[::-1]
    for cpt in range(len(param_externe_analyse)):
        if liste_param_externe[cpt] in ["Date d'analyse","Heure de mise sous essai"]:
            extra_data_extern_pdf.append([liste_param_externe[cpt], feuille_calcul_trie[cpt]])
        else:
            info_data_extern_pdf.append([liste_param_externe[cpt], feuille_calcul_trie[cpt]])

    if feuille_calcul[0].type_analyse.nom in ["sabm","SIL 650","SIL 815","SIL-BC"]:
        info_data_extern_pdf.append(["Etalonnage réalisé par", profil.user.first_name + " " + profil.user.last_name])

    info_data_extern_pdf.append(["Analyse réalisé par", profil.user.first_name + " " + profil.user.last_name])
    nested = []
    # array d'array composé de couple de deux array
    for x in range(0, len(info_data_extern_pdf), 2):
        if len(info_data_extern_pdf)>1:
            nested.append(info_data_extern_pdf[x:x + 2])
        else:
            nested.append([info_data_extern_pdf[0],""])
    nested2=[]
    if len(extra_data_extern_pdf)>1:
        nested2.append(extra_data_extern_pdf[0:2])
    else:
        nested2.append([extra_data_extern_pdf[0],""])
    path = ""
    if feuille_calcul[0].type_analyse.nom in ["sabm", "SIL-BC", "SIL 650","SIL 815"]:
        path = os.path.abspath(os.path.dirname(__file__)) + "\static\myapp\\" + profil.user.username
        nom_fig = path + "\\" + feuille_calcul[0].type_analyse.nom + ".png"
        parametre_etalonnage = list(feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('valeur',
                                                                                                     flat=True))
        if parametre_etalonnage[0] == "Absorbance":
            k = parametre_etalonnage[0]
            parametre_etalonnage[0] = parametre_etalonnage[1]
            parametre_etalonnage[1] = k
        parametre_etalonnage_nom = list(feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('nom',
                                                                                                         flat=True))
        if parametre_etalonnage_nom[0] == "absorbance":
            k = parametre_etalonnage_nom[0]
            parametre_etalonnage_nom[0] = parametre_etalonnage_nom[1]
            parametre_etalonnage_nom[1] = k
        les_etalonnages = Etalonnage.objects.filter(profil=profil,
                                                    type_analyse=feuille_calcul[0].type_analyse,
                                                    date_etalonnage=feuille_calcul[0].date_etalonnage).values_list(
            *parametre_etalonnage_nom)[::-1]
        for etalonnage in les_etalonnages:
            array_concentration.append(float(etalonnage[0]))
            array_absorbance.append(float(etalonnage[1]))
        concentration_and_absorbance = create_figure(array_concentration,array_absorbance,parametre_etalonnage,path,nom_fig)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="' + filename + '.pdf"'
    # find the template and render it.
    if feuille_calcul[0].type_analyse.nom in ["chlorophylle lorenzen","chlorophylle scor unesco","dbo sans dilution","dbo avec dilution","matiere seche et mvs"]:
        template="myapp/rendu_analyse_pdf_paysage.html"
    else:
        template = "myapp/rendu_analyse_pdf_portrait.html"
    html = render_to_string(template,
                            {'data_externe': nested,"extra_data_externe":nested2 , 'param_interne_analyse': liste_param_interne,
                             'valeur_interne_feuille': liste_analyses, 'path': nom_fig,
                             'parametre_etalonnage': parametre_etalonnage,
                             'concentration_and_absorbance': concentration_and_absorbance,
                             'nom_analyse': feuille_calcul[0].type_analyse.nom,
                             'codification': codification
                             })

    # create a pdf
    pisaStatus = pisa.CreatePDF(
        html, dest=response
    )
    # if error then show some funy view
    if pisaStatus.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

