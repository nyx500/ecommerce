from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
import os
from timezone_field import TimeZoneField
from django_countries.fields import CountryField
from django_countries import countries
from djmoney.models.fields import MoneyField
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    time_created = models.DateTimeField(auto_now_add=True)
    watched_listings = models.ManyToManyField('Listing', blank=True)
    def __str__(self):
        return f"ID{self.id}: {self.username} created at {self.time_created}"


class Listing(models.Model):

    CATEGORY_CHOICES = [
        (None, ("---------")),
        ("Antiques", ("Antiques")),
        ("Baby", ("Baby")),
        ("Books", ("Books")),
        ("Business & Industrial", ("Business & Industrial")),
        ("Clothing & Shoes", ("Clothing & Shoes")),
        ("Collectibles", ("Collectibles")),
        ("Consumer Electronics", ("Consumer Electronics")),
        ("Crafts", ("Crafts")),
        ("Dolls & Bears", ("Dolls & Bears")),
        ("Entertainment: Games, Movies, Videos", ("Entertainment: Games, Movies, Videos")),
        ("Home & Garden", ("Home & Garden")),  
        ("Motors", ("Motors")),
        ("Pet Supplies", ("Pet Supplies")),
        ("Sporting Goods", ("Sporting Goods")),
        ("Sporting Memorabilia", ("Sporting Memorabilia")),
        ("Toys & Hobbies", ("Toys & Hobbies"))                    
    ]

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
    starting_bid = models.DecimalField(decimal_places=2, max_digits=30, validators=[MinValueValidator(0)], verbose_name="Starting bid in US $:")
    minimum_bid = models.DecimalField(decimal_places=2, max_digits=30, validators=[MinValueValidator(0)], verbose_name="Minimum bid:", default=None, blank=True, null=True)
    highest_bid = models.DecimalField(decimal_places=2, max_digits=30, validators=[MinValueValidator(0)], verbose_name="Highest bid:", default=None, blank=True, null=True)
    current_bid = models.DecimalField(decimal_places=2, max_digits=30, validators=[MinValueValidator(0)], verbose_name="Current bid:", default=None, blank=True, null=True)
    category = models.CharField(max_length=128, verbose_name="Category:", choices = CATEGORY_CHOICES)
    
    # Creates a custom image path for each user via their id. The join function creates a path that links the media folder in the root directory to the user id in that 'instance' (current object) and saves it as the filename the user has uploaded
    def image_path(instance, filename):
        return os.path.join(settings.MEDIA_ROOT, f"{str(instance.seller.id)}/{filename}")
    image = models.ImageField(upload_to=image_path, verbose_name="Upload image", blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)

    # Creates a list of countries where the product can be sent to
    list_countries = list(countries)
    for index, country in enumerate(list_countries):
        list_countries[index] = country
    list_countries.insert(0, (None, '---------') )
    list_countries.insert(0, ("South America", "South America"))
    list_countries.insert(0, ("North America", "North America"))
    list_countries.insert(0, ("Europe", "Europe"))
    list_countries.insert(0, ("Australia and New Zealand", "Australia & NZ"))
    list_countries.insert(0, ("Asia", "Asia"))
    list_countries.insert(0, ("Africa", "Africa"))
    list_countries.insert(0, (None, '---------') )
    list_countries.insert(0, ("Worldwide", "Worldwide"))

    COUNTRY_CHOICES = list_countries

    location = CountryField(verbose_name="Country the product is being sent from:")
    shipping_options = models.CharField(max_length=64, verbose_name="Ships to:", choices=COUNTRY_CHOICES)
    shipping_cost = models.DecimalField(decimal_places=2, max_digits=30, validators=[MinValueValidator(0)], verbose_name="Shipping cost in US $:")
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
    amount_bid = models.DecimalField(decimal_places=2, max_digits=30, validators=[MinValueValidator(0)], verbose_name="Place bid in US $:")
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


