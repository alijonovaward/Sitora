from django.db import models
from django.contrib.auth.models import User
import os


class Profile(models.Model):
    ROLE_CHOICES = (
        ('superadmin', 'SuperAdmin'),
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    total_audio_duration = models.PositiveIntegerField(default=0)
    card_number = models.CharField(max_length=20, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    can_write_text = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} ({self.user.username})"


class Audio(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('finished', 'Finished'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    )
    audio_author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='audio_author')
    transcript_author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='transcript_author')
    duration = models.DecimalField(max_digits=10, decimal_places=1, default=0)

    audio_file = models.FileField(upload_to='audio', null=True, blank=True)
    transcript = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and self.audio_file:
            ext = self.audio_file.name.split('.')[-1]
            new_name = f"audio/audio_{self.pk}.{ext}"

            try:
                old_path = self.audio_file.path
                new_path = os.path.join(os.path.dirname(old_path), f"audio_{self.pk}.{ext}")

                if old_path != new_path:
                    os.rename(old_path, new_path)
                    self.audio_file.name = new_name
                    super().save(update_fields=['audio_file'])
            except Exception:
                pass

    def __str__(self):
        file_name = self.audio_file.name if self.audio_file else "No file"
        return f"{file_name} ({self.audio_author})"
