from django.urls import path
from . import views

urlpatterns=[
    path('',views.connexion,name='myapp_accueil'),
    path('logout/',views.deconnexion,name='myapp_logout'),
    path('import/', views.import_data,name='myapp_import'),
    path('index/feuille_calcul', views.index_feuille_calcul, name='myapp_index_feuille_calcul'),
    path('choix/', views.choix_analyse, name='myapp_choix'),
    path('choix_specifique1/', views.choix_specifique1, name='myapp_choix_specifique1'),
    path('choix_specifique2/', views.choix_specifique2, name='myapp_choix_specifique2'),
    path('externe_data/', views.externe_data_feuille_calcul, name='myapp_externe_data'),
    path('feuille_calcul/', views.feuille_calcul_data, name='myapp_calcul'),
    path('export/<int:id_feuille_calcul>', views.export_analyse, name='export_analyse'),
    path('ajax_add/', views.ajax_echantillon_add, name='myapp_ajax_add'),
    path('ajax_del/', views.ajax_echantillon_del, name='myapp_ajax_del'),
    path('test/', views.test, name='myapp_test'),
    path('etalonnage/',views.fix_etalonnage,name='myapp_etalonnage'),
    path('export_xls/<int:id_feuille_calcul>',views.export_xls, name='myapp_export_xls'),
    path('export_pdf/<int:id_feuille_calcul>',views.export_pdf, name='myapp_export_pdf')

]