from django.contrib.auth import authenticate, login, logout
from django.contrib.admin import widgets
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Bid, Category, Comment, Listing, User
from django import forms
from django.utils import timezone
import datetime
import pytz
import bootstrap4
from bootstrap_datepicker_plus import DateTimePickerInput
from django_countries import countries
from moneyfield import MoneyField
import djmoney_rates
from djmoney_rates.utils import convert_money
from money.money import Money
from money.currency import Currency
from decimal import Decimal

class DateTimeInput(forms.DateTimeInput):
    input_type = 'datetime'

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount_bid']


class NewListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['name', 'description', 'category', 'condition', 'start_bid_time', 'end_bid_time', 'image', 'starting_bid', 'shipping_cost', 'location', 'time_zone', 'shipping_options']
        # Models do not take datetime formats whereas forms do. Therefore it is crucial to add the exact type of datetime input format to the form, so that it validates correctly. It is important for the input_format (server side validation) to match the widget DateTimePickerInput options in terms of whether you put / or - or : in between variables!!!! Otherwise the fields will not match and the form will not be validated
        start_bid_time = forms.DateTimeField(initial=datetime.datetime.now(),input_formats=['%m/%d/%Y %H:%M:%S'])
        end_bid_time = forms.DateTimeField(initial=(datetime.datetime.now() + datetime.timedelta(days=1)), label="Insert datetime", input_formats=['%m/%d/%Y %H:%M:%S'])
        starting_bid = MoneyField(decimal_places=2, max_digits=19)
        widgets = {
            'description': forms.Textarea(attrs={"rows": 8, "cols": 100}),
            'start_bid_time': DateTimePickerInput(
                options={
                    "format": "MM/DD/YYYY HH:mm:ss"
                }
            ),
            'end_bid_time': DateTimePickerInput(
                options={
                    "format": "MM/DD/YYYY HH:mm:ss"
                }
            )
        }
        
    # Attributed to this tutorial on how to order model fields in Django: https://stackoverflow.com/questions/42811866/how-to-sort-a-choicefield-in-a-modelform
    def __init__(self, *args, **kwargs):
        # The super() function returns a temporary object of the superclass kind (here it is a NewListingForm)
        super(NewListingForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = self.fields['category'].queryset.order_by('category')

def index(request):
    if request.method == "POST":
        form = BidForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data["amount_bid"]
            listing_id = request.POST["listing_id"]
            og_amount = request.POST["og_amount"]
            og_currency = request.POST["og_currency"]
            amount = convert_money(amount.amount, amount.currency, og_currency)
            og_bid = float(Listing.objects.filter(id=listing_id).values_list('starting_bid')[0][0])
            if float(amount.amount) < og_bid:
                message = f"Please match the starting bid of {og_amount} in {og_currency}"
                return render(request, "auctions/index.html", {
                            "listings": Listing.objects.filter(bid_active=True), "form": BidForm(), "message": message
                        })
            else:  
                listing = Listing.objects.get(id=listing_id)
                listing.starting_bid.amount = listing.starting_bid.amount * Decimal(1.25)
                listing.save()
                bids = Listing.objects.get(id=listing_id).bids.all()
                if bids is None:
                    b = Bid(bidder=request.user, listing=Listing.objects.get(id=listing_id), amount_bid=amount)
                    b.save()
                    listing = Listing.objects.get(id=listing_id)
                    listing.highest_bid = amount
                    listing.save()
                    return render(request, "auctions/index.html", {
                        "listings": Listing.objects.filter(bid_active=True), "form": BidForm(),
                        "message":"Thank you for your bid!"
                    })
                else:
                    for bid in bids:
                        if bid.amount_bid.amount > amount.amount:
                            obj = Bid()
                            obj.listing = listing
                            obj.bidder = bid.bidder
                            obj.amount_bid = listing.starting_bid
                            obj.save()
                            return render(request, "auctions/index.html", {
                                "listings": Listing.objects.filter(bid_active=True), "form": BidForm(), "message": f"Unfortunately, {bid.bidder} has already bid higher than you with a {bid.amount_bid} amount!"
                            })  
                    return render(request, "auctions/index.html", {
                        "listings": Listing.objects.filter(bid_active=True), "form": BidForm(),
                        "message":"Thank you for your bid!"
                    })
        else:
            return render(request, "auctions/index.html", {
                "listings": Listing.objects.filter(bid_active=True), "form": BidForm(), "message": "Invalid form"
            })
    else:
        UTC = pytz.utc
        current_time = datetime.datetime.now(UTC)
        for listing in Listing.objects.all():
            # Turns current UTC time into the current time in the timezone of the user who created that listing by adding the utcoffset between UTC and that user's timezone to the current UTC time
            if listing.start_bid_time <= current_time and current_time <= listing.end_bid_time:
                listing.bid_active = True
            else:
                listing.bid_active = False
            bids = listing.bids.all().order_by('amount_bid')
            listing.highest_bid = bids[0].amount_bid
            listing.save()
        return render(request, "auctions/index.html", {
            "listings": Listing.objects.filter(bid_active=True), "form": BidForm()
        })

def create_listing(request):
    if request.method == "POST":
        form = NewListingForm(request.POST, request.FILES)
        # Server-side check validating the form
        if form.is_valid():
            # Changed django.utils file code, so that the user data returns a naive datetime object that I am manipulating manually to store the data in the user's local time, for easier comparison purposes
            time_zone = form.cleaned_data["time_zone"]

            # Calculates difference between the user's local time and the time in UTC as a timedelta object
            utc_offset = datetime.datetime.now(time_zone).utcoffset()

            # Makes naive times aware
            start_time = form.cleaned_data["start_bid_time"] - utc_offset
            end_time = form.cleaned_data["end_bid_time"] - utc_offset

            UTC = pytz.utc

            current_time = datetime.datetime.now(UTC)

            obj = Listing()
            # Checks if user's current time is in between the start and end datetimes which they entered and sets the bid to active if this is the case
            if start_time <= current_time and current_time <= end_time:
                obj.bid_active = True
            obj.seller = request.user
            obj.name = form.cleaned_data["name"]
            obj.description = form.cleaned_data["description"]
            obj.category = form.cleaned_data["category"]
            obj.condition= form.cleaned_data["condition"]
            obj.image = form.cleaned_data['image']
            obj.start_bid_time= start_time
            obj.time_zone = time_zone
            obj.end_bid_time= end_time
            obj.starting_bid= form.cleaned_data["starting_bid"]
            obj.shipping_options= form.cleaned_data["shipping_options"]
            obj.shipping_cost= form.cleaned_data["shipping_cost"]
            obj.location= form.cleaned_data["location"]
            obj.save()
            return render(request, "auctions/create_listing.html", {
            "form": NewListingForm(), "message1": "Works: check admin class", "start_time": start_time, "end_time": end_time, "current_time": current_time, "utc_offset": utc_offset
            })
        else:
            form = NewListingForm()
            message = "Doesn't work"
            return render(request, "auctions/create_listing.html", {
                "form": form, "message": message
            })
    else:
        if request.user.is_authenticated:
            form = NewListingForm()
            username = User.id
            
            return render(request, "auctions/create_listing.html", {
                "form": form, "timezones": pytz.common_timezones
            })
        # In case someone types the route in the URL bar when they are not logged in
        else:
            return render("auctions/login.html")

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
