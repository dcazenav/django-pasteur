# Generated by Django 2.1.5 on 2019-02-07 15:10

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0030_auto_20190207_1501'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feuille_calcul',
            name='date_analyse',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]