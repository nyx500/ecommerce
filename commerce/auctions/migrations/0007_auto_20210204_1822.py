# Generated by Django 3.1.5 on 2021-02-04 17:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0006_remove_listing_current_price'),
    ]

    operations = [
        migrations.RenameField(
            model_name='listing',
            old_name='starting_bid',
            new_name='starting_price',
        ),
    ]