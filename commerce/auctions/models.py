from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
import datetime
import os
from django.utils import timezone
import pytz
from timezone_field import TimeZoneField

class User(AbstractUser):
    time_created = models.DateTimeField(auto_now_add=True)
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
    description = models.CharField(max_length=255, verbose_name="Describe the product:")
    condition = models.CharField(max_length=64, verbose_name="Describe the condition of the product (whether it is old or new etc.):")
    starting_price = models.FloatField(verbose_name="Starting price (US $):")
    # Sets the field to NULL if the category gets deleted
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="listings", verbose_name="Product category:")

    # Creates a custom image path for each user via their id. The join function creates a path that links the media folder in the root directory to the user id in that 'instance' (that particular object which is being stored in the view) and saves it as the filename the user has uploaded
    def image_path(instance, filename):
        return os.path.join(settings.MEDIA_ROOT, f"{str(instance.seller.id)}/{filename}")

    image = models.ImageField(upload_to=image_path, verbose_name="Upload image",blank=True, null=True)

    shipping_options = models.CharField(max_length=64, verbose_name="Ships to:")
    shipping_cost = models.FloatField(verbose_name="Shipping cost (US $):")
    location = models.CharField(max_length=64, verbose_name="Location the product being sent from:")
    time_listed = models.DateTimeField(auto_now_add=True)
    start_bid_time = models.DateTimeField(verbose_name="Enter start date and time:")
    end_bid_time = models.DateTimeField(verbose_name="Enter end date and time:"
    )
    time_zone = TimeZoneField(verbose_name="Enter your time zone:")
    bid_active = models.BooleanField(default=False)

    # Have to create a new function to round currency to the last two decimal points (this is because SQLite does not support DecimalField, therefore the float has to be rounded in a custom function)
    #https://stackoverflow.com/questions/23739030/restrict-django-floatfield-to-2-decimal-places/46081058#46081058
    def save(self, *args, **kwargs):
        self.starting_bid = round(self.starting_price, 2)
        self.shipping_cost = round(self.shipping_cost, 2)
        super(Listing, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.id}: {self.name} listed at ${self.starting_price} on date {self.time_listed}"


class Bid(models.Model):
    listing_id = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    amount_bid = models.FloatField()
    time_bid = models.DateTimeField(auto_now_add=True)
    def __str___(self):
        return f"{self.id}: Bid on {self.listing_id}.name by {self.bidder.username} at {time_bid}"

class Comment(models.Model):
    product = models.ForeignKey(Listing, on_delete=models.CASCADE)
    comment = models.CharField(max_length=768)
    
    def __str__(self):
        return f"Listing: {self.product.name}\nComment: {self.comment}"


