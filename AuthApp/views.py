from django.shortcuts import render, redirect
from . import forms
from . import models
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from BlogApp.models import BlogPosts
from django.core.paginator import Paginator
from django.conf import settings
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
import os
from django.contrib.auth import views as auth_views
from CodeVisorProject.settings import imagekit
from CodeVisorProject import settings
from PracticeApp.models import *
from JobsApp.models import *

# Create your views here.

def login_user(request):
    form = forms.LoginForm(request.POST)
    if request.user.is_authenticated:
        messages.warning(
            request,
            message=f'You are already logged in!',
            extra_tags='error'
        )
        return redirect('/')
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            attempt = authenticate(
                request,
                username=username,
                password=password
            )
            if attempt:
                login(
                    request,
                    attempt
                )
                messages.success(
                    request,
                    message=f'You are now logged into the website',
                    extra_tags='success'
                )
                return redirect('/auth/dashboard')
            else:
                messages.warning(
                    request,
                    message=f'Invalid Username or password!',
                    extra_tags='error'
                )
        else:
            messages.warning(
                request,
                message=f'Your form has errors!\n{form.errors}',
                extra_tags='error'
            )
    return render(
        request,
        'AuthApp/login.html',
        {
            'form': form,
            'login': True
        }
    )
    
def logout_user(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(
            request,
            message=f'Logout Successful!',
            extra_tags='success'
        )
        return redirect('/auth/login')
    else:
        messages.warning(
            request,
            message=f'You have to login to visit this page',
            extra_tags='error'
        )
        return redirect('/auth/login')
    
def register_user(request):
    form = forms.RegisterForm(request.POST)
    if request.user.is_authenticated:
        messages.warning(
            request,
            message=f'You are already registered on this site!',
            extra_tags='error'
        )
        return redirect('/auth/dashboard') 
    if request.method == 'POST':
        if form.is_valid():
            form_email = form.cleaned_data['email']
            user_query = User.objects.filter(email=form_email).first()
            if user_query:
                messages.warning(
                    request,
                    message=f'This email is already registered with another account! Please try again with a different one',
                    extra_tags='error'
                )
                form.fields['email'].help_text = f'Change this email! It is associated with another account'
                return render(
                    request,
                    'AuthApp/register.html',
                    {
                        'form': form
                    }
                )
            else:
                form.save()
                messages.success(
                    request,
                    message=f'You are now registered in on this site!',
                    extra_tags='success'
                )
                return redirect('/auth/login') 
        else:
            messages.warning(
                request,
                message=f'Your form has errors!\n{form.errors}',
                extra_tags='error'
            )
            return render(
                request,
                'AuthApp/register.html',
                {
                    'form': form
                }
            )
    return render(
        request,
        'AuthApp/register.html',
        {
            'form': form,
            'register': True
        }
    )
    
@login_required(login_url='/auth/login')
def edit_user(request):
    form = forms.CustomUserChangeForm(request.POST or None, instance=request.user)
    if request.method == 'POST':
        if form.is_valid():
            form_email = form.cleaned_data['email']
            email_query = User.objects.filter(email=form_email).exclude(pk=request.user.pk).first()
            if email_query:
                messages.warning(
                    request,
                    message=f'Invalid Email! This email is associated with another account',
                    extra_tags='error'
                )
                return render(
                    request,
                    'AuthApp/edit-user.html',
                    {
                        'form': form
                    }
                )
            else:
                form.save()
                messages.success(
                    request,
                    message=f'Your account is now updated!',
                    extra_tags='success'
                )
                return redirect('/auth/dashboard')  
        else:
            messages.warning(
                request,
                message=f'Your form has errors!\n{form.errors}',
                extra_tags='error'
            )
            return render(
                request,
                'AuthApp/edit-user.html',
                {
                    'form': form
                }
            )
    return render(
        request,
        'AuthApp/edit-user.html',
        {
            'form': form,
            'edit_user': True
        }
    )
    
@login_required(login_url='/auth/login')
def edit_password(request):
    form = forms.CustomEditPasswordForm(request.user, request.POST)
    if request.method == 'POST':
        if form.is_valid():
            user = request.user
            form.save()
            update_session_auth_hash(
                request,
                user
            )
            messages.success(
                request,
                message=f'Your password is updated!',
                extra_tags='success'
            )
            return redirect('/auth/dashboard') 
        else:
            messages.warning(
                request,
                message=f'Your form has errors!\n{form.errors}',
                extra_tags='error'
            )
            return redirect('/auth/edit-password')
    return render(
        request,
        'AuthApp/edit-password.html',
        {
            'form': form,
            'edit_password': True
        }
    )
    
@login_required(login_url='/auth/login')
def delete_user(request):
    form = forms.DeleteConfirmation(request.POST)
    if request.method == 'POST':
        if request.user.is_superuser and request.user.is_staff:
            messages.warning(
                request,
                message=f'Accounts with escalated permissions cannot be deleted!',
                extra_tags='error'
            )
            return redirect('/auth/dashboard')
        if form.is_valid():
            password = form.cleaned_data['password']
            attempt = authenticate(
                request,
                username=request.user.username,
                password=password
            )
            if attempt is not None:
                request.user.delete()
                messages.success(
                    request,
                    message=f'Your account has been deleted successfully!',
                    extra_tags='success'
                )
                return redirect('/')
            else:
                messages.warning(
                    request,
                    message=f'Account deletion not possible due to incorrect password!',
                    extra_tags='error'
                )
                return redirect('/auth/delete-user')
    return render(
        request,
        'AuthApp/delete-user.html',
        {
            'form': form,
            'delete_user': True
        }
    )

from . import models
    
@login_required(login_url='/auth/login')
def create_profile(request):
    check = None
    try:
        check = request.user.profile
    except Exception as error:
        check = None
    if check is not None:
        messages.warning(
            request,
            message=f'Your profile already exists!',
            extra_tags='error'
        )
        return redirect('/auth/dashboard') 
    form = forms.ProfileForm(request.POST, request.FILES)
    if request.method == 'POST':
        if form.is_valid():
            form.instance.user = request.user
            profile = form.save(commit=False)
            if 'profile_pic_url' in request.FILES:
                image = request.FILES['profile_pic_url']
                # print(image)
                temp_image_path = os.path.join(settings.MEDIA_ROOT, f'tempfiles/profile-pictures/{image.name}')
                os.makedirs(os.path.dirname(temp_image_path), exist_ok=True)
                with open(temp_image_path, 'wb+') as temp_file:
                    for chunk in image.chunks():
                        temp_file.write(chunk)
                upload_response = imagekit.upload_file(
                    file=open(
                        temp_image_path, 
                        'rb'
                    ),
                    file_name=image.name,
                    options=UploadFileRequestOptions(
                        folder='/codevisor/profile_pictures/'
                    )
                )
                profile.profile_pic = upload_response.url
                # print('reached if block')
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                models.ImageUpload.objects.create(
                    uploaded_by = request.user,
                    image_url = upload_response.url,
                    image_type = 'ProfilePicture',
                )
            profile.save()
            messages.success(
                request,
                message=f'Your Profile has been created successfully!',
                extra_tags='success'
            )
            return redirect('/auth/dashboard') 
        else:
            messages.warning(
                request,
                message=f'Your form has errors!\n{form.errors}',
                extra_tags='error'
            )
            return render(
                request,
                'AuthApp/create-profile.html',
                {
                    'form': form
                }
            )
    return render(
        request,
        'AuthApp/create-profile.html',
        {
            'form': form,
            'create_profile': True
        }
    )
    
from . import models    

@login_required(login_url='/auth/login')
def edit_profile(request):
    check = None
    try:
        check = request.user.profile
    except Exception as error:
        check = None
    if check is None:
        messages.warning(
            request,
            message=f'You have to create a profile in order to edit it!',
            extra_tags='error'
        )
        return redirect('/auth/create-profile')
    form = forms.ProfileForm(
        request.POST,
        request.FILES,
        instance=request.user.profile
    )
    if request.method == 'POST':
        if form.is_valid():
            profile = form.save(commit=False)
            if 'profile_pic_url' in request.FILES:
                image = request.FILES['profile_pic_url']
                # print(image)
                temp_image_path = os.path.join(settings.MEDIA_ROOT, f'tempfiles/profile-pictures/{image.name}')
                os.makedirs(os.path.dirname(temp_image_path), exist_ok=True)
                with open(temp_image_path, 'wb+') as temp_file:
                    for chunk in image.chunks():
                        temp_file.write(chunk)
                upload_response = imagekit.upload_file(
                    file=open(
                        temp_image_path, 
                        'rb'
                    ),
                    file_name=image.name,
                    options=UploadFileRequestOptions(
                        folder='/codevisor/profile_pictures/'
                    )
                )
                profile.profile_pic = upload_response.url
                # print('reached if block')
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                models.ImageUpload.objects.create(
                    uploaded_by = request.user,
                    image_url = upload_response.url,
                    image_type = 'ProfilePicture',
                )
            profile.save()
            messages.success(
                request,
                message=f'Your Profile has been updated!',
                extra_tags='success'
            )
            return redirect('/auth/dashboard') 
        else:
            messages.warning(
                request,
                message=f'Your form has errors!\n{form.errors}',
                extra_tags='error'
            )
            return render(
                request,
                'AuthApp/edit-profile.html',
                {
                    'form': form
                }
            )
    else:
        form = forms.ProfileForm(
            instance=request.user.profile
        )
        return render(
            request,
            'AuthApp/edit-profile.html',
            {
                'form': form,
                'edit_profile': True
            }
        )
        
        
   

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from PracticeApp.models import CertificationQuizAttempt
from PracticeApp.models import ProblemSubmission # Update to your exact path!

@login_required
def student_analytics_view(request):
    user = request.user
    
    # Grab all passed submissions for this user up front to optimize database memory load
    passed_submissions = ProblemSubmission.objects.filter(
        user=user,
        passed=True
    ).select_related('problem')

    # -------------------------------------------------------------
    # METRIC 1: SKILL FOCUS DOMAINS (PROBLEMS BY CATEGORY)
    # -------------------------------------------------------------
    raw_distribution_map = {}
    difficulty_map = {'easy': 0, 'medium': 0, 'hard': 0}

    for submission in passed_submissions:
        prob = submission.problem
        if prob:
            # Category Label Logic Extraction Fallback
            if hasattr(prob, 'domain') and prob.domain:
                category_name = getattr(prob.domain, 'display_name', str(prob.domain))
            elif hasattr(prob, 'topic_tags') and prob.topic_tags:
                category_name = str(prob.topic_tags).title()
            else:
                category_name = "Core Syntax & Logic"

            raw_distribution_map[category_name] = raw_distribution_map.get(category_name, 0) + 1
            
            # -------------------------------------------------------------
            # METRIC 3: PROBLEM DIFFICULTY DISTRIBUTION (EXTRACTED IN SAME LOOP)
            # -------------------------------------------------------------
            diff_level = getattr(prob, 'difficulty_level', '').lower().strip()
            if diff_level in difficulty_map:
                difficulty_map[diff_level] += 1
            else:
                difficulty_map['easy'] += 1 # Default fallback tier

    # Format Metric 1 arrays
    sorted_metrics = sorted(raw_distribution_map.items(), key=lambda x: x[1], reverse=True)
    domain_labels = [item[0] for item in sorted_metrics]
    domain_counts = [item[1] for item in sorted_metrics]
            
    if not domain_labels:
        domain_labels = ["OOP", "Data Structures", "Databases", "Core Syntax"]
        domain_counts = [0, 0, 0, 0]

    # Format Metric 3 arrays
    difficulty_labels = ['Easy Complexity', 'Medium Tier', 'Hard Challenges']
    difficulty_counts = [difficulty_map['easy'], difficulty_map['medium'], difficulty_map['hard']]

    # -------------------------------------------------------------
    # METRIC 2: CERTIFICATION STATUS MATRIX (STATE COUNTS)
    # -------------------------------------------------------------
    cert_matrix = CertificationQuizAttempt.objects.filter(
        student=user
    ).values('status').annotate(total=Count('id'))
    
    status_tracker = {'pending': 0, 'verified': 0, 'rejected': 0}
    for item in cert_matrix:
        status_key = item['status']
        if status_key in status_tracker:
            status_tracker[status_key] = item['total']

    # -------------------------------------------------------------
    # METRIC 4: AI ASSESSMENT PERFORMANCE SCORE PER DOMAIN
    # -------------------------------------------------------------
    # Calculate average grade percentage achieved grouped by individual tech domains
    score_avg_data = CertificationQuizAttempt.objects.filter(
        student=user
    ).values('domain__display_name').annotate(avg_score=Avg('score_percentage')).order_by('-avg_score')

    score_labels = []
    score_averages = []
    for item in score_avg_data:
        d_name = item['domain__display_name']
        if d_name:
            score_labels.append(f"{d_name} Avg")
            score_averages.append(round(item['avg_score'], 1))

    if not score_labels:
        score_labels = ["Framework Core Baseline"]
        score_averages = [0]

    context = {
        # Graph 1
        'domain_labels': domain_labels,
        'domain_counts': domain_counts,
        # Graph 2
        'cert_pending': status_tracker['pending'],
        'cert_verified': status_tracker['verified'],
        'cert_rejected': status_tracker['rejected'],
        # Graph 3
        'difficulty_labels': difficulty_labels,
        'difficulty_counts': difficulty_counts,
        # Graph 4
        'score_labels': score_labels,
        'score_averages': score_averages,
    }
    return render(request, 'AuthApp/student_analytics.html', context)
  
        
        

from django.db.models import Q # don't dare to remove it from here!        

@login_required(login_url='/auth/login')
def user_dashboard(request):
    user = request.user

    # --- 1. Authored Posts ---
    authored_posts_qs = BlogPosts.objects.filter(author=user).order_by('-pk')
    authored_paginator = Paginator(authored_posts_qs, 3)
    post_page_num = request.GET.get('post_page')
    authored_posts_page = authored_paginator.get_page(post_page_num)

    # --- 2. Liked Posts ---
    liked_posts_qs = BlogPosts.objects.filter(likes=user, hide_post=False).order_by('-pk')
    liked_paginator = Paginator(liked_posts_qs, 4)
    like_page_num = request.GET.get('like_page')
    liked_posts_page = liked_paginator.get_page(like_page_num)

    # --- 3. Algorithm Problems, Solved Badges & DUEL ARENA ---
    is_student = False
    active_tab = 'beginner'
    problems = {'beginner': [], 'intermediate': [], 'advanced': []}
    ai_problems = []
    
    # NEW ARENA VARIABLES
    is_arena_eligible = False 
    suggested_rivals = []
    user_duels = []
    applied_jobs = None
    certification_topics = None
    pending_student_certs = None
    if hasattr(user, 'profile') and user.profile:
        if getattr(user.profile, 'role', '') == 'student': 
            is_student = True
            active_tab = getattr(user.profile, 'skill_level', 'beginner')
            
            # Create a dictionary of {problem_id: earliest_date_solved}
            solved_submissions = ProblemSubmission.objects.filter(user=user, passed=True).order_by('created_at')
            solved_dict = {}
            for sub in solved_submissions:
                if sub.problem_id not in solved_dict:
                    solved_dict[sub.problem_id] = sub.created_at
            
            # --- ELIGIBILITY CHECK ---
            # If the length of solved_dict is >= 5, they have solved 5 DISTINCT problems!
            if len(solved_dict) >= 5:
                is_arena_eligible = True
                
                # Fetch 3 random rivals with the exact same skill level
                suggested_rivals = User.objects.filter(
                    profile__role='student', 
                    profile__skill_level=active_tab
                ).exclude(id=user.id).order_by('?')[:3]

            # Fetch normal problems (excluding AI generated ones)
            problems['beginner'] = list(AlgorithmProblem.objects.filter(difficulty_level='beginner', is_ai_generated=False))
            problems['intermediate'] = list(AlgorithmProblem.objects.filter(difficulty_level='intermediate', is_ai_generated=False))
            problems['advanced'] = list(AlgorithmProblem.objects.filter(difficulty_level='advanced', is_ai_generated=False))
            
            # Inject the solved_date into the objects for the frontend
            for level in ['beginner', 'intermediate', 'advanced']:
                for prob in problems[level]:
                    prob.solved_date = solved_dict.get(prob.id)

            # Fetch Solo AI problems and inject dates
            ai_problems = list(AlgorithmProblem.objects.filter(is_ai_generated=True, generated_by=user).order_by('-created_at'))
            for prob in ai_problems:
                prob.solved_date = solved_dict.get(prob.id)

            # --- FETCH DUEL HISTORY ---
            # Get duels where user is EITHER the challenger OR the opponent
            user_duels = Duel.objects.filter(
                Q(challenger=user) | Q(opponent=user)
            ).select_related('challenger', 'opponent').order_by('-created_at')[:10]
            
            apps_list = JobApplication.objects.filter(applicant=user).select_related('job', 'job__recruiter').order_by('-applied_at')
            
            # Paginate by 3 items per page to keep the layout tight alongside your algorithm lists
            apps_paginator = Paginator(apps_list, 3)
            student_app_page_num = request.GET.get('student_app_page')
            applied_jobs_page = apps_paginator.get_page(student_app_page_num)
            
            # Save the paginated page object to our context variable
            applied_jobs = applied_jobs_page
            all_certification_topics = TechDomain.objects.all().order_by('display_name')

            # Append it into your existing context map dictionary
            certification_topics = all_certification_topics
            pending_student_certs = CertificationQuizAttempt.objects.filter(
                student=user
            ).select_related('domain').order_by('-created_at')

            # Append it safely directly into your existing dashboard context map dictionary
            pending_student_certs = pending_student_certs
    
    jobs = None
    if hasattr(request.user, 'profile') and request.user.profile.role == 'recruiter':
        # 1. Fetch only THEIR jobs, ordered newest first
        job_list = JobPosting.objects.filter(recruiter=request.user).order_by('-created_at')
        
        # 2. Set up Pagination (e.g., 5 jobs per page for a clean UI)
        paginator = Paginator(job_list, 5) 
        page_number = request.GET.get('job_page')
        jobs = paginator.get_page(page_number)
        
    context = {
        'dashboard': True,
        'posts': authored_posts_page,
        'has_posts': authored_posts_qs.exists(),
        'liked_posts': liked_posts_page,
        'has_liked_posts': liked_posts_qs.exists(),
        'is_student': is_student,
        'active_tab': active_tab,
        'problems': problems,
        'ai_problems': ai_problems,
        
        # New Context Variables
        'is_arena_eligible': is_arena_eligible,
        'suggested_rivals': suggested_rivals,
        'user_duels': user_duels,
        'jobs': jobs,
        'applied_jobs': applied_jobs,
        'certification_topics': certification_topics,
        'pending_student_certs': pending_student_certs
    }

    return render(request, 'AuthApp/dashboard.html', context)     



  
       
# forgot password implementation

class CustomPasswordResetView(auth_views.PasswordResetView):
    form_class = forms.CustomPasswordResetForm
    template_name = 'AuthApp/forgot-password/password-reset.html'

class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    form_class = forms.CustomSetPasswordForm
    template_name = 'AuthApp/forgot-password/password-set.html'
    
# handling email duplication error
# @login_required(login_url='/auth/login')
# def email_duplication(request, email):
#     if request.user.is_superuser or request.user.is_staff:
#         email_query = User.objects.filter(email=email).first()
#         if email_query:
#             messages.warning(
#                 request,
#                 message=f'You are using an email that is associated with another user!',
#                 extra_tags='error'
#             )
#             return render(
#                 request,
#                 'AuthApp/email-duplication.html',
#                 {
                    
#                 }
#             )
#         else:
#             messages.warning(
#                 request,
#                 message=f'You can not visit this page without any reason!',
#                 extra_tags='error'
#             )
#             return redirect('/auth/dashboard')
#     else:
#         messages.warning(
#             request,
#             message=f'Invalid Operation! You can not visit this page',
#             extra_tags='error'
#         )
#         return redirect('/auth/dashboard')