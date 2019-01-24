from django.shortcuts import render,redirect
from .forms import ConnexionForm,ImportForm
from django.forms import modelformset_factory
from django.contrib.auth import authenticate,login,logout
from tkinter.filedialog import askopenfilename
from django.contrib import messages
from django import forms
from .models import *


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
        my_file = request.FILES['file'].read().decode('cp1252').split("\n")[:-1]

        return render(request,'myapp/test.html',{'f': my_file })
    else :
        form=  ImportForm()



    return render(request, 'myapp/import_data.html',{'form': form} )

