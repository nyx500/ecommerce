from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("categories", views.categories, name="categories"),
    path("", views.index, name="index"),
    path("create_listing", views.create_listing, name="create"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("<int:id>", views.view_listing, name="view"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("cat_listings<int:id>", views.cat_listings, name="cat_listings"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
