from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from .models import StreamMetrics
import json



def live_feed(request):
    return render(request, 'live_feed.html')

def get_metrics(request):
    # Get latest metrics for dashboard
    latest_metrics = StreamMetrics.objects.first()
    if latest_metrics:
        return JsonResponse({
            'publisher_fps': latest_metrics.publisher_fps,
            'receiver_fps': latest_metrics.receiver_fps,
            'latency_ms': latest_metrics.latency_ms,
            'timestamp': latest_metrics.timestamp.isoformat()
        })
    return JsonResponse({'error': 'No metrics available'})