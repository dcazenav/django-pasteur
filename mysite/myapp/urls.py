from django.urls import path
from . import views

urlpatterns=[
    path('',views.connexion,name='myapp_accueil'),
    path('logout/',views.deconnexion,name='myapp_logout'),
    path('import/', views.import_data,name='myapp_import'),
    path('creation_paillasse/', views.creation_paillasse, name='myapp_creation_paillasse'),
    path('choix/', views.choix_analyse, name='myapp_choix'),
    path('externe_data/', views.externe_data_feuille_calcul, name='myapp_externe_data'),
    path('feuille_calcul/', views.feuille_calcul_data, name='myapp_calcul'),
    path('export/xls/<int:id_feuille_calcul>', views.export_analyse_xls, name='export_analyse_xls'),

]