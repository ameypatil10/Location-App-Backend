# Generated by Django 2.1.3 on 2018-11-25 15:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('SpotMe', '0008_auto_20181125_1243'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='router_location_data',
            unique_together={('location', 'router', 'signal_strength')},
        ),
    ]
