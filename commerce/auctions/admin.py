from django.contrib import admin
# Have to import all the models needed from .models in the app directory because otherwise they cannot be edited on the admin page
from .models import Bid, Category, Comment, Listing, User
# admin.site.register() function allows superuser to manipulate models on the admin page when server runs
admin.site.register(Bid)
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(Listing)
admin.site.register(User)
