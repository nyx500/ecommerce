# Generated by Django 3.1.5 on 2021-02-05 18:32

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0010_auto_20210205_1930'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='end_bid_time',
            field=models.DateTimeField(default=datetime.datetime(2021, 2, 6, 19, 32, 33, 101410), verbose_name='Set bidding end time'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='image_url',
            field=models.URLField(blank=True, null=True, verbose_name='Enter Image Url (i.e. from Google Photos or another image hosting website)'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='start_bid_time',
            field=models.DateTimeField(default=datetime.datetime(2021, 2, 5, 19, 32, 33, 101410), verbose_name='Set bidding start time'),
        ),
    ]
