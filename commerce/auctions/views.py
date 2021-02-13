from django.contrib.auth import authenticate, login, logout
from django.contrib.admin import widgets
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Bid, Category, Comment, Listing, User
from django import forms
import datetime
import pytz
import django.utils
import bootstrap4
from bootstrap_datepicker_plus import DateTimePickerInput


class DateTimeInput(forms.DateTimeInput):
    input_type = 'datetime'

class NewListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['name', 'description', 'category', 'condition', 'start_bid_time', 'end_bid_time', 'image', 'starting_price', 'shipping_options', 'shipping_cost', 'location', 'time_zone']
        # Models do not take datetime formats whereas forms do. Therefore it is crucial to add the exact type of datetime input format to the form, so that it validates correctly. It is important for the input_format (server side validation) to match the widget DateTimePickerInput options in terms of whether you put / or - or : in between variables!!!! Otherwise the fields will not match and the form will not be validated
        start_bid_time = forms.DateTimeField(initial=datetime.datetime.now(),input_formats=['%m/%d/%Y %H:%M:%S'])
        end_bid_time = forms.DateTimeField(initial=(datetime.datetime.now() + datetime.timedelta(days=1)), label="Insert datetime", input_formats=['%m/%d/%Y %H:%M:%S'])
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
    return render(request, "auctions/index.html")

def create_listing(request):
    if request.method == "POST":
        form = NewListingForm(request.POST, request.FILES)
        # Server-side check validating the form
        if form.is_valid():
            timezone = form.cleaned_data["time_zone"]
            utc_offset = datetime.datetime.now(timezone).utcoffset()
            start_time_in_utc_time = (form.cleaned_data["start_bid_time"] - utc_offset).replace(tzinfo=datetime.timezone.utc)
            end_time_in_utc_time = (form.cleaned_data["end_bid_time"] - utc_offset).replace(tzinfo=datetime.timezone.utc)
            utc_timezone = pytz.timezone("UTC")
            current_time_in_utc = utc_timezone.localize(datetime.datetime.utcnow())
            obj = Listing()
            if start_time_in_utc_time < current_time_in_utc and current_time_in_utc < end_time_in_utc_time:
                obj.bid_active = True
            obj.seller = request.user
            obj.name = form.cleaned_data["name"]
            obj.description = form.cleaned_data["description"]
            obj.category = form.cleaned_data["category"]
            obj.condition= form.cleaned_data["condition"]
            obj.image = form.cleaned_data['image']
            obj.start_bid_time= start_time_in_utc_time
            obj.time_zone = timezone
            obj.end_bid_time= end_time_in_utc_time
            obj.starting_price= form.cleaned_data["starting_price"]
            obj.shipping_options= form.cleaned_data["shipping_options"]
            obj.shipping_cost= form.cleaned_data["shipping_cost"]
            obj.location= form.cleaned_data["location"]
            obj.save()
            return render(request, "auctions/create_listing.html", {
            "form": NewListingForm(), "message1": "Works: check admin class"
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
