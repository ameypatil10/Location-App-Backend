# Generated by Django 2.1.3 on 2018-11-25 15:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SpotMe', '0009_auto_20181125_1553'),
    ]

    operations = [
        migrations.AlterField(
            model_name='router_location_data',
            name='signal_strength',
            field=models.IntegerField(),
        ),
    ]
