from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("categories", views.categories, name="categories"),
    path("", views.index, name="index"),
    path("category/<str:cat_name>", views.index, name="index"),
    path("watchlist/<int:user_id>", views.index, name="index"),
    path("create_listing", views.create_listing, name="create"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("<int:id>", views.view_listing, name="view"),
]+static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG == True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
