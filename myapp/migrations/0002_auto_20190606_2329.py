# Generated by Django 2.1.7 on 2019-06-06 23:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analyse',
            name='var10_dbo_sans_dilution',
            field=models.CharField(blank=True, max_length=60, verbose_name='controle'),
        ),
        migrations.AlterField(
            model_name='analyse',
            name='var4_dbo_sans_dilution',
            field=models.CharField(blank=True, max_length=60, verbose_name='mesure2 [O2]t0'),
        ),
        migrations.AlterField(
            model_name='analyse',
            name='var5_dbo_sans_dilution',
            field=models.CharField(blank=True, max_length=60, verbose_name='mesure2 [O2]t5'),
        ),
        migrations.AlterField(
            model_name='analyse',
            name='var6_dbo_sans_dilution',
            field=models.CharField(blank=True, max_length=60, verbose_name='valeur DBO2 mg/L'),
        ),
        migrations.AlterField(
            model_name='analyse',
            name='var7_dbo_sans_dilution',
            field=models.CharField(blank=True, max_length=60, verbose_name='r expérimentale'),
        ),
        migrations.AlterField(
            model_name='analyse',
            name='var8_dbo_sans_dilution',
            field=models.CharField(blank=True, max_length=60, verbose_name='r théorique'),
        ),
        migrations.AlterField(
            model_name='analyse',
            name='var9_dbo_sans_dilution',
            field=models.CharField(blank=True, max_length=60, verbose_name='limite de controle'),
        ),
    ]