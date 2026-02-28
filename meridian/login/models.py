from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.FloatField(default=100000.0)

    def __str__(self):
        return f"{self.user.username} — ${self.balance:,.2f}"