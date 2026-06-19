from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.core.paginator import Paginator
# Create your views here.

@login_required
def create_job_view(request):
    # SECURITY GATE: Boot the user out if they aren't a recruiter
    print(request.user.profile.role)
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'recruiter':
        messages.error(request, "Access Denied: Only verified recruiters can post jobs.", extra_tags='error')
        return redirect('/auth/dashboard') # Redirecting back to your AuthApp dashboard

    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            # Pause the save so we can inject the logged-in user as the recruiter
            new_job = form.save(commit=False)
            new_job.recruiter = request.user
            new_job.save()
            
            messages.success(request, f"Success! '{new_job.title}' is now live on the board.", extra_tags='success')
            return redirect('/auth/dashboard')
    else:
        # If it's a GET request, just hand them a blank form
        form = JobPostingForm()

    context = {
        'form': form,
    }
    return render(request, 'JobsApp/create_job.html', context)


@login_required
def edit_job_view(request, job_id):
    # 1. Fetch the specific job from the database, or throw a clean 404 if it doesn't exist
    job = get_object_or_404(JobPosting, id=job_id)
    
    # 2. SECURITY GATE 1: Are they a recruiter?
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'recruiter':
        messages.error(request, "Access Denied: Only verified recruiters can edit jobs.", extra_tags='error')
        return redirect('/auth/dashboard')
        
    # 3. SECURITY GATE 2: Do they OWN this specific job? (The ultimate flex)
    if job.recruiter != request.user:
        messages.error(request, "Security Alert: You cannot edit a job posted by another company.", extra_tags='error')
        return redirect('/auth/dashboard')

    # 4. Handle the form submission
    if request.method == 'POST':
        # Pass the existing job instance so Django knows to UPDATE, not CREATE
        form = JobPostingForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f"Success! '{job.title}' has been updated.", extra_tags='success')
            return redirect('/auth/dashboard')
    else:
        # GET request: Pre-fill the form with the existing job data
        form = JobPostingForm(instance=job)

    context = {
        'form': form,
        'job': job, # Pass the job to the template in case we need its ID or Title
    }
    return render(request, 'JobsApp/edit_job.html', context)

@login_required
def delete_job_view(request, job_id):
    # 1. Fetch the job
    job = get_object_or_404(JobPosting, id=job_id)
    
    # 2. SECURITY GATE 1: Are they a recruiter?
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'recruiter':
        messages.error(request, "Access Denied: Only verified recruiters can delete jobs.", extra_tags='error')
        return redirect('/auth/dashboard')
        
    # 3. SECURITY GATE 2: Do they OWN this specific job?
    if job.recruiter != request.user:
        messages.error(request, "Security Alert: You cannot delete a job posted by another company.", extra_tags='error')
        return redirect('/auth/dashboard')

    # 4. Handle the deletion confirmation
    if request.method == 'POST':
        job_title = job.title # Save the title to memory before we destroy the object
        job.delete()
        messages.success(request, f"Success! '{job_title}' has been permanently deleted.", extra_tags='success')
        return redirect('/auth/dashboard')

    # 5. GET request: Show the confirmation page
    context = {
        'job': job,
    }
    return render(request, 'JobsApp/delete_job.html', context)

from django.db.models import Q # don't remove this line from here!!!

def job_board_view(request):
    # 1. Base Query: Only show active jobs. 
    # select_related('recruiter') makes it insanely fast by grabbing the user data in the same query.
    jobs_qs = JobPosting.objects.filter(is_active=True).select_related('recruiter')

    # 2. Search Logic
    search_query = request.GET.get('q', '')
    if search_query:
        # Search by Title OR Location (case-insensitive)
        jobs_qs = jobs_qs.filter(
            Q(title__icontains=search_query) | 
            Q(location__icontains=search_query)
        )

    # 3. Pagination (e.g., 10 jobs per page for the global board)
    paginator = Paginator(jobs_qs, 5) 
    page_number = request.GET.get('page')
    jobs = paginator.get_page(page_number)

    context = {
        'jobs': jobs,
        'search_query': search_query, # Pass this back to keep the search bar populated
    }
    return render(request, 'JobsApp/job_board.html', context)

def job_detail_view(request, job_id):
    # Fetch the specific job, throw a 404 if someone tries to guess a random ID
    job = get_object_or_404(JobPosting, id=job_id)
    
    context = {
        'job': job,
    }
    return render(request, 'JobsApp/job_detail.html', context)

