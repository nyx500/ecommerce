from .models import *
import datetime
import pytz

# Checks for active listings
def is_active():
    UTC = pytz.utc
    current_time = datetime.datetime.now(UTC)
    for listing in Listing.objects.all():
        if listing.start_bid_time <= current_time and current_time < listing.end_bid_time:
            listing.bid_active = True
        else:
            listing.bid_active = False
        listing.save()

# Checks if newly added listing object is active
def add_active(object, start, end):
    UTC = pytz.utc
    current_time = datetime.datetime.now(UTC)
    if start <= current_time and current_time <= end:
        object.bid_active = True
        object.save()

def when_created(listings):
    UTC = pytz.utc
    for listing in listings:
        listing.time_difference = datetime.datetime.now(UTC) - listing.time_listed
        listing.save()

# Converts user's local time to UTC time
def convert_to_utc(time_zone, time):
    utc_offset = datetime.datetime.now(time_zone).utcoffset()
    converted_time = time - utc_offset
    return converted_time
