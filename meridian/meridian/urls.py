from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('login.urls')),
    path('stocks/', include('stocks.urls')),
    path('leaderboard/', include('leaderboard.urls')),
    path('about/', include("About.urls")),
    path('', include('gettingStarted.urls')),
]