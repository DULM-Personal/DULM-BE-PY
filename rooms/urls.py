from django.urls import path
from .views import RoomCreateView

urlpatterns = [
    path("rooms", RoomCreateView.as_view()),
]
