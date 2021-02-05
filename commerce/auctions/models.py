from django.contrib.auth.models import AbstractUser
from django.db import models
import datetime


class User(AbstractUser):
    time_created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.id}: {self.username} created at {self.time_created}"

class Category(models.Model):
    category = models.CharField(max_length=64)
    def __str__(self):
        return f"{self.category}"

class Listing(models.Model):
    name = models.CharField(max_length=128, verbose_name="Product name:")
    description = models.CharField(max_length=255, verbose_name="Describe the product:")
    condition = models.CharField(max_length=64, verbose_name="Describe the condition of the product (whether it is old or new etc.):")
    starting_price = models.FloatField(verbose_name="Starting price (US $):")
    # Sets the field to NULL if the category gets deleted
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="listings", verbose_name="Product category:")
    image = models.ImageField(blank=True, null=True, verbose_name="Upload image")
    image_url = models.URLField(blank=True, null=True, max_length=200, verbose_name="Enter Image Url (i.e. from Google Photos or another image hosting website)")
    shipping_options = models.CharField(max_length=64, verbose_name="Ships to:")
    shipping_cost = models.FloatField(verbose_name="Shipping cost (US $):")
    location = models.CharField(max_length=64, verbose_name="Location the product being sent from:")
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    time_listed = models.DateTimeField(auto_now_add=True)
    start_bid_time = models.DateTimeField(default = datetime.datetime.now(), verbose_name="Set bidding start time:")
    end_date_and_time = datetime.datetime.now() + datetime.timedelta(hours = 24)
    end_bid_time = models.DateTimeField(default = end_date_and_time, verbose_name="Set bidding end time:")
    bid_active = models.BooleanField(default=False)


    # Have to create a new function to make sure float number is rounded to the last two decimal points because SQLite does not support DecimalField
    #https://stackoverflow.com/questions/23739030/restrict-django-floatfield-to-2-decimal-places/46081058#46081058
    def save(self, *args, **kwargs):
        self.starting_bid = round(self.starting_bid, 2)
        self.shipping_cost = round(self.shipping_cost, 2)
        super(Listing, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.id}: {self.name} listed at ${self.starting_bid} on date {self.time_listed}"


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


