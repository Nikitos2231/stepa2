# Generated by Django 5.0.2 on 2024-02-22 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='password',
            field=models.CharField(default='', max_length=128, verbose_name='Password'),
        ),
    ]
