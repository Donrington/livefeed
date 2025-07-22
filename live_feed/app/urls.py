from django.urls import path
from . import views

urlpatterns = [
    path('', views.live_feed, name='live_feed'),
    path('api/status/', views.stream_status, name='stream_status'),
]