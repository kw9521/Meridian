from django.db import models
from django.contrib.auth.models import User

class Holding(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)
    shares = models.FloatField()
    buy_price = models.FloatField()
    bought_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.ticker} x{self.shares}"

class Transaction(models.Model):
    BUY = 'BUY'
    SELL = 'SELL'
    ACTION_CHOICES = [(BUY, 'Buy'), (SELL, 'Sell')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)
    action = models.CharField(max_length=4, choices=ACTION_CHOICES)
    shares = models.FloatField()
    price = models.FloatField()
    total = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} {self.action} {self.shares} {self.ticker}"