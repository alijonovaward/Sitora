from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from pydub import AudioSegment
import requests
from django.core.exceptions import ObjectDoesNotExist

from .models import Audio, Profile, S2TRequest


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
    total_duration = int(audios.aggregate(total=Sum('duration'))['total'] or 0)

    context = {
        'audios': audios,
        'status': status,
        'count': audios.count(),
        'total_duration': total_duration,
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

@login_required
@user_passes_test(lambda u: u.is_staff)  # faqat admin
def update_audio_status(request, audio_id):
    status_url = 'pending'
    if request.method == 'POST':
        audio = get_object_or_404(Audio, id=audio_id)
        new_status = request.POST.get('status')
        status_url = request.POST.get('status_url')
        if new_status == 'approved':
            if audio.status == 'pending':
                audio.status = 'processing'
            elif audio.status == 'finished':
                audio.status = 'done'
        elif new_status == 'rejected':
            if audio.status == 'pending':
                audio.status = 'failed'
            elif audio.status == 'processing':
                audio.status = 'pending'
            elif audio.status == 'finished':
                audio.status = 'processing'
                audio.transcript = ""

        audio.save()
    return redirect('audio', status=status_url)

def add_transcript(request, audio_id = None):
    try:
        status = "processing"
        if request.method == "POST":
            transcript = request.POST.get('transcript')
            text_author = request.user
            status = request.POST.get('status')
            audio = get_object_or_404(Audio, id=audio_id)
            if transcript:
                audio.transcript = transcript
                audio.status = 'finished'
                audio.transcript_author = text_author
                audio.save()
        return redirect('audio', status=status)
    except Exception as e:
        pass

def send_transcript(request, audio_id = None):
    try:
        audio = get_object_or_404(Audio, id=audio_id)
        status_url = request.POST.get('status_url')

        url = "https://back.aisha.group/api/v2/stt/post/"
        api_key = "9gYFg92M.8G32FkSQTmaOpQt8nOX581qkQPPqh1ps"

        audio_path = audio.audio_file.path

        with open(audio_path, 'rb') as f:
            files = {
                'audio': f
            }

            data = {
                'title': 'Weekly sync',
                'language': 'uz',
                'webhook_notification_url': 'https://example.com/webhook',
                'has_diarization': False
            }

            headers = {
                'x-api-key': api_key
            }

            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )

        response.raise_for_status()
        data_json = response.json()
        task_id = data_json.get('id')

        s2t_request, created = S2TRequest.objects.get_or_create(
            audio=audio,
            defaults={
                'status': 'pending',
                'task_id': task_id
            }
        )
        audio.status = 'finished'
        audio.save()

        return redirect('audio', status=status_url)
    except Exception as e:
        pass

API_KEY = "9gYFg92M.8G32FkSQTmaOpQt8nOX581qkQPPqh1ps"

def get_transcript(request, audio_id=None):
    status_url = request.POST.get('status_url')
    audio = get_object_or_404(Audio, id=audio_id)

    try:
        s2t_request = audio.s2t_request
        print(s2t_request)
    except ObjectDoesNotExist:
        messages.error(request, "STT request topilmadi.")
        return redirect('audio', status=status_url)

    if not s2t_request.task_id:
        messages.error(request, "Task ID mavjud emas.")
        return redirect('audio', status=status_url)

    url = f"https://back.aisha.group/api/v2/stt/get/{s2t_request.task_id}/"
    headers = {'x-api-key': API_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(response.json())
        response.raise_for_status()
        response.raise_for_status()
        data = response.json()
        transcript = data.get('transcript', "No transcript")

        if not transcript:
            messages.warning(request, "Transcript hali tayyor emas.")
            return redirect('audio', status=status_url)

        # Audio transcript update
        if not audio.transcript:
            audio.transcript = transcript
            audio.save(update_fields=['transcript', 'status'])

        # S2TRequest status update
        s2t_request.status = 'finished'
        s2t_request.save(update_fields=['status'])

        messages.success(request, "Transcript muvaffaqiyatli olindi.")

    except requests.exceptions.RequestException as e:
        messages.error(request, f"API so‘rovida xato: {str(e)}")

    except Exception as e:
        messages.error(request, f"Noma’lum xato: {str(e)}")

    return redirect('audio', status=status_url)