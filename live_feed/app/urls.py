from django.urls import path
from . import views

urlpatterns = [
    # Your existing URLs (keep these)
    path('', views.live_feed, name='live_feed'),
    path('api/metrics/latest/', views.latest_metrics, name='latest_metrics'),
    
    # New API endpoints for standalone apps
    path('api/metrics/publisher/', views.publisher_metrics, name='publisher'),
    path('api/metrics/receiver/', views.receiver_metrics, name='receiver'),
]