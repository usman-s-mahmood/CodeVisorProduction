# created manually
from django.urls import path
from . import views

urlpatterns = [
    path('', views.compiler_view, name='py-comp')
]
