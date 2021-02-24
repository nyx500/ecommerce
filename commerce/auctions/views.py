from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import *
import datetime
import pytz
from djmoney_rates.utils import convert_money
from decimal import Decimal
from django_prices_openexchangerates.tasks import extract_rate, get_latest_exchange_rates, update_conversion_rates
from .forms import *
from .functions import *

# Main page view
def index(request):
    # Sets 'bid active' property for objects for which the current time is between their start bid and end bid times
    is_active()
    listings = Listing.objects.filter(bid_active=True)
    return render(request, "auctions/index.html", {
        "listings": listings
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
            add_active(obj, start_time, end_time)
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
    add_active(listing, listing.start_bid_time, listing.end_bid_time)
    winner = ""
    if request.user.is_authenticated and listing.highest_bid is not None:
        highest_bidder = Bid.objects.all().order_by('-amount_bid')[0].bidder
        if request.user == highest_bidder:
                user_final_bid = Bid.objects.filter(bidder=highest_bidder).order_by('-time_bid')[0]
                if listing.bid_active == False:
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
            UTC = pytz.utc
            current_listing.end_bid_time = datetime.datetime.now(UTC)
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
                if Listing.objects.get(id=listing_id).minimum_bid is None:
                    strt_bid = Listing.objects.get(id=listing_id).starting_bid
                else:
                    strt_bid = Listing.objects.get(id=listing_id).minimum_bid
                # Checks if the bidder has matched the minimum bid amount
                if amount < strt_bid:
                    # Returns a message telling the bidder that his amount has not matched the minimum bid
                    message = f"Error: Please match the starting/minimum bid of {og_amount}{og_currency}"
                    if listing.highest_bid is not None:
                        last_bid = Bid.objects.all().order_by('-time_bid')[0]
                    else:
                        last_bid = None
                    return render(request, "auctions/view_listing.html", {
                                "listing": listing, "form": BidForm(), "message": message, "last_bid": last_bid, "watchers":watchers, "winner": winner, "comment_form": CommentForm(), "comments": comments
                            })
                else:
                    # Increments the minimum bid amount for that listing by 25% of the original price every time a bid is made
                    listing = Listing.objects.get(id=id)
                    if listing.highest_bid is not None and amount <= listing.highest_bid:
                        # Increments the minimum bidding amount by a quarter of the original starting price
                        new_min_bid = listing.minimum_bid + (listing.starting_bid * Decimal(0.25) * listing.increment)
                        listing.minimum_bid = new_min_bid
                        listing.save()
                        # Finds highest bid from bid objects
                        highest_bid = Bid.objects.filter(listing=listing).order_by('-amount_bid')[0]

                        lose = Bid()
                        lose.bidder = request.user
                        lose.listing=listing
                        lose.amount_bid = amount
                        lose.save()
                        
                        if highest_bid.amount_bid > new_min_bid:
                            # Creates new bid for previous higher bidder
                            win = Bid()
                            win.bidder = highest_bid.bidder
                            win.listing = listing
                            win.amount_bid = new_min_bid
                            win.save()
                        
                        listing.current_bid = Bid.objects.all().order_by('-time_bid')[0].amount_bid
                        listing.minimum_bid = listing.minimum_bid + (listing.starting_bid * Decimal(0.25) * listing.increment)
                        listing.save()

                        message = f"Sorry! Unfortunately your bid of {amount} was lower than or equal to the highest bid of {highest_bid.amount_bid} placed by {highest_bid.bidder.username}. {new_min_bid} has automatically been bid to {highest_bid.bidder.username}. Please try again!"
                        last_bid = Bid.objects.all().order_by('-time_bid')[0]
                        return render(request, "auctions/view_listing.html", {
                            "listing": listing, "form": BidForm(), "message": message, "last_bid": last_bid, "watchers":watchers, "winner": winner, "comment_form": CommentForm(), "comments": comments
                        })
                    elif listing.highest_bid is None:
                        obj = Bid()
                        obj.bidder = request.user
                        obj.listing = listing
                        obj.amount_bid = amount
                        obj.save()
                        obj2 = Bid()
                        obj2.bidder = request.user
                        obj2.listing = listing
                        obj2.amount_bid = listing.starting_bid
                        obj2.save()
                        listing.minimum_bid = listing.starting_bid * Decimal(1.25)
                        listing.highest_bid = amount
                        listing.current_bid = Bid.objects.all().order_by('-time_bid')[0].amount_bid 
                        listing.save()
                        last_bid = Bid.objects.all().order_by('-time_bid')[0]
                        message = f"Thank you for your bid of {amount} on Listing #{listing.id}! Your bid has been successful!"
                        return render(request, "auctions/view_listing.html", {
                            "listing":listing, "form": BidForm(), 
                            "message": message, "last_bid": last_bid, "watchers":watchers, "winner": winner, "comment_form": CommentForm(), "comments": comments
                        })
                    else:
                        listing.increment += 1
                        listing.save()
                        obj = Bid()
                        obj.bidder = request.user
                        obj.listing = Listing.objects.get(id=listing_id)
                        obj.amount_bid = amount
                        obj.save()
                        obj2 = Bid()
                        obj2.bidder = request.user
                        obj2.listing = Listing.objects.get(id=listing_id)
                        obj2.amount_bid.amount = listing.highest_bid.amount + (listing.starting_bid.amount * (Decimal(0.25) * Decimal(listing.increment)))
                        obj2.amount_bid.currency = listing.highest_bid.currency
                        obj2.save()
                        last_bid = Bid.objects.all().order_by('-time_bid')[0]
                        listing.current_bid.amount = Bid.objects.all().order_by('-time_bid')[0].amount_bid.amount
                        listing.current_bid.currency = listing.starting_bid.currency
                        listing.minimum_bid.amount = listing.current_bid.amount + (Decimal(0.25) * Decimal(listing.increment))
                        listing.highest_bid = amount
                        listing.save()
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
                    "listing" :listing, "last_bid": last_bid, "form": BidForm(), "message": "Invalid form", "watchers": watchers, "comment_form": CommentForm(), "comments": comments
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
    is_active()
    listings = category.listings.filter(bid_active=True)
    return render(request, "auctions/cat_listings.html", {
        "listings": listings
    })

