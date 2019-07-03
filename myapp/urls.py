from django.urls import path
from . import views

urlpatterns=[
    path('',views.connexion,name='myapp_accueil'),
    path('logout/',views.deconnexion,name='myapp_logout'),
    path('import/', views.import_data,name='myapp_import'),
    path('index/feuille_calcul/<slug:username>/', views.index_feuille_calcul, name='myapp_index_feuille_calcul'),
    path('choix/<slug:session_id>/', views.choix_analyse, name='myapp_choix'),
    path('choix_specifique1/<slug:session_id>/', views.choix_specifique1, name='myapp_choix_specifique1'),
    path('choix_specifique2/<slug:session_id>/', views.choix_specifique2, name='myapp_choix_specifique2'),
    path('externe_data/<slug:session_id>/', views.externe_data_feuille_calcul, name='myapp_externe_data'),
    path('feuille_calcul/<slug:session_id>/', views.feuille_calcul_data, name='myapp_calcul'),
    path('feuille_calcul_admin/<int:id_feuille_calcul>/', views.feuille_calcul_admin, name='myapp_feuille_admin'),
    path('export/<int:id_feuille_calcul>/<slug:session_id>/', views.export_analyse, name='export_analyse'),
    path('ajax_add/<slug:session_id>/', views.ajax_echantillon_add, name='myapp_ajax_add'),
    path('ajax_del/<slug:session_id>/', views.ajax_echantillon_del, name='myapp_ajax_del'),
    path('gestion_admin/', views.gestion_admin, name='myapp_gestion'),
    path('etalonnage/<slug:session_id>/',views.fix_etalonnage,name='myapp_etalonnage'),
    path('export_xls/<int:id_feuille_calcul>',views.export_xls, name='myapp_export_xls'),
    path('export_pdf/<int:id_feuille_calcul>',views.export_pdf, name='myapp_export_pdf')

]