# Generated by Django 2.1.5 on 2019-02-12 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0032_auto_20190208_1138'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feuille_calcul',
            name='var1_oxygene_dissous',
            field=models.CharField(default='NULL', max_length=100, verbose_name="Volume thiosulfate versé pour l'étalonnage mL"),
        ),
        migrations.AlterField(
            model_name='feuille_calcul',
            name='var2_oxygene_dissous',
            field=models.CharField(default='NULL', max_length=100, verbose_name='Concentration du thiosulfate de sodium mmol/L'),
        ),
    ]