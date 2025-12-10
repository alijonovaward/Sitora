from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("audio/<str:status>", views.audio_view, name="audio"),
    path('upload_audio/', views.upload_audio, name='upload_audio'),
]
