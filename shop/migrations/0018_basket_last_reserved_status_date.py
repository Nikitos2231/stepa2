# Generated by Django 5.0.2 on 2024-02-26 17:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0017_basket_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='basket',
            name='last_reserved_status_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Last status date'),
        ),
    ]