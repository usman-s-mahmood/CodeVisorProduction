# created manually
from django.urls import path
from . import views

urlpatterns = [
    path('solve/<slug:slug>/', views.problem_solve_view, name='problem_solve'),
    path('api/evaluate/<slug:slug>/', views.submit_code_evaluation, name='submit_evaluation'),
    path('api/generate-ai/', views.generate_ai_problem, name='generate_ai_problem'),
    path('duel/create/', views.create_duel, name='create_duel'),
    path('duel/accept/<int:duel_id>/', views.accept_duel, name='accept_duel'),
    path('duel/submit/<int:duel_id>/', views.submit_duel_code, name='submit_duel_code'),
    path('duel/arena/<int:duel_id>/', views.duel_arena_view, name='duel_arena_view'),
    path('certifications/add-topic/', views.add_topic_view, name='add_topic'),
    path('certifications/generate/<int:domain_id>/', views.create_quiz_view, name='create_quiz'),
    path('certifications/quiz/<int:attempt_id>/', views.take_certification_quiz_view, name='take_certification_quiz'),
    path('certifications/quiz/<int:attempt_id>/submit/', views.evaluate_quiz_view, name='evaluate_quiz'),
    path('certifications/staff-queue/', views.staff_queue_view, name='staff_queue'),
    path('certifications/staff-review/<int:attempt_id>/', views.staff_detail_review_view, name='staff_detail_review'),
    # 1. Secure stream path enabling dynamic, protected student-only certificate PDF creation
    path('certifications/download/<int:attempt_id>/', views.download_certification_pdf_view, name='download_certification_pdf'),

    # 2. Open public gateway enabling unauthenticated certificate audits (Pearson structure matching)
    path('certifications/verify/', views.verify_certification_public_view, name='verify_certification_public'),
]