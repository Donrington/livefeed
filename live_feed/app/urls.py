from django.urls import path
from . import views

urlpatterns = [
    path('', views.live_feed, name='live_feed'),
    path('api/status/', views.stream_status, name='stream_status'),
    path('settings/', views.settings, name='settings'),# Settings page
    path('analytics/', views.analytics, name='analytics'),# Analytics page
    path('live_stream/', views.live_stream, name='live_stream'),# Live Stream page
]