# Generated by Django 2.1.7 on 2019-03-19 09:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0042_auto_20190313_1015'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='feuille_paillasse',
            name='poste',
        ),
    ]