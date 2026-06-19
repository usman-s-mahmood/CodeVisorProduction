from django.contrib import admin
from . import models

# Register your models here.

admin.site.register(models.ChatMessage)
admin.site.register(models.ChatSession)