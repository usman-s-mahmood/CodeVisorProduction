from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
# Create your models here.


class JobPosting(models.Model):
    EMPLOYMENT_TYPES = (
        ('full_time', 'Full-Time'),
        ('part_time', 'Part-Time'),
        ('contract', 'Contract'),
        ('remote', 'Remote'),
        ('internship', 'Internship'),
    )

    # The recruiter who created the job
    recruiter = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='job_postings'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    company_name = models.CharField(
        max_length=255,
        default='unknown',
        null=True,
        blank=True
    )
    
    employment_type = models.CharField(
        max_length=50, 
        choices=EMPLOYMENT_TYPES, 
        default='full_time'
    )
    
    # Optional but highly recommended fields for a real job board
    location = models.CharField(max_length=255, blank=True, null=True, help_text="e.g., Lahore, PK or Remote")
    salary_range = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., $50k - $70k or Rs. 100k")
    
    # Control flags and timestamps
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at'] # Automatically sorts newest jobs first

    def __str__(self):
        return f"{self.title} | Posted by {self.recruiter.username}"
    
    


class JobApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('interview', 'Interview Scheduled'),
        ('rejected', 'Rejected'),
    )

    applicant = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='job_applications'
    )
    
    job = models.ForeignKey(
        'JobPosting', 
        on_delete=models.CASCADE, 
        related_name='applications'
    )
    
    cv = models.FileField(
        upload_to='cv_uploads/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        help_text="Upload your CV. Only PDF, DOC, and DOCX files are allowed."
    )
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    
    applied_at = models.DateTimeField(auto_now_add=True)
    
    # 2. The Cover Letter
    cover_letter = models.TextField(
        blank=True, 
        null=True,
        help_text="Introduce yourself and explain why you are a great fit for this specific role."
    )
    
    # 3. Job-Specific Portfolio Link
    relevant_project_url = models.URLField(
        blank=True, 
        null=True,
        help_text="Link to a specific GitHub repo or project relevant to this job."
    )
    
    # 4. Availability
    AVAILABILITY_CHOICES = (
        ('immediate', 'Immediately'),
        ('two_weeks', 'In 2 Weeks'),
        ('one_month', 'In 1 Month'),
        ('student', 'Currently Enrolled (Part-time only)'),
    )
    availability = models.CharField(
        max_length=50,
        choices=AVAILABILITY_CHOICES,
        default='immediate'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevents a user from applying to the exact same job more than once
        unique_together = ('applicant', 'job') 
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant.username} applied to {self.job.title}"


    
    
    