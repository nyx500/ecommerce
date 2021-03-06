# Generated by Django 3.1.5 on 2021-02-07 20:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0017_auto_20210207_1850'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='listing',
            name='image_url',
        ),
        migrations.AddField(
            model_name='listing',
            name='time_zone',
            field=models.CharField(default='', max_length=64),
        ),
        migrations.AlterField(
            model_name='listing',
            name='end_bid_time',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='listing',
            name='start_bid_time',
            field=models.DateTimeField(),
        ),
    ]
