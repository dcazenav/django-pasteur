from django.db import models
from django.contrib.auth.models import User

class Profil(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,  # La liaison OneToOne vers le modèle User
                            )
    def __str__(self):
        return self.user.username

class Feuille_paillasse(models.Model):
    profil= models.ForeignKey(Profil,on_delete=models.CASCADE)

class Parametre_externe_analyse(models.Model):
    nom = models.CharField(max_length=60)
    def __str__(self):
        return self.nom

class Parametre_interne_analyse(models.Model):
    nom = models.CharField(max_length=60)
    def __str__(self):
        return self.nom

class Type_analyse(models.Model):
    nom = models.CharField(max_length=100,default="NULL")
    parametre_interne=models.ManyToManyField(Parametre_interne_analyse)
    parametre_externe = models.ManyToManyField(Parametre_externe_analyse)
    def __str__(self):
        return self.nom

class Feuille_calcul(models.Model):
    feuille_paillasse= models.ForeignKey(Feuille_paillasse,on_delete=models.CASCADE)
    type_analyse=models.ForeignKey(Type_analyse,on_delete=models.CASCADE)

class Echantillon(models.Model):
    numero = models.CharField(max_length=60)
    def __str__(self):
        return self.numero

class Analyse(models.Model):
    echantillon=models.ForeignKey(Echantillon,on_delete=models.CASCADE)
    feuille_calcul = models.ForeignKey(Feuille_calcul, on_delete=models.CASCADE)
    nEchantillon= models.CharField(max_length=60)
    m1 = models.CharField(max_length=60)
    m2 = models.CharField(max_length=60)
    ma = models.CharField(max_length=60)
    mb = models.CharField(max_length=60)
    mc = models.CharField(max_length=60)
    def __str__(self):
        return self




