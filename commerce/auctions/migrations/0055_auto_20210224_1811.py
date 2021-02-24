# Generated by Django 3.1.7 on 2021-02-24 17:11

from django.db import migrations
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0054_listing_increment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='minimum_bid',
            field=djmoney.models.fields.MoneyField(decimal_places=2, default=None, default_currency='USD', max_digits=19, verbose_name='Minimum bid:'),
        ),
    ]
