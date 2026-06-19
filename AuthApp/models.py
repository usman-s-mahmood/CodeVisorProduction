from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )
    about_user = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    social_link = models.URLField(
        null=True,
        blank=True
    )
    
    profile_pic = models.URLField(
        null=True,
        blank=True
    )
    
    role = models.CharField ( # student or recruiter
        max_length=50,
        default='student',
        null=False,
        blank=False
    )
    
    skill_level = models.CharField(
        max_length=100,
        default='beginner',
        null=False,
        blank=False
    )
    
    target_role = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    
    interests = models.JSONField(
        default=list,
        blank=True
    )
    elo_score = models.IntegerField(
        null=True,
        blank=True,
        default=0
    )
    
    
    def get_absolute_url(self):
        return (self.profile_pic)
    
    def __str__(self):
        return (self.user.username)
    
class ImageUpload(models.Model):
    uploaded_by = models.ForeignKey(
        User,
        blank=False,
        null=False,
        on_delete=models.DO_NOTHING
    )
    image_url = models.URLField(
        blank=False,
        null=False
    )
    image_type = models.CharField(
        max_length=250,
        blank=False,
        null=False
    )
    uploaded_on = models.DateTimeField(
        auto_now_add=True
    )
    
    def __str__(self):
        return f'{self.uploaded_by.username} | {self.image_type} | {self.uploaded_on}'    
    
class TestingModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    added_on = models.DateTimeField(auto_now_add=True)