from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
# Important! Remember to import all new classes from models
from .models import Bid, Category, Comment, Listing, User
import django.forms
from django.contrib.admin import widgets
from bootstrap_datepicker_plus import DateTimePickerInput

class NewListingForm(django.forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['name', 'description', 'category', 'condition', 'start_bid_time', 'end_bid_time', 'image']
        # Models do not take datetime formats whereas forms do. Therefore it is crucial to add the exact type of datetime input format to the form, so that it validates correctly. It is important for the input_format (server side validation) to match the widget DateTimePickerInput options in terms of whether you put / or - or : in between variables!!!! Otherwise the fields will not match and the form will not be validated
        start_bid_time = django.forms.DateTimeField(input_formats=['%MM/%DD/%YYYY %HH:%mm:%ss'])
        end_bid_time = django.forms.DateTimeField(input_formats=['%MM/%DD/%YYYY %HH:%mm:%ss'])
        widgets = {
            'description': django.forms.Textarea(attrs={"rows": 8, "cols": 100})
            , 'start_bid_time': DateTimePickerInput(options={
                "format": "MM/DD/YYYY HH:mm:ss"
            }),
            'end_bid_time': DateTimePickerInput(options={
                "format": "MM/DD/YYYY HH:mm:ss"
            })
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
        form = NewListingForm(request.POST)
        # Server-side check validating the form
        if form.is_valid():
            message = "Finally works"
            return render(request, "auctions/create_listing.html", {
            "form": form, "message": message
            })
        else:
            form = NewListingForm()
            message = "Doesn't work 1"
            return render(request, "auctions/create_listing.html", {
                "form": form, "message": message
            })
    else:
        form = NewListingForm()
        message = "Doesn't work 2"
        return render(request, "auctions/create_listing.html", {
            "form": form, "message": message
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
