from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
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
from django.db.models import Q

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

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']
        comment = forms.Textarea()

def index(request):
    # Code for all methods to find active listings and update the database
    UTC = pytz.utc
    current_time = datetime.datetime.now(UTC)
    for listing in Listing.objects.all():
        # Checks if time is right for listing to be active
        if listing.start_bid_time <= current_time and current_time <= listing.end_bid_time:
            listing.bid_active = True
        else:
            listing.bid_active = False
        listing.save()
    if request.method == "POST":
        form = BidForm(request.POST)
        listing = Listing.objects.get(id=request.POST["listing_id"])
        if form.is_valid():
            # Money object used for user's bid
            amount = form.cleaned_data["amount_bid"]
            # Listing of the object bid on
            listing_id = request.POST["listing_id"]
            # Amount of starting/minimum bid price
            og_amount = request.POST["og_amount"]
            # The currency of the starting/minimum bid price
            og_currency = request.POST["og_currency"]
            # User's bid is converted into a money object with the same currency as the listing's currency
            amount = convert_money(amount.amount, amount.currency, og_currency)
            # Turns starting/minimum bid amount into a float object, so that it can be compared with the bidder's amount
            strt_bid = float(Listing.objects.filter(id=listing_id).values_list('starting_bid')[0][0])
            min_bid = float(Listing.objects.filter(id=listing_id).values_list('minimum_bid')[0][0])
            # Checks if the bidder has matched the minimum bid amount
            if float(amount.amount) < strt_bid or float(amount.amount) < min_bid:
                # Returns a message telling the bidder that his amount has not matched the minimum bid
                message = f"Please match the starting/minimum bid of {og_amount} in {og_currency}"
                return render(request, "auctions/index.html", {
                            "listings": Listing.objects.filter(Q(bid_active=True) & Q(user_closed_bid=False)), "form": BidForm(), "message": message
                        })
            # Code for if the bidder has placed enough money for a bid to be created
            else:
                # Increments the minimum bid amount for that listing by 25% of the original price every time a bid is made
                listing = Listing.objects.get(id=listing_id)
                if listing.highest_bid is not None and amount <= listing.highest_bid:
                    # Increments the minimum bidding amount by a quarter of the original starting price
                    new_bid = listing.minimum_bid + (listing.starting_bid * Decimal(0.25))
                    new_min_bid = new_bid + (listing.starting_bid * Decimal(0.25))
                    listing.minimum_bid = new_min_bid
                    listing.save()
                    # Finds highest bid from bid objects
                    highest_bid = Bid.objects.filter(listing=listing).order_by('-amount_bid')[0]
                    
                    if highest_bid.amount_bid > new_bid:
                        # Creates new bid for previous higher bidder
                        win = Bid()
                        win.bidder = highest_bid.bidder
                        win.listing = listing
                        win.amount_bid = new_bid
                        win.save()

                    lose = Bid()
                    lose.bidder = request.user
                    lose.listing=listing
                    lose.amount_bid = amount
                    lose.save()

                    message = f"Error: Unfortunately your bid of {amount} was not greater than {highest_bid.amount_bid} placed by {highest_bid.bidder.username}. {new_bid} has automatically been bid to {highest_bid.bidder.username}. Please try again!"
                    return render(request, "auctions/index.html", {
                        "listings": Listing.objects.filter(Q(bid_active=True) & Q(user_closed_bid=False)), "form": BidForm(), "message": message
                    })
                elif listing.highest_bid is None:
                    min_amount = convert_money(listing.minimum_bid.amount, listing.minimum_bid.currency, listing.starting_bid.currency)
                    listing.minimum_bid = min_amount
                    listing.minimum_bid = listing.starting_bid * Decimal(1.25)
                    listing.save()
                    obj = Bid()
                    obj.bidder = request.user
                    obj.listing = Listing.objects.get(id=listing_id)
                    obj.amount_bid = amount
                    obj.save()
                    listing = Listing.objects.get(id=listing_id)
                    listing.highest_bid = amount
                    listing.save()
                    message = f"Thank you for your bid of {amount} on Listing #{listing.id}! Your bid has been successful!"
                    return render(request, "auctions/index.html", {
                        "listings": Listing.objects.filter(Q(bid_active=True) & Q(user_closed_bid=False)), "form": BidForm(), 
                        "message": message
                    })
                else:
                    listing = Listing.objects.get(id=listing_id)
                    listing.minimum_bid = listing.highest_bid + (listing.starting_bid * Decimal(0.25))
                    listing.highest_bid = amount
                    listing.save()
                    obj = Bid()
                    obj.bidder = request.user
                    obj.listing = Listing.objects.get(id=listing_id)
                    obj.amount_bid = amount
                    obj.save()
                    message = f"Thank you for your bid of {amount} on Listing #{listing.id}! Your bid has been successful!"
                    return render(request, "auctions/index.html", {
                        "listings": Listing.objects.filter(Q(bid_active=True) & Q(user_closed_bid=False)), "form": BidForm(), 
                        "message": message
                    })
        else:
            return render(request, "auctions/index.html", {
                "listings": Listing.objects.filter(Q(bid_active=True) & Q(user_closed_bid=False)), "form": BidForm(), "message": "Invalid form"
            })
    else:
        return render(request, "auctions/index.html", {
            "listings": Listing.objects.filter(Q(bid_active=True) & Q(user_closed_bid=False)), "form": BidForm()
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

def view_listing(request, id):
    listing = Listing.objects.get(id=id)
    comments = listing.comments.all().order_by('-time_submitted')
    UTC = pytz.utc
    current_time = datetime.datetime.now(UTC)
    if listing.start_bid_time <= current_time and current_time <= listing.end_bid_time:
            listing.bid_active = True
    else:
        listing.bid_active = False
    listing.save()
    winner = ""
    if request.user.is_authenticated and listing.highest_bid is not None:
        highest_bidder = Bid.objects.all().order_by('-amount_bid')[0].bidder
        if request.user == highest_bidder:
                user_final_bid = Bid.objects.filter(bidder=highest_bidder).order_by('-time_bid')[0]
                if listing.bid_active == False:
                    winner = f"You have won this bid at {user_final_bid.amount_bid}!"
                elif listing.user_closed_bid == True:
                    winner = f"You have won this bid at {user_final_bid.amount_bid}!"

    if request.method == "POST":
        if 'watch' in request.POST:
            current_listing = Listing.objects.get(id=request.POST["listing_id"])
            watchers = current_listing.user_set.all()
            current_user = request.user
            current_user.watched_listings.add(current_listing)
            current_user.save()
            message = "You have added this listing to your watchlist"
            if current_listing.highest_bid is not None:
                last_bid = Bid.objects.all().order_by('-time_bid')[0]
            else:
                last_bid = ""
            return render (request, "auctions/view_listing.html", {
                "message": message, "form": BidForm(), "last_bid": last_bid,
                "listing": current_listing, "watchers": watchers, "winner": winner, "comment_form": CommentForm(), "comments": comments
            })
        elif 'unwatch' in request.POST:
            current_listing = Listing.objects.get(id=request.POST["listing_id"])
            watchers = current_listing.user_set.all()
            current_user = request.user
            current_listing.user_set.remove(current_user)
            message = "You have removed this listing to your watchlist"
            if current_listing.highest_bid is not None:
                last_bid = Bid.objects.all().order_by('-time_bid')[0]
            else:
                last_bid = ""
            return render (request, "auctions/view_listing.html", {
                "message": message, "form": BidForm(), "last_bid": last_bid,
                "listing": current_listing, "watchers": watchers, "winner": winner, "comment_form": CommentForm(), "comments": comments
            })
        elif 'leave_comment' in request.POST:
            watchers =  listing.user_set.all()
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.cleaned_data['comment']
                new_comment = Comment()
                new_comment.comment = comment
                new_comment.user = request.user
                new_comment.product = listing
                new_comment.save()
                if listing.highest_bid is not None:
                        last_bid = Bid.objects.all().order_by('-time_bid')[0]
                else:
                    last_bid = ""
                message = f"Thank you for submitting a comment."
                return render(request, "auctions/view_listing.html", {
                            "listing": listing, "form": BidForm(), "message": message, "last_bid": last_bid, "watchers":watchers, "winner": winner, "comment_form": CommentForm(), "comments": comments
                        })
            else:
                if listing.highest_bid is not None:
                        last_bid = Bid.objects.all().order_by('-time_bid')[0]
                else:
                    last_bid = ""
                message = f"Form data is invalid. Errors: {comment_form.errors}"
                return render(request, "auctions/view_listing.html", {
                            "listing": listing, "form": BidForm(), "message": message, "last_bid": last_bid, "watchers":watchers, "winner": winner, "comment_form": CommentForm(), "comments": comments
                        })

        elif 'off' in request.POST:
            current_listing = Listing.objects.get(id=id)
            current_listing.user_closed_bid = True
            current_listing.save()
            return HttpResponseRedirect(reverse('index'))

        else:
            form = BidForm(request.POST)
            listing = Listing.objects.get(id=request.POST["listing_id"])
            if form.is_valid():
                watchers = listing.user_set.all()
                # Money object used for user's bid
                amount = form.cleaned_data["amount_bid"]
                # Listing of the object bid on
                listing_id = request.POST["listing_id"]
                # Amount of starting/minimum bid price
                og_amount = request.POST["og_amount"]
                # The currency of the starting/minimum bid price
                og_currency = request.POST["og_currency"]
                # User's bid is converted into a money object with the same currency as the listing's currency
                amount = convert_money(amount.amount, amount.currency, og_currency)
                # Turns starting/minimum bid amount into a float object, so that it can be compared with the bidder's amount
                strt_bid = float(Listing.objects.filter(id=listing_id).values_list('starting_bid')[0][0])
                min_bid = float(Listing.objects.filter(id=listing_id).values_list('minimum_bid')[0][0])
                # Checks if the bidder has matched the minimum bid amount
                if float(amount.amount) < strt_bid or float(amount.amount) < min_bid:
                    # Returns a message telling the bidder that his amount has not matched the minimum bid
                    message = f"Error: Please match the starting/minimum bid of {og_amount} in {og_currency}"
                    if listing.highest_bid is not None:
                        last_bid = Bid.objects.all().order_by('-time_bid')[0]
                    return render(request, "auctions/view_listing.html", {
                                "listing": listing, "form": BidForm(), "message": message, "last_bid": last_bid, "watchers":watchers, "winner": winner, "comment_form": CommentForm(), "comments": comments
                            })
                else:
                    # Increments the minimum bid amount for that listing by 25% of the original price every time a bid is made
                    listing = Listing.objects.get(id=id)
                    if listing.highest_bid is not None and amount <= listing.highest_bid:
                        # Increments the minimum bidding amount by a quarter of the original starting price
                        new_bid = listing.minimum_bid + (listing.starting_bid * Decimal(0.25))
                        new_min_bid = new_bid + (listing.starting_bid * Decimal(0.25))
                        listing.minimum_bid = new_min_bid
                        listing.save()
                        # Finds highest bid from bid objects
                        highest_bid = Bid.objects.filter(listing=listing).order_by('-amount_bid')[0]

                        lose = Bid()
                        lose.bidder = request.user
                        lose.listing=listing
                        lose.amount_bid = amount
                        lose.save()
                        
                        if highest_bid.amount_bid > new_bid:
                            # Creates new bid for previous higher bidder
                            win = Bid()
                            win.bidder = highest_bid.bidder
                            win.listing = listing
                            win.amount_bid = new_bid
                            win.save()

                        message = f"Sorry! Unfortunately your bid of {amount} was lower than or equal to the highest bid of {highest_bid.amount_bid} placed by {highest_bid.bidder.username}. {new_bid} has automatically been bid to {highest_bid.bidder.username}. Please try again!"
                        last_bid = Bid.objects.all().order_by('-time_bid')[0]
                        return render(request, "auctions/view_listing.html", {
                            "listing": listing, "form": BidForm(), "message": message, "last_bid": last_bid, "watchers":watchers, "winner": winner, "comment_form": CommentForm(), "comments": comments
                        })
                    elif listing.highest_bid is None:
                        min_amount = convert_money(listing.minimum_bid.amount, listing.minimum_bid.currency, listing.starting_bid.currency)
                        listing.minimum_bid = min_amount
                        listing.minimum_bid = listing.starting_bid * Decimal(1.25)
                        listing.save()
                        obj = Bid()
                        obj.bidder = request.user
                        obj.listing = Listing.objects.get(id=listing_id)
                        obj.amount_bid = amount
                        obj.save()
                        listing = Listing.objects.get(id=listing_id)
                        listing.highest_bid = amount
                        listing.save()
                        last_bid = Bid.objects.all().order_by('-time_bid')[0]
                        message = f"Thank you for your bid of {amount} on Listing #{listing.id}! Your bid has been successful!"
                        return render(request, "auctions/view_listing.html", {
                            "listing":listing, "form": BidForm(), 
                            "message": message, "last_bid": last_bid, "watchers":watchers, "winner": winner, "comment_form": CommentForm(), "comments": comments
                        })
                    else:
                        listing = Listing.objects.get(id=id)
                        listing.minimum_bid = listing.highest_bid + (listing.starting_bid * Decimal(0.25))
                        listing.highest_bid = amount
                        listing.save()
                        obj = Bid()
                        obj.bidder = request.user
                        obj.listing = Listing.objects.get(id=listing_id)
                        obj.amount_bid = amount
                        obj.save()
                        obj2 = Bid()
                        obj2.bidder = request.user
                        obj2.listing = Listing.objects.get(id=listing_id)
                        obj2.amount_bid = listing.minimum_bid
                        obj2.save()
                        listing.minimum_bid = listing.highest_bid + (listing.starting_bid * Decimal(0.25))
                        last_bid = Bid.objects.all().order_by('-time_bid')[0]
                        message = f"Thank you for your bid of {amount} on Listing #{listing.id}! Your bid has been successful!"
                        return render(request, "auctions/view_listing.html", {
                            "listing": listing, "form": BidForm(), 
                            "message": message, "last_bid": last_bid, "watchers":watchers, "winner": winner, "comment_form": CommentForm(), "comments": comments
                        })
            else:
                listing = Listing.objects.get(id=id)
                watchers = listing.user_set.all()
                if listing.highest_bid is not None:
                    last_bid = Bid.objects.all().order_by('-time_bid')[0]
                return render(request, "auctions/view_listing.html", {
                    "listing":listing, "last_bid": last_bid, "form": BidForm(), "message": "Invalid form", "watchers": watchers, "comment_form": CommentForm(), "comments": comments
                })
    else:
        listing = Listing.objects.get(id=id)
        watchers = listing.user_set.all()
        if listing.highest_bid is not None:
            last_bid = Bid.objects.all().order_by('-time_bid')[0]
        else:
            last_bid = ""
        return render(request, "auctions/view_listing.html",
        {   
            "form": BidForm(), "last_bid": last_bid,
            "listing": listing, "watchers": watchers, "winner": winner, "comment_form": CommentForm(), "comments": comments
        })

@login_required
def watchlist(request):
    user = request.user
    watchlist = Listing.objects.filter(user__id=user.id)
    return render(request, "auctions/watchlist.html", {
        "watchlist": watchlist
    })

def categories(request):
    categories = Category.objects.all().order_by('category')
    return render(request, "auctions/categories.html", {
        "categories": categories
    })

def cat_listings(request, id):
    category = Category.objects.get(id=id)
    
    UTC = pytz.utc
    current_time = datetime.datetime.now(UTC)

    active_listings = []
    for listing in category.listings.all():
        if (current_time >= listing.start_bid_time and current_time <= listing.end_bid_time):
            if not listing.user_closed_bid:
                active_listings.append(listing)
                listing.save()
    return render(request, "auctions/cat_listings.html", {
        "listings": active_listings
    })

