# Generated by Django 3.1.5 on 2021-02-19 17:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0042_auto_20210219_1702'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='user_closed_bid',
            field=models.BooleanField(default=False),
        ),
    ]
