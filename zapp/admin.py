from django.contrib import admin
from django.utils.html import format_html

from .models import Profile, Audio, S2TRequest


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_name', 'phone_number', 'card_number', 'can_write_text')
    search_fields = ('user__username', 'full_name', 'phone_number')
    list_filter = ('can_write_text',)


@admin.register(Audio)
class AudioAdmin(admin.ModelAdmin):
    list_display = ('id', 'audio_author', 'transcript_author', 'status', 'duration', 'audio_player', 'transcript', 'created_at')
    search_fields = ('audio_author__username', 'transcript')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'updated_at')

    def audio_player(self, obj):
        if obj.audio_file:
            return format_html(
                '<audio controls style="width:200px;"><source src="{}" type="audio/mpeg"></audio>',
                obj.audio_file.url
            )
        return "No audio"

    audio_player.short_description = "Audio"

@admin.register(S2TRequest)
class S2TRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_id', 'status', 'created_at', 'updated_at')
    search_fields = ('task_id', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
