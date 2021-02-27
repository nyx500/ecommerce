from .models import *
from django import forms
import datetime
from djmoney.forms.fields import MoneyField
from django.contrib.admin import widgets
from bootstrap_datepicker_plus import DateTimePickerInput

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount_bid']
        labels = {
            'amount_bid': "Enter the amount you would like to bid and select your currency"
        }
    # Gets rid of colon after label
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(BidForm, self).__init__(*args, **kwargs)
        

class NewListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['name', 'description', 'category', 'condition', 'start_bid_time', 'end_bid_time', 'image', 'image_url', 'starting_bid', 'shipping_cost', 'location', 'time_zone', 'shipping_options']
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
        # The super() function returns a temporary object of the superclass kind (here it is a NewListingForm) and then changes and saves it
        super(NewListingForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = self.fields['category'].queryset.order_by('category')
        
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']
        comment = forms.Textarea()