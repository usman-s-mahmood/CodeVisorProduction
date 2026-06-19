# created manually
from django.urls import path
from . import views

urlpatterns = [
    path('create-job/', views.create_job_view, name='create_job'),
    # yourdomain.com/marketplace/edit-job/5/
    path('edit-job/<int:job_id>/', views.edit_job_view, name='edit_job'),
    # yourdomain.com/marketplace/delete-job/5/
    path('delete-job/<int:job_id>/', views.delete_job_view, name='delete_job'),
    # yourdomain.com/marketplace/board/
    path('board/', views.job_board_view, name='job_board'),
    # yourdomain.com/marketplace/job/5/
    path('job/<int:job_id>/', views.job_detail_view, name='job_detail'),
    # yourdomain.com/marketplace/job/5/apply/
    path('job/<int:job_id>/apply/', views.apply_job_view, name='apply_job'),
    # yourdomain.com/marketplace/job/5/applicants/
    path('job/<int:job_id>/applicants/', views.view_applicants_view, name='view_applicants'),
    # yourdomain.com/marketplace/application/5/profile/
    path('application/<int:application_id>/profile/', views.applicant_profile_view, name='applicant_profile'),
    path('search/', views.search_jobs_view, name='search_jobs'),
]
