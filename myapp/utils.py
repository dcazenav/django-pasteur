from .models import *
import xlwt
from xhtml2pdf import pisa
from PIL import Image
from django.http import HttpResponse
import os.path
from django.template.loader import render_to_string


def export_xls_f(id_feuille_calcul):
    feuille_calcul = Feuille_calcul.objects.filter(id=id_feuille_calcul)
    profil=feuille_calcul[0].feuille_paillasse.profil
    param_externe_analyse = feuille_calcul[0].type_analyse.parametre_externe.all().values_list('nom', flat=True)
    liste_param_externe = feuille_calcul[0].type_analyse.parametre_externe.all().values_list('valeur', flat=True)
    feuille_calcul_trie = Feuille_calcul.objects.filter(id=id_feuille_calcul).values_list(
        *param_externe_analyse)
    feuille_calcul_trie = feuille_calcul_trie[0]

    filename=profil.user.first_name+"_"+feuille_calcul[0].feuille_paillasse.numero_paillasse+"_"+feuille_calcul[0].type_analyse.nom
    dico = {}
    entete_data_externe= []
    parametre_etalonnage=""
    concentration_and_absorbance = {}
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
                "matiere seche et mvs":"DE/TE08/Ceau/91"
    }
    # On veut obtenir le vrais nom des paramètre tel que renseigné sur une feuille de calcul classique pour les entêtes dans le tableau
    liste_param_interne = list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('valeur', flat=True))
    # On récupère le nom des variable du type d'analyse les nom sont tel que var1_dco, etc car ce son ces noms la qu'on retrouve dans l'entité feuille de calcul
    param_interne_analyse = list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('nom',flat=True))
    index_param_interne_analyse = list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('rang', flat=True))
    for i in range(len(index_param_interne_analyse)):
        for j in range(len(index_param_interne_analyse) - 1):
            if index_param_interne_analyse[i] < index_param_interne_analyse[j]:
                tmp1 = index_param_interne_analyse[i]
                tmp2 = param_interne_analyse[i]
                tmp3 = liste_param_interne[i]
                index_param_interne_analyse[i] = index_param_interne_analyse[j]
                param_interne_analyse[i] = param_interne_analyse[j]
                liste_param_interne[i] =liste_param_interne[j]
                index_param_interne_analyse[j] = tmp1
                param_interne_analyse[j] = tmp2
                liste_param_interne[j] =tmp3

    # l'opérateur * permet à la fonction values_list d'interpréter un array
    liste_analyses = Analyse.objects.filter(feuille_calcul=feuille_calcul[0]).values_list(*param_interne_analyse)[::-1]
    for cpt in range(len(param_externe_analyse)):
        dico[param_externe_analyse[cpt]] = feuille_calcul_trie[cpt]
        entete_data_externe.append(liste_param_externe[cpt])
    dico["N° feuille paillasse"]=feuille_calcul[0].feuille_paillasse.numero_paillasse
    dico["Analyse réalisé par"]=profil.user.first_name+" "+profil.user.last_name
    entete_data_externe.extend(("N° feuille paillasse","Analyse réalisé par"))
    path = ""
    if feuille_calcul[0].type_analyse.nom in ["sabm","silice","silice ifremer","silicate"]:
        path = os.path.abspath(os.path.dirname(__file__)) + "\static\myapp\\"+profil.user.username+"\\"+feuille_calcul[0].type_analyse.nom+".png"
        parametre_etalonnage = feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('valeur', flat=True)
        parametre_etalonnage_nom = feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('nom',flat=True)
        les_etalonnages=Etalonnage.objects.filter(profil=profil,type_analyse=feuille_calcul[0].type_analyse).values_list(*parametre_etalonnage_nom)[::-1]
        for etalonnage in les_etalonnages:
            concentration_and_absorbance[etalonnage[0]] = etalonnage[1]

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

    ws.write(row_num,3,"Feuille de calcul "+feuille_calcul[0].type_analyse.nom,gras_base)
    ws.write(row_num,5,"Codification: "+codification[feuille_calcul[0].type_analyse.nom],gras_base)
    row_num+=2
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

