from django.shortcuts import render

def getting_started_view(request):
    return render(request, "gettingStarted.html")