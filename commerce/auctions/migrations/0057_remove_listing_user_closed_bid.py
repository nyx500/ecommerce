# Generated by Django 3.1.7 on 2021-02-24 18:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0056_auto_20210224_1824'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='listing',
            name='user_closed_bid',
        ),
    ]
