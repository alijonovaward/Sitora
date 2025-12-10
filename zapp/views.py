from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from pydub import AudioSegment

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
def audio_view(request, status=None):
    profile = None
    audios = None

    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        pass

    if profile and profile.role == 'user':
        audios = Audio.objects.filter(audio_author=request.user)
    else:
        audios = Audio.objects.all()

    if status:
        audios = audios.filter(status=status)

    audios = audios.order_by('-created_at')

    context = {
        'audios': audios,
        'status': status,
    }
    return render(request, "zapp/audio_list.html", context)


@login_required
def upload_audio(request):
    if request.method == "POST" and request.FILES.get('audio_file'):
        audio_file = request.FILES['audio_file']

        # Audio instance yaratish
        audio_instance = Audio(audio_author=request.user)
        audio_instance.audio_file.save(f"{request.user.username}_recording.wav", audio_file)
        audio_instance.save()

        # Duration hisoblash (pydub yordamida)
        try:
            audio_path = audio_instance.audio_file.path
            audio_segment = AudioSegment.from_file(audio_path)
            duration_sec = round(len(audio_segment) / 1000, 1)  # sekundlarda
            audio_instance.duration = duration_sec
            audio_instance.save(update_fields=['duration'])

            # Profilga jami duration qo'shish
            profile = request.user.profile
            profile.total_audio_duration += duration_sec
            profile.save(update_fields=['total_audio_duration'])

        except Exception as e:
            return JsonResponse({'message': f'Error processing audio: {str(e)}'}, status=500)

        return JsonResponse({'message': 'Audio uploaded and duration calculated!'})

    return JsonResponse({'message': 'No file uploaded.'}, status=400)