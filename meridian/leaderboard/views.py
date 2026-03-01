from django.shortcuts import render
from .models import Profile, Leaderboard

#Leaderboard has top 10 users
def leaderboard_view(request):
    for profile in Profile.objects.select_related('user'):
        Leaderboard.objects.update_or_create(
            profile=profile,
            defaults={'score': profile.balance}
        )

    top_entries = Leaderboard.objects.select_related('profile')[:10]

    context = {
        'top_entries': top_entries,
    }
    return render(request, 'leaderboard.html', context)
