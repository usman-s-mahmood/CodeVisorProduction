from django.db import models

# Create your models here.
from django.contrib.auth.models import User

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # The 'One-Liner' for the sidebar
    title = models.CharField(max_length=255, default="New Conversation")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

class ChatMessage(models.Model):
    ROLE_CHOICES = [('user', 'User'), ('bot', 'AI')]
    
    session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']