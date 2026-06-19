from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('session/<int:session_id>/', views.get_session_history, name='get_history'),
    path('search/', views.search_chats, name='search_chats'),
    path('career-coach/', views.career_coach_home_view, name='career_coach_home'),
    path('career-coach/api/chat/', views.career_coach_api_view, name='career_coach_api'),
]