# Generated by Django 3.1.7 on 2021-02-28 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0061_listing_image_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='category',
            field=models.CharField(choices=[(None, '---------'), ('Antiques', 'Antiques'), ('Baby', 'Baby'), ('Books', 'Books'), ('Business & Industrial', 'Business & Industrial'), ('Clothing & Shoes', 'Clothing & Shoes'), ('Collectibles', 'Collectibles'), ('Consumer Electronics', 'Consumer Electronics'), ('Crafts', 'Crafts'), ('Dolls & Bears', 'Dolls & Bears'), ('Entertainment: Games, Movies, Videos', 'Entertainment: Games, Movies, Videos'), ('Home & Garden', 'Home & Garden'), ('Motors', 'Motors'), ('Pet Supplies', 'Pet Supplies'), ('Sporting Goods', 'Sporting Goods'), ('Sporting Memorabilia', 'Sporting Memorabilia'), ('Toys & Hobbies', 'Toys & Hobbies')], default=None, max_length=128, verbose_name='Category:'),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='Category',
        ),
    ]