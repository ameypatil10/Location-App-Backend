# Generated by Django 2.1.3 on 2018-11-21 20:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('SpotMe', '0004_attendance_router_router_location_data_router_location_statistic_tracking_data'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='takes',
            unique_together={('student', 'course_session')},
        ),
    ]
