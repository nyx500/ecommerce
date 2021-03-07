from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import *
import datetime
import pytz
from decimal import Decimal
from .forms import *
from .functions import *


# Main page view
def index(request, cat_name=None, user_id=None):

    # Checks which bids are active and which listings to return depending on url parameters (cat_name, user_id)
    is_active()
    listings = Listing.objects.filter(bid_active=True)
    watch = False
    cat = False
    if user_id is None:
        if cat_name:
            listings = listings.filter(category=cat_name)
            cat = True
    else:
        watch = True
        listings = User.objects.get(id=user_id).watched_listings.all()
    when_created(listings)

    if request.method == "POST":
        listing = Listing.objects.get(id=request.POST["listing_id"])

        # Checks if user has added/deleted an item to their watchlist and updates their watchlist.
        if 'watch' in request.POST:
            request.user.watched_listings.add(listing)
            request.user.save()
            return render (request, "auctions/index.html", {
                "listings": listings, "cat":cat, "cat_name": cat_name, "watch": watch
            })
        else:
            listing.user_set.remove(request.user)
            return render (request, "auctions/index.html", {
                "listings": listings, "cat":cat, "cat_name":cat_name, "watch": watch
            })
    else:
        return render(request, "auctions/index.html", {
            "listings": listings, "cat":cat, "cat_name": cat_name, "watch": watch
            })

