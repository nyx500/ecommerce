# Generated by Django 3.1.5 on 2021-02-05 17:51

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0008_auto_20210205_1735'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='listings', to='auctions.category', verbose_name='Product category'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='condition',
            field=models.CharField(max_length=64, verbose_name='Describe the condition of the product (whether it is old or new etc.)'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='description',
            field=models.CharField(max_length=255, verbose_name='Describe the product'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='end_bid_time',
            field=models.DateTimeField(default=datetime.datetime(2021, 2, 6, 18, 51, 43, 852463), verbose_name='Set bidding end time'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='', verbose_name='Uplaod image'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='location',
            field=models.CharField(max_length=64, verbose_name='Which location product is being sent from'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='name',
            field=models.CharField(max_length=128, verbose_name='Product name'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='shipping_cost',
            field=models.FloatField(verbose_name='Shipping cost'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='shipping_options',
            field=models.CharField(max_length=64, verbose_name='Where product is shipped to'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='start_bid_time',
            field=models.DateTimeField(default=datetime.datetime(2021, 2, 5, 18, 51, 43, 852463), verbose_name='Set bidding start time'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='starting_price',
            field=models.FloatField(verbose_name='Starting price'),
        ),
    ]
