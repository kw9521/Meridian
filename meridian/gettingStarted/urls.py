from django.urls import path
from . import views

urlpatterns = [
    path('getting-started/', views.getting_started_view, name='gettingStarted'),
]