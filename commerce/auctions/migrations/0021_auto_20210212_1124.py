# Generated by Django 3.1.5 on 2021-02-12 10:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0020_auto_20210208_1040'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='end_bid_time',
            field=models.DateTimeField(verbose_name='Enter end date and time:'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='seller',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='listings', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='listing',
            name='start_bid_time',
            field=models.DateTimeField(verbose_name='Enter start date and time:'),
        ),
    ]