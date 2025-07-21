from django.db import models
from django.utils import timezone

class StreamMetrics(models.Model):
    component = models.CharField(max_length=50, default='publisher')
    timestamp = models.DateTimeField(default=timezone.now)
    publisher_fps = models.FloatField(default=0)
    receiver_fps = models.FloatField(default=0)
    latency_ms = models.FloatField(default=0)
    frame_number = models.IntegerField(default=0)
    timestamp_ms = models.BigIntegerField(default=0)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.component} - Frame {self.frame_number} - Latency: {self.latency_ms:.1f}ms"
