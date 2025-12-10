from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Audio, Profile


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")  # logindan keyin redirect qiladigan page
        else:
            messages.error(request, "Username yoki password noto‘g‘ri")

    return render(request, "zapp/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    # Agar user oddiy foydalanuvchi bo‘lsa, faqat uning audiolari
    if profile and profile.user:
        audios = Audio.objects.filter(audio_author=user).order_by('-created_at')
    else:
        audios = Audio.objects.all().order_by('-created_at')

    context = {
        'user': user,
        'profile': profile,
        'audios': audios,
    }
    return render(request, "zapp/dashboard.html", context)

@login_required
def audio_view(request, status=None, user_id=None):
    pass