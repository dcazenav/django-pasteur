from django.urls import path
from . import views

urlpatterns=[
    path('',views.connexion,name='myapp_accueil'),
    path('logout/',views.deconnexion,name='myapp_logout'),
    path('import/', views.import_data,name='myapp_import'),
    path('index/paillasse', views.index_paillasse, name='myapp_index_paillasse'),
    path('view/paillasse/<int:id_feuille_paillasse>', views.view_paillasse, name='myapp_view_paillasse'),
    path('choix/', views.choix_analyse, name='myapp_choix'),
    path('choix_specifique/', views.choix_specifique, name='myapp_choix_specifique'),
    path('externe_data/', views.externe_data_feuille_calcul, name='myapp_externe_data'),
    path('feuille_calcul/', views.feuille_calcul_data, name='myapp_calcul'),
    path('export/<int:id_feuille_calcul>', views.export_analyse, name='export_analyse'),
    path('ajax/', views.ajax_echantillon, name='myapp_ajax'),
    path('etalonnage/',views.fix_etalonnage,name='myapp_etalonnage')
]