from django.db import models
from login.models import Profile

class Leaderboard(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='leaderboard_entries')
    score = models.DecimalField(max_digits=10, decimal_places=2)  # mirrors Profile.balance
    
    class Meta:
        ordering = ['-score']  # order descending

    def __str__(self):
        return f"{self.profile.user} - {self.profile.balance}"