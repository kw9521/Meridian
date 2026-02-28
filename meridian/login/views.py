from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Profile

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            return render(request, 'login/register.html', {'error': 'Username taken'})
        user = User.objects.create_user(username=username, password=password)
        Profile.objects.create(user=user)
        login(request, user)
        return redirect('/stocks/')
    return render(request, 'login/register.html')

def login_view(request):
    if request.method == 'POST':
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user:
            login(request, user)
            return redirect('/stocks/')
        return render(request, 'login/login.html', {'error': 'Invalid credentials'})
    return render(request, 'login/login.html')

def logout_view(request):
    logout(request)
    return redirect('/login/')