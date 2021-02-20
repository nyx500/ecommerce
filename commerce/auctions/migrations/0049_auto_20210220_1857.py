# Generated by Django 3.1.7 on 2021-02-20 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0048_auto_20210220_1435'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='time_submitted',
            field=models.DateTimeField(auto_now_add=True, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='comment',
            name='comment',
            field=models.CharField(max_length=768, verbose_name='Leave a comment:'),
        ),
    ]
