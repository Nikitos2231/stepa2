# Generated by Django 5.0.2 on 2024-02-22 08:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0005_customer_password2'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='password2',
        ),
    ]
