from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('stock/<str:ticker>/', views.stock_view, name='stock'),
    path('portfolio/', views.portfolio_view, name='portfolio'),
    path('history/', views.transactions_view, name='transactions'),

    # API
    path('api/stock/<str:ticker>/', views.api_stock, name='api_stock'),
    path('api/search/<str:ticker>/', views.api_search, name='api_search'),
    path('api/portfolio/', views.api_portfolio, name='api_portfolio'),
    path('api/buy/', views.api_buy, name='api_buy'),
    path('api/sell/', views.api_sell, name='api_sell'),
    path('api/user/', views.api_user, name='api_user'),
]