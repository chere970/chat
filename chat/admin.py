from django.contrib import admin

from .models import Message, PhoneOTP, Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "phone_number", "is_protected", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug", "phone_number")
    list_filter = ("created_at",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("username", "room", "content", "created_at")
    list_filter = ("room", "created_at")
    search_fields = ("username", "content")


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "room", "code", "verification_id", "is_verified", "attempts", "created_at", "expires_at")
    list_filter = ("is_verified", "room", "created_at")
    search_fields = ("phone_number", "code", "verification_id")
    readonly_fields = ("code", "verification_id", "created_at")
