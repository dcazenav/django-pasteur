from django.urls import path
from . import views

urlpatterns=[
    path('',views.connexion,name='myapp_accueil'),
    path('logout/',views.deconnexion,name='myapp_logout'),
    path('import/', views.import_data,name='myapp_import'),
    path('choix/', views.choix_analyse, name='myapp_choix'),
    path('feuille_calcul/', views.feuille_calcul_data, name='myapp_calcul'),

]