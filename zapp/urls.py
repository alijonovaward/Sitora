from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("audio/<str:status>", views.audio_view, name="audio"),
    path('upload_audio/', views.upload_audio, name='upload_audio'),

    path('audio/<int:audio_id>/update_status/', views.update_audio_status, name='update_audio_status'),
    path('transcript/<int:audio_id>/', views.add_transcript, name='add_transcript'),
]
