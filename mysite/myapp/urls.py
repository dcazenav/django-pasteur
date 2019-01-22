from django.urls import path
from . import views

urlpatterns=[
    path('',views.connexion,name='myapp_accueil'),
    path('logout/',views.deconnexion,name='myapp_logout'),
    path('test/', views.test_form),
]