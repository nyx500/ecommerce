from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
import datetime
import os
from django.utils import timezone
import pytz
from timezone_field import TimeZoneField
from django_countries.fields import CountryField
from django_countries import countries
from djmoney.models.fields import MoneyField
from six import python_2_unicode_compatible

class User(AbstractUser):
    time_created = models.DateTimeField(auto_now_add=True)
    watched_listings = models.ManyToManyField('Listing', blank=True)
    def __str__(self):
        return f"{self.id}: {self.username} created at {self.time_created}"

class Category(models.Model):
    category = models.CharField(max_length=64)
    def __str__(self):
        return f"{self.category}"

class Listing(models.Model):    
    
    def image_path(instance, filename): 
        return os.path.join(settings.MEDIA_ROOT, instance.name)

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings", blank=True, null=True, default=None)
    name = models.CharField(max_length=128, verbose_name="Product name:")
    description = models.CharField(max_length=255, verbose_name="Product description:")

    CONDITION_CHOICES = [
        ("", ("---------")),
        ("Antique", ("Antique")),
        ("Poor", ("Used - in poor condition")),
        ("Okay", ("Used - in okay condition")),
        ("Good", ("Used - in good condition")),
        ("Excellent", ("Used - in excellent condition, like new")),
        ("New", ("New"))
    ]

    condition = models.CharField(max_length=64, verbose_name="Product condition:", choices = CONDITION_CHOICES)
    starting_bid = MoneyField(max_digits=19, decimal_places=2, default_currency='USD', default=00.00, verbose_name="Starting bid:")
    minimum_bid = MoneyField(max_digits=19, decimal_places=2, default_currency='USD', default=00.00, verbose_name="Minimum bid:")
    highest_bid = MoneyField(max_digits=19, decimal_places=2, default_currency='USD', default=None, verbose_name="Highest bid:", blank=True, null=True)
    # Sets the field to NULL if the category gets deleted
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="listings", verbose_name="Product category:")

    # Creates a custom image path for each user via their id. The join function creates a path that links the media folder in the root directory to the user id in that 'instance' (that particular object which is being stored in the view) and saves it as the filename the user has uploaded
    def image_path(instance, filename):
        return os.path.join(settings.MEDIA_ROOT, f"{str(instance.seller.id)}/{filename}")

    image = models.ImageField(upload_to=image_path, verbose_name="Upload image",blank=True, null=True)

    # Creates a list of countries where the product can be sent to
    list_countries = list(countries)
    for index, country in enumerate(list_countries):
        list_countries[index] = country
    list_countries.insert(0, ("Worldwide", "Worldwide"))
    list_countries.insert(0, ("Africa", "Africa"))
    list_countries.insert(0, ("Asia", "Asia"))
    list_countries.insert(0, ("Australia and New Zealand", "Australia & NZ"))
    list_countries.insert(0, ("North America", "North America"))
    list_countries.insert(0, ("South America", "South America"))
    list_countries.insert(0, ("Europe", "Europe"))
    list_countries.insert(0, ("", '---------') )
    COUNTRY_CHOICES = list_countries

    shipping_options = models.CharField(max_length=64, verbose_name="Can ship to:", choices=COUNTRY_CHOICES)
    shipping_cost = MoneyField(max_digits=19, decimal_places=2, default=00.00, default_currency="USD", verbose_name="Shipping cost:")
    location = CountryField(verbose_name="Country the product is being sent from:")
    time_listed = models.DateTimeField(auto_now_add=True)
    start_bid_time = models.DateTimeField(verbose_name="Enter start date and time:")
    end_bid_time = models.DateTimeField(verbose_name="Enter end date and time:"
    )
    time_zone = TimeZoneField(verbose_name="Enter your time zone:")
    bid_active = models.BooleanField(default=False)
    user_closed_bid = models.BooleanField(default=False)

    # Have to create a new function to round currency to the last two decimal points (this is because SQLite does not support DecimalField, therefore the float has to be rounded in a custom function)
    #https://stackoverflow.com/questions/23739030/restrict-django-floatfield-to-2-decimal-places/46081058#46081058
    def save(self, *args, **kwargs):
        self.shipping_cost = round(self.shipping_cost, 2)
        super(Listing, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.id}: {self.name} listed at {self.starting_bid} on date {self.time_listed}"


class Bid(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    amount_bid = MoneyField(max_digits=19, decimal_places=2, default=00.00, default_currency="USD")
    time_bid = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bid {self.id} of {self.amount_bid} on {self.listing.name} by user {self.bidder.username}"

class Comment(models.Model):
    product = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    comment = models.CharField(max_length=768, verbose_name="Leave a comment:")
    time_submitted = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Listing: {self.product.name}\nComment: {self.comment} by {self.user}"


