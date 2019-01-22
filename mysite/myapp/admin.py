from django.contrib import admin

from . import models

admin.site.register(models.Profil)
admin.site.register(models.Feuille_paillasse)
admin.site.register(models.Parametre_interne_analyse)
admin.site.register(models.Parametre_externe_analyse)
admin.site.register(models.Type_analyse)
admin.site.register(models.Analyse)
admin.site.register(models.Feuille_calcul)
admin.site.register(models.Echantillon)