@login_required
def apply_job_view(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id)

    # 1. SECURITY GATE: Are they a student?
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'student':
        messages.error(request, "Access Denied: Only developers can apply for jobs.", extra_tags='error')
        return redirect(f'/marketplace/job/{job.id}/') 

    # 2. LOGIC GATE: Is the job still active?
    if not job.is_active:
        messages.error(request, "This position is no longer accepting applications.", extra_tags='error')
        return redirect(f'/marketplace/job/{job.id}/')

    # 3. UX GATE: Did they already apply? (Stop them before they even see the form)
    if JobApplication.objects.filter(applicant=request.user, job=job).exists():
        messages.error(request, "You have already applied for this role. Check your dashboard for updates!", extra_tags='error')
        return redirect(f'/marketplace/job/{job.id}/')

    if request.method == 'POST':
        # THE FLEX: You MUST pass request.FILES here to catch the PDF CV
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Pause the save to inject the user and the job
                application = form.save(commit=False)
                application.applicant = request.user
                application.job = job
                application.save()
                
                messages.success(request, f"Boom! Your application for '{job.title}' was successfully submitted.", extra_tags='success')
                # Route them back to the board to keep hunting
                return redirect('/marketplace/board/') 
                
            except IntegrityError:
                # The ultimate database safety net
                messages.error(request, "Duplicate application detected.", extra_tags='error')
                return redirect(f'/marketplace/job/{job.id}/')
    else:
        form = JobApplicationForm()

    context = {
        'form': form,
        'job': job,
    }
    return render(request, 'JobsApp/apply_job.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import JobPosting, JobApplication # Make sure JobApplication is imported!


@login_required
def view_applicants_view(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id)
    
    # 1. SECURITY GATES
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'recruiter':
        messages.error(request, "Access Denied: Only recruiters can view applicant tracking.", extra_tags='error')
        return redirect('/auth/dashboard')
        
    if job.recruiter != request.user:
        messages.error(request, "Security Alert: You do not own this job posting.", extra_tags='error')
        return redirect('/auth/dashboard')

    # 2. HANDLE STATUS UPDATES
    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        new_status = request.POST.get('new_status')
        
        if app_id and new_status:
            app_to_update = get_object_or_404(JobApplication, id=app_id, job=job)
            app_to_update.status = new_status
            app_to_update.save()
            
            messages.success(request, f"Status updated to '{app_to_update.get_status_display()}'.", extra_tags='success')
            return redirect(f'/marketplace/job/{job.id}/applicants/')

    # 3. PAGINATED FETCH (The clean, optimized way)
    # Fetch all applications, pre-selecting user profiles to avoid N+1 database hits
    applicant_list = job.applications.all().select_related('applicant', 'applicant__profile').order_by('-applied_at')
    
    # Paginate by 5 applicants per page for a beautifully scannable dashboard layout
    paginator = Paginator(applicant_list, 5) 
    applicant_page_num = request.GET.get('applicant_page')
    applications = paginator.get_page(applicant_page_num)

    context = {
        'job': job,
        'applications': applications, # This is now a paginated Page object, not a raw QuerySet
        'status_choices': JobApplication.STATUS_CHOICES,
    }
    return render(request, 'JobsApp/view_applicants.html', context)




from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import JobApplication

@login_required
def applicant_profile_view(request, application_id):
    # 1. Fetch the exact application
    application = get_object_or_404(JobApplication, id=application_id)
    job = application.job
    applicant = application.applicant
    
    # 2. SECURITY GATES
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'recruiter':
        messages.error(request, "Access Denied: Only recruiters can view applicant profiles.", extra_tags='error')
        return redirect('/auth/dashboard')
        
    if job.recruiter != request.user:
        messages.error(request, "Security Alert: You do not own this job posting.", extra_tags='error')
        return redirect('/auth/dashboard')

    # 3. HANDLE STATUS UPDATES (If they change it from this page)
    if request.method == 'POST':
        new_status = request.POST.get('new_status')
        if new_status:
            application.status = new_status
            application.save()
            messages.success(request, f"Status updated to '{application.get_status_display()}' for {applicant.username}.", extra_tags='success')
            return redirect(f'/marketplace/job/{job.id}/applicants/')

    # 4. FETCH ALGORITHM STATS (Assuming ProblemSubmission is imported or accessible)
    # This counts how many distinct problems this specific user has passed
    from PracticeApp.models import ProblemSubmission # Update this import path to wherever your model lives!
    problems_solved_count = ProblemSubmission.objects.filter(user=applicant, passed=True).values('problem').distinct().count()
    print(applicant.profile.profile_pic)
    
    # 🌟 5. NEW CROSS-APP COUPLING: Fetch Verified CodeVisor Certifications
    from PracticeApp.models import CertificationQuizAttempt
    verified_certifications = CertificationQuizAttempt.objects.filter(
        student=applicant,
        status='verified'
    ).select_related('domain', 'reviewed_by').order_by('-updated_at')
    context = {
        'application': application,
        'job': job,
        'applicant': applicant,
        'profile': applicant.profile,
        'problems_solved_count': problems_solved_count,
        'status_choices': JobApplication.STATUS_CHOICES,
        'verified_certifications': verified_certifications,
    }
    return render(request, 'JobsApp/applicant_profile.html', context)

from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import JobPosting

def search_jobs_view(request):
    # 1. Grab the search term
    search_query = request.GET.get('q', '').strip()
    
    # 2. Safety Catch: If the search button was clicked with no input, redirect to global board
    if not search_query:
        return redirect('JobsApp:job_board')

    # 3. Dedicated Search Filtering
    search_results = JobPosting.objects.filter(
        Q(is_active=True) & (
            Q(title__icontains=search_query) | 
            Q(location__icontains=search_query) |
            Q(employment_type__icontains=search_query)
        )
    ).select_related('recruiter').order_by('-created_at')

    # 4. Strict Pagination for Search Results (10 entries per page)
    paginator = Paginator(search_results, 5)
    page_number = request.GET.get('page')
    jobs = paginator.get_page(page_number)

    context = {
        'jobs': jobs,
        'search_query': search_query,
    }
    # Rendering a dedicated search results template file
    return render(request, 'JobsApp/search_results.html', context)

























