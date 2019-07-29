# Generated by Django 2.1.7 on 2019-07-23 09:13

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_table_correspondance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feuille_calcul',
            name='date_analyse',
            field=models.DateField(default=datetime.datetime(1980, 1, 1, 1, 1, 1), verbose_name="Date d'analyse"),
        ),
        migrations.AlterField(
            model_name='feuille_calcul',
            name='heure_mise_sous_essai',
            field=models.TimeField(default=datetime.time(0, 0), verbose_name='Heure de mise sous essai'),
        ),
        migrations.AlterField(
            model_name='feuille_calcul',
            name='longueur_onde',
            field=models.CharField(max_length=100, verbose_name="Longueur d'onde d'analyse"),
        ),
        migrations.AlterField(
            model_name='feuille_calcul',
            name='var1_chlorophylle_lorenzen',
            field=models.CharField(max_length=100, verbose_name="Lot d'acide chlorhydrique utilisé"),
        ),
        migrations.AlterField(
            model_name='feuille_calcul',
            name='var1_dbo_avec_dilution',
            field=models.DateField(default=datetime.datetime(1980, 1, 1, 1, 1, 1), verbose_name="Date de préparation de l'eau de dilution"),
        ),
        migrations.AlterField(
            model_name='feuille_calcul',
            name='var1_dco',
            field=models.DateField(default=datetime.datetime(1980, 1, 1, 1, 1, 1), verbose_name='Date de minéralisation'),
        ),
        migrations.AlterField(
            model_name='feuille_calcul',
            name='var1_mest',
            field=models.CharField(max_length=100, verbose_name='Numéro de lot des filtres'),
        ),
        migrations.AlterField(
            model_name='feuille_calcul',
            name='var2_dco',
            field=models.DateField(default=datetime.datetime(1980, 1, 1, 1, 1, 1), verbose_name='Date de titration'),
        ),
        migrations.AlterField(
            model_name='feuille_calcul',
            name='var3_mest',
            field=models.CharField(max_length=100, verbose_name='Rendement(%)'),
        ),
        migrations.AlterField(
            model_name='feuille_calcul',
            name='var4_mest',
            field=models.DateField(default=datetime.datetime(1980, 1, 1, 1, 1, 1), verbose_name='Date de préparation de la solution de cellulose microcristalline'),
        ),
        migrations.AlterField(
            model_name='feuille_calcul',
            name='var5_dco',
            field=models.CharField(max_length=100, verbose_name='Volume de sulfate versé pour la détermination de sa concentration'),
        ),
        migrations.AlterField(
            model_name='feuille_calcul',
            name='var6_dco',
            field=models.CharField(max_length=100, verbose_name='Valeur de solution de référence C'),
        ),
        migrations.AlterField(
            model_name='feuille_calcul',
            name='var7_dco',
            field=models.CharField(max_length=100, verbose_name='Essaie à blanc V1'),
        ),
        migrations.AlterField(
            model_name='feuille_calcul',
            name='var8_dco',
            field=models.CharField(max_length=100, verbose_name='Lot de sulfate de mercure'),
        ),
        migrations.AlterField(
            model_name='feuille_calcul',
            name='var9_dco',
            field=models.CharField(max_length=100, verbose_name="Lot de sulfate d'argent"),
        ),
    ]