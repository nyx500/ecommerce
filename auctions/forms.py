from .models import *
from django import forms
import datetime
from django.contrib.admin import widgets
from bootstrap_datepicker_plus import DateTimePickerInput
from django.core.validators import MinValueValidator

class BidForm(forms.Form):
    amount_bid = forms.DecimalField(decimal_places=2, validators=[MinValueValidator(0)], label="Place bid in US $")
        

class NewListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['name', 'description', 'category', 'condition', 'start_bid_time', 'end_bid_time', 'image', 'image_url', 'starting_bid', 'shipping_cost', 'location', 'time_zone', 'shipping_options']
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
        
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']
        comment = forms.Textarea()