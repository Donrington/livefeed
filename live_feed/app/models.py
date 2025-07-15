# Add this to your existing app/models.py file

from django.db import models
from django.utils import timezone

class StreamMetrics(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    publisher_fps = models.FloatField()
    receiver_fps = models.FloatField()
    latency_ms = models.FloatField()
    frame_number = models.IntegerField()
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"Frame {self.frame_number} - Latency: {self.latency_ms:.1f}ms"
