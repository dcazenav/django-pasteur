# Generated by Django 2.1.7 on 2019-07-25 15:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0003_auto_20190723_0913'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='feuille_calcul',
            name='visa',
        ),
    ]