def export_pdf_f(id_feuille_calcul):
    feuille_calcul = Feuille_calcul.objects.filter(id=id_feuille_calcul)
    profil = feuille_calcul[0].feuille_paillasse.profil
    param_externe_analyse = feuille_calcul[0].type_analyse.parametre_externe.all().values_list('nom', flat=True)
    liste_param_externe = feuille_calcul[0].type_analyse.parametre_externe.all().values_list('valeur', flat=True)
    feuille_calcul_trie = Feuille_calcul.objects.filter(id=id_feuille_calcul).values_list(
        *param_externe_analyse)
    feuille_calcul_trie = feuille_calcul_trie[0]

    filename = profil.user.first_name + "_" + feuille_calcul[0].feuille_paillasse.numero_paillasse + "_" + feuille_calcul[
        0].type_analyse.nom
    entete_data_externe = []
    parametre_etalonnage = ""
    concentration_and_absorbance = {}
    info_data_extern_pdf = []
    codification = {
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
        "silicate": "ETE8/16-C",
        "silice": "ETE8/70-C",
        "matiere seche et mvs": "DE/TE08/Ceau/91"
    }
    # On veut obtenir le vrais nom des paramètre tel que renseigné sur une feuille de calcul classique pour les entêtes dans le tableau
    liste_param_interne = list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('valeur', flat=True))
    # On récupère le nom des variable du type d'analyse les nom sont tel que var1_dco, etc car ce son ces noms la qu'on retrouve dans l'entité feuille de calcul
    param_interne_analyse = list(feuille_calcul[0].type_analyse.parametre_interne.all().values_list('nom', flat=True))
    index_param_interne_analyse = list(
        feuille_calcul[0].type_analyse.parametre_interne.all().values_list('rang', flat=True))
    for i in range(len(index_param_interne_analyse)):
        for j in range(len(index_param_interne_analyse) - 1):
            if index_param_interne_analyse[i] < index_param_interne_analyse[j]:
                tmp1 = index_param_interne_analyse[i]
                tmp2 = param_interne_analyse[i]
                tmp3 = liste_param_interne[i]
                index_param_interne_analyse[i] = index_param_interne_analyse[j]
                param_interne_analyse[i] = param_interne_analyse[j]
                liste_param_interne[i] = liste_param_interne[j]
                index_param_interne_analyse[j] = tmp1
                param_interne_analyse[j] = tmp2
                liste_param_interne[j] = tmp3

    # l'opérateur * permet à la fonction values_list d'interpréter un array
    liste_analyses = Analyse.objects.filter(feuille_calcul=feuille_calcul[0]).values_list(*param_interne_analyse)[::-1]
    for cpt in range(len(param_externe_analyse)):
        entete_data_externe.append(liste_param_externe[cpt])
        info_data_extern_pdf.append([liste_param_externe[cpt], feuille_calcul_trie[cpt]])
    entete_data_externe.extend(("N° feuille paillasse", "Analyse réalisé par"))
    info_data_extern_pdf.extend((["N° feuille paillasse", feuille_calcul[0].feuille_paillasse.numero_paillasse],
                                 ["Analyse réalisé par", profil.user.first_name + " " + profil.user.last_name]))
    nested = []
    # array d'array composé de couple de deux array
    for x in range(0, len(info_data_extern_pdf) - 1, 2):
        nested.append(info_data_extern_pdf[x:x + 2])

    path = ""
    if feuille_calcul[0].type_analyse.nom in ["sabm", "silice", "silice ifremer", "silicate"]:
        path = os.path.abspath(os.path.dirname(__file__)) + "\static\myapp\\" + profil.user.username + "\\" + \
               feuille_calcul[0].type_analyse.nom + ".png"
        parametre_etalonnage = feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('valeur',
                                                                                                     flat=True)
        parametre_etalonnage_nom = feuille_calcul[0].type_analyse.parametre_etalonnage.all().values_list('nom',
                                                                                                         flat=True)
        les_etalonnages = Etalonnage.objects.filter(profil=profil,
                                                    type_analyse=feuille_calcul[0].type_analyse).values_list(
            *parametre_etalonnage_nom)[::-1]
        for etalonnage in les_etalonnages:
            concentration_and_absorbance[etalonnage[0]] = etalonnage[1]

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="' + filename + '.pdf"'
    # find the template and render it.
    html = render_to_string('myapp/rendu_analyse_pdf.html',
                            {'data_externe': nested, 'param_interne_analyse': liste_param_interne,
                             'valeur_interne_feuille': liste_analyses, 'path': path,
                             'parametre_etalonnage': parametre_etalonnage,
                             'concentration_and_absorbance': concentration_and_absorbance,
                             'nom_analyse': feuille_calcul[0].type_analyse.nom,
                             'codification': codification[feuille_calcul[0].type_analyse.nom]
                             })

    # create a pdf
    pisaStatus = pisa.CreatePDF(
        html, dest=response
    )
    # if error then show some funy view
    if pisaStatus.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response