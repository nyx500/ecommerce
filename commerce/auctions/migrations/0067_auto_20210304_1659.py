# Generated by Django 3.1.7 on 2021-03-04 15:59

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0066_auto_20210304_1655'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bid',
            name='amount_bid',
            field=models.DecimalField(decimal_places=2, max_digits=30, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Place bid in US $:'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='current_bid',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=30, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Current bid:'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='highest_bid',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=30, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Highest bid:'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='minimum_bid',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=30, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Minimum bid:'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='shipping_cost',
            field=models.DecimalField(decimal_places=2, max_digits=30, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Shipping cost in US $:'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='starting_bid',
            field=models.DecimalField(decimal_places=2, max_digits=30, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Starting bid in US $:'),
        ),
    ]
