import random
import string

from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Room(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=64, unique=True)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Phone number required to join this room (E.164 format). Leave blank for open rooms.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:64]
        super().save(*args, **kwargs)

    @property
    def is_protected(self):
        return bool(self.phone_number)


class Message(models.Model):
    room = models.ForeignKey(Room, related_name="messages", on_delete=models.CASCADE)
    username = models.CharField(max_length=32)
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.username}: {self.content[:40]}"


class PhoneOTP(models.Model):
    """Stores OTP codes sent for room access verification."""

    phone_number = models.CharField(max_length=20)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="otps")
    code = models.CharField(max_length=6, blank=True, default="")
    verification_id = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"OTP {self.code} for {self.phone_number} → {self.room.name}"

    def save(self, *args, **kwargs):
        if not self.code and not self.verification_id:
            self.code = "".join(random.choices(string.digits, k=6))
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=5)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_expired and not self.is_verified and self.attempts < 5