@login_required
def create_listing(request):

    if request.method == "POST":

        form = NewListingForm(request.POST, request.FILES)

        if form.is_valid():
            # If user input both image upload and image URL, return an error message
            if form.cleaned_data["image"] and form.cleaned_data["image_url"]:
                error = "You must either 1) upload an image OR 2) enter an image URL, but not both!"
                return render(request, "auctions/create_listing.html", {
                "form": NewListingForm(), "error": error
            })
            
            # Converts the user's localised time information all to UTC time
            time_zone = form.cleaned_data["time_zone"]
            start_time = convert_to_utc(time_zone, form.cleaned_data["start_bid_time"])
            end_time = convert_to_utc(time_zone, form.cleaned_data["end_bid_time"])

            obj = Listing()
            obj.seller = request.user
            obj.name = form.cleaned_data["name"]
            obj.description = form.cleaned_data["description"]
            obj.category = form.cleaned_data["category"]
            obj.condition= form.cleaned_data["condition"]
            if form.cleaned_data["image"]:
                obj.image = form.cleaned_data['image']
            if form.cleaned_data["image_url"]:
                obj.image_url = form.cleaned_data['image_url']
            obj.start_bid_time= start_time
            obj.time_zone = time_zone
            obj.end_bid_time= end_time
            obj.starting_bid= form.cleaned_data["starting_bid"]
            obj.shipping_options= form.cleaned_data["shipping_options"]
            obj.shipping_cost= form.cleaned_data["shipping_cost"]
            obj.location= form.cleaned_data["location"]
            obj.save()

            # Checks if new listing is active and updates it
            add_active(obj, start_time, end_time)

            message = f"Thank you for creating a listing for {obj.name}"
            return render(request, "auctions/create_listing.html", {
            "form": NewListingForm(), "message": message
            })

        else:
            error = f"Invalid Form - {form.errors}"
            return render(request, "auctions/create_listing.html", {
                "form": NewListingForm(), "error": error
            })

    else:
        return render(request, "auctions/create_listing.html", {
            "form": NewListingForm()
        })


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

    is_active()
    # Gets the listing as a list of one item and calculates how long ago the listing was created
    listing = Listing.objects.filter(id=id)
    when_created(listing)
    
    # Gets the listing as a single object
    listing = Listing.objects.get(id=id)

    # Gets all the comments for that listing
    comments = listing.comments.all().order_by('-time_submitted')

    # Updates active status of bid based on current time
    add_active(listing, listing.start_bid_time, listing.end_bid_time)

    # Checks if currently logged-in user has won the bid on this listing
    winner = ""
    if request.user.is_authenticated and listing.highest_bid is not None:
        highest_bidder = listing.bids.all().order_by('-amount_bid')[0].bidder
        if request.user == highest_bidder:
            # Checks if the bid is open or closed
            if listing.bid_active == False:
                winner = f"You have won this bid at {Bid.objects.filter(bidder=highest_bidder).order_by('-time_bid')[0].amount_bid}!"

    if request.method == "POST":

        # Logic for if the user clicked on the form to add an item to their watchlist
        if 'watch' in request.POST:
            request.user.watched_listings.add(listing)
            request.user.save()
            message = "You have added this listing to your watchlist!"
            return render (request, "auctions/view_listing.html", {
                "message": message, "form": BidForm(),
                "listing": listing, "winner": winner, "comment_form": CommentForm(), "comments": comments
            })

        # Logic for if the user clicked on the form to remove an item from their watchlist
        elif 'unwatch' in request.POST:
            listing.user_set.remove(request.user)
            message = "You have removed this listing from your watchlist!"
            return render (request, "auctions/view_listing.html", {
                "message": message, "form": BidForm(), "listing": listing, "winner": winner, "comment_form": CommentForm(), "comments": comments
            })

        # Logic for if the user clicked on the form to add a comment
        elif 'leave_comment' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                new_comment = Comment()
                new_comment.comment = comment_form.cleaned_data['comment']
                new_comment.user = request.user
                new_comment.product = listing
                new_comment.save()               
                message = f"Thank you for submitting your comment!"
                return render(request, "auctions/view_listing.html", {
                            "listing": listing, "form": BidForm(), "message": message, "winner": winner, "comment_form": CommentForm(), "comments": comments
                        })            
            else:
                error = f"Form data is invalid. Errors: {comment_form.errors}"
                return render(request, "auctions/view_listing.html", {
                            "listing": listing, "form": BidForm(), "error": error, "winner": winner, "comment_form": CommentForm(), "comments": comments
                        })
        
        # Logic for if user who made the listing decides to close bidding
        elif 'off' in request.POST:
            listing.end_bid_time = datetime.datetime.now(pytz.utc)
            listing.save()
            is_active()
            return HttpResponseRedirect(reverse('index'))

        # Logic for all bidding possibilities
        else:

            form = BidForm(request.POST)
            
            if form.is_valid():
                amount = form.cleaned_data["amount_bid"]
                if listing.minimum_bid is None:
                    strt_bid = listing.starting_bid
                else:
                    strt_bid = listing.minimum_bid

                # Logic for if the amount bid fails to meet the minimum bidding amount
                if amount < strt_bid:
                    error = f"Please match the starting/minimum bid of ${strt_bid}"
                    return render(request, "auctions/view_listing.html", {
                            "listing": listing, "form": BidForm(), "error": error, "winner": winner, "comment_form": CommentForm(), "comments": comments
                        })
                else:
                    # Logic for if there has already been a higher bid than the user's current bid
                    if listing.highest_bid is not None and amount <= listing.highest_bid:
                        # Automatically bids to the highest bidder and then increments the minimum bidding amount by an increment which starts at a quarter of the original starting price but increases by one every time a *successful* bid is placed on the listing
                        listing.minimum_bid = listing.minimum_bid + (listing.starting_bid * Decimal(0.25) * listing.increment)
                        listing.save()
                        # Finds highest bid from bid objects
                        highest_bid = Bid.objects.filter(listing=listing).order_by('-amount_bid')[0]

                        # Places the loser's bid
                        lose = Bid()
                        lose.bidder = request.user
                        lose.listing=listing
                        lose.amount_bid = amount
                        lose.save()
                        
                        # If the automatic bid is smaller than the highest bidder's highest bid, a bid is automatically placed on the highest bidder's behalf
                        if highest_bid.amount_bid > listing.minimum_bid:
                            # Creates new bid for previous higher bidder
                            win = Bid()
                            win.bidder = highest_bid.bidder
                            win.listing = listing
                            win.amount_bid = listing.minimum_bid
                            win.save()
                        
                        listing.current_bid = Bid.objects.all().order_by('-time_bid')[0].amount_bid
                        # Updates the minimum bid once again
                        listing.minimum_bid = listing.minimum_bid + (listing.starting_bid * Decimal(0.25) * listing.increment)
                        listing.save()

                        message = f"Sorry! Unfortunately, your bid of ${amount} was lower than or equal to the maximum bid. Please try again!"
                       
                        return render(request, "auctions/view_listing.html", {
                            "listing": listing, "form": BidForm(), "message": message, "winner": winner, "comment_form": CommentForm(), "comments": comments
                        })
                    
                    # Logic if this bidder is the first one to place a bid
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

                        message = f"Thank you for your bid of ${amount} on Listing #{listing.id} {listing.name}! Your bid has been successful!"
                        return render(request, "auctions/view_listing.html", {
                            "listing":listing, "form": BidForm(), 
                            "message": message, "winner": winner, "comment_form": CommentForm(), "comments": comments
                        })

                    # Logic if the user's bid manages to beat all the previous bids
                    else:
                        listing.increment += 1
                        listing.current_bid = listing.highest_bid + (listing.starting_bid * (Decimal(0.25) * Decimal(listing.increment)))
                        listing.highest_bid = amount
                        listing.minimum_bid = listing.current_bid + (listing.starting_bid * (Decimal(0.25) * Decimal(listing.increment)))
                        listing.save()

                        obj = Bid()
                        obj.bidder = request.user
                        obj.listing = listing
                        obj.amount_bid = amount
                        obj.save()

                        if listing.highest_bid > listing.minimum_bid:
                            obj2 = Bid()
                            obj2.bidder = request.user
                            obj2.listing = listing
                            obj2.amount_bid = listing.current_bid
                            obj2.save()

                        message = f"Thank you for your bid of ${amount} on Listing #{listing.id} {listing.name}! Your bid has been successful!"
                        return render(request, "auctions/view_listing.html", {
                            "listing": listing, "form": BidForm(), 
                            "message": message, "winner": winner, "comment_form": CommentForm(), "comments": comments
                        })
            # Error message if form data is invalid
            else:
                message = f"Invalid form - {form.errors}"
                return render(request, "auctions/view_listing.html", {
                    "listing" :listing, "form": BidForm(), "message": message, "comment_form":CommentForm(), "comments": comments
                })
    else:
        return render(request, "auctions/view_listing.html",
        {   
            "form": BidForm(),
            "listing": listing, "winner": winner, "comment_form": CommentForm(), "comments": comments
        })


def categories(request):
    is_active()
    listings = Listing.objects.filter(bid_active=True).values('category').distinct().order_by('category')
    return render(request, "auctions/categories.html", {
        "listings": listings
    })

