# Generated by Django 5.2 on 2025-05-12 19:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CourseEnrollment', '0002_myuser_fullname'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='fullName',
            field=models.CharField(default='', max_length=50),
        ),
    ]
