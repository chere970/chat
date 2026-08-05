from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("name/", views.set_display_name, name="set_display_name"),
    path("rooms/create/", views.create_room, name="create_room"),
    path("rooms/<slug:room_slug>/", views.room, name="room"),
]
