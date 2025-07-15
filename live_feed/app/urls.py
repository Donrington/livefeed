from django.urls import path
from . import views

urlpatterns = [
    path('', views.live_feed, name='live_feed'),
    path('api/metrics/latest/', views.get_metrics, name='get_metrics'),

]