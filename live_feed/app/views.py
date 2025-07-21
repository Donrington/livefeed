from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from .models import StreamMetrics
import json



def live_feed(request):
    return render(request, 'live_feed.html')

# def get_metrics(request):
#     """Get latest metrics for dashboard"""
#     latest_metrics = StreamMetrics.objects.first()
#     if latest_metrics:
#         return JsonResponse({
#             'publisher_fps': latest_metrics.publisher_fps,
#             'receiver_fps': latest_metrics.receiver_fps,
#             'latency_ms': latest_metrics.latency_ms,
#             'timestamp': latest_metrics.timestamp.isoformat()
#         })
#     return JsonResponse({'error': 'No metrics available'})




@csrf_exempt
@require_http_methods(["POST"])
def publisher_metrics(request):
    """Receive metrics from standalone publisher"""
    try:
        data = json.loads(request.body)
        
        # Store publisher metrics
        metric = StreamMetrics.objects.create(
            component=data.get('component', 'publisher'),
            publisher_fps=data.get('fps', 0),
            frame_number=data.get('frame_number', 0),
            timestamp_ms=data.get('timestamp_ms', 0),
            receiver_fps=0,
            latency_ms=0
        )
        
        return JsonResponse({
            'status': 'success',
            'metric_id': metric.id
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def receiver_metrics(request):
    """Receive metrics from standalone receiver"""
    try:
        data = json.loads(request.body)
        
        # Find latest publisher metric to update
        latest_metric = StreamMetrics.objects.filter(
            component='publisher'
        ).order_by('-id').first()
        
        if latest_metric:
            # Update with receiver data
            latest_metric.receiver_fps = data.get('fps', 0)
            latest_metric.latency_ms = data.get('latency_ms', 0)
            latest_metric.save()
            
            return JsonResponse({
                'status': 'success',
                'updated_metric_id': latest_metric.id
            })
        else:
            # Create new metric entry
            metric = StreamMetrics.objects.create(
                component='receiver',
                publisher_fps=0,
                receiver_fps=data.get('fps', 0),
                latency_ms=data.get('latency_ms', 0),
                frame_number=0,
                timestamp_ms=0
            )
            
            return JsonResponse({
                'status': 'success',
                'metric_id': metric.id
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

def latest_metrics(request):
    """Get latest metrics for dashboard"""
    try:
        latest_metric = StreamMetrics.objects.order_by('-id').first()
        
        if latest_metric:
            return JsonResponse({
                'publisher_fps': latest_metric.publisher_fps,
                'receiver_fps': latest_metric.receiver_fps,
                'latency_ms': latest_metric.latency_ms,
                'timestamp': latest_metric.timestamp.isoformat()
            })
        else:
            return JsonResponse({
                'error': 'No metrics available'
            })
            
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)