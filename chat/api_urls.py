"""
API URL patterns — mounted at /api/ in the main urls.py.
"""
from django.urls import path

from . import api_views

urlpatterns = [
    path("rooms/", api_views.room_list, name="api_room_list"),
    path("rooms/<slug:room_slug>/", api_views.room_detail, name="api_room_detail"),
]
