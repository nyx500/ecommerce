from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
import os
from timezone_field import TimeZoneField
from django_countries.fields import CountryField
from django_countries import countries
from djmoney.models.fields import MoneyField

class User(AbstractUser):
    time_created = models.DateTimeField(auto_now_add=True)
    watched_listings = models.ManyToManyField('Listing', blank=True)
    def __str__(self):
        return f"ID{self.id}: {self.username} created at {self.time_created}"

class Category(models.Model):
    category = models.CharField(max_length=64)
    def __str__(self):
        return f"{self.category}"

class Listing(models.Model):

    # Creates a set of choices for the condition field
    CONDITION_CHOICES = [
        (None, ("---------")),
        ("Antique", ("Antique")),
        ("Poor", ("Used - in poor condition")),
        ("Okay", ("Used - in okay condition")),
        ("Good", ("Used - in good condition")),
        ("Excellent", ("Used - in excellent condition, like new")),
        ("New", ("New"))
    ]

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    name = models.CharField(max_length=128, verbose_name="Product name:")
    description = models.CharField(max_length=255, verbose_name="Product description:", blank=True, null=True)
    condition = models.CharField(max_length=64, verbose_name="Product condition:", choices = CONDITION_CHOICES)
    starting_bid = MoneyField(max_digits=19, decimal_places=2, default_currency='USD', default=00.00, verbose_name="Starting bid:")
    minimum_bid = MoneyField(max_digits=19, decimal_places=2, default_currency='USD', default=None, verbose_name="Minimum bid:", null=True, blank=True)
    highest_bid = MoneyField(max_digits=19, decimal_places=2, default_currency='USD', default=None, verbose_name="Highest bid:", blank=True, null=True)
    current_bid = MoneyField(max_digits=19, decimal_places=2, default_currency='USD', default=None, verbose_name="Current bid:", blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="listings", verbose_name="Product category:")

    # Creates a custom image path for each user via their id. The join function creates a path that links the media folder in the root directory to the user id in that 'instance' (current object) and saves it as the filename the user has uploaded
    def image_path(instance, filename):
        return os.path.join(settings.MEDIA_ROOT, f"{str(instance.seller.id)}/{filename}")
    image = models.ImageField(upload_to=image_path, verbose_name="Upload image", blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)

    # Creates a list of countries where the product can be sent to
    list_countries = list(countries)
    for index, country in enumerate(list_countries):
        list_countries[index] = country
    list_countries.insert(0, ("Africa", "Africa"))
    list_countries.insert(0, ("Asia", "Asia"))
    list_countries.insert(0, ("Australia and New Zealand", "Australia & NZ"))
    list_countries.insert(0, ("North America", "North America"))
    list_countries.insert(0, ("South America", "South America"))
    list_countries.insert(0, ("Europe", "Europe"))
    list_countries.insert(0, (None, '---------') )
    list_countries.insert(0, ("Worldwide", "Worldwide"))
    list_countries.insert(0, (None, '---------') )
    COUNTRY_CHOICES = list_countries

    location = CountryField(verbose_name="Country the product is being sent from:")
    shipping_options = models.CharField(max_length=64, verbose_name="Ships to:", choices=COUNTRY_CHOICES)
    shipping_cost = MoneyField(max_digits=19, decimal_places=2, default=00.00, default_currency="USD", verbose_name="Shipping cost:")
    time_listed = models.DateTimeField(auto_now_add=True)
    time_difference = models.DurationField(blank=True, null=True)
    start_bid_time = models.DateTimeField(verbose_name="Enter start date and time:")
    end_bid_time = models.DateTimeField(verbose_name="Enter end date and time:"
    )
    time_zone = TimeZoneField(verbose_name="Enter your time zone (required):")
    bid_active = models.BooleanField(default=False)
    increment = models.IntegerField(default=1)
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


