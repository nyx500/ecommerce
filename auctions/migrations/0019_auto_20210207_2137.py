# Generated by Django 3.1.5 on 2021-02-07 20:37

from django.db import migrations
import timezone_field.fields


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0018_auto_20210207_2126'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='time_zone',
            field=timezone_field.fields.TimeZoneField(),
        ),
    ]