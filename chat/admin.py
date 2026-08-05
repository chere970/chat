from django.contrib import admin

from .models import Message, Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("username", "room", "content", "created_at")
    list_filter = ("room", "created_at")
    search_fields = ("username", "content")
