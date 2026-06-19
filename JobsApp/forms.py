# created manually!
from django import forms
from .models import *

class JobPostingForm(forms.ModelForm):
    title = forms.CharField(
        label="Job Title",
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-3', 
            'placeholder': 'e.g., Senior Backend Engineer'
        })
    )
    
    employment_type = forms.ChoiceField(
        choices=JobPosting.EMPLOYMENT_TYPES,
        label="Employment Type",
        widget=forms.Select(attrs={
            'class': 'form-select mb-3'
        })
    )
    
    company_name = forms.CharField(
        label="Company Name*",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-3', 
            'placeholder': 'Name of Company'
        })
    )
    
    location = forms.CharField(
        label="Location (Optional)",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-3', 
            'placeholder': 'e.g., Remote or Lahore, PK'
        })
    )
    
    salary_range = forms.CharField(
        label="Salary Range (Optional)",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-3', 
            'placeholder': 'e.g., $80k - $100k or Rs. 150k'
        })
    )
    
    # --- THE TRIX EDITOR MAGIC ---
    # We hide the native Django field. Trix will use this ID to inject the HTML payload.
    description = forms.CharField(
        label="Job Description",
        widget=forms.HiddenInput(attrs={
            'id': 'trix_description_input'
        })
    )
    
    is_active = forms.BooleanField(
        label="Job is Currently Active",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input mb-3',
            'role': 'switch'  # Makes it look like a sleek toggle switch in Bootstrap 5
        })
    )

    class Meta:
        model = JobPosting
        fields = [
            'title', 
            'employment_type', 
            'company_name', 
            'location', 
            'salary_range', 
            'description', 
            'is_active'
        ]
        
class JobApplicationForm(forms.ModelForm):
    cv = forms.FileField(
        label="Upload your CV / Resume (Required)",
        help_text="Strictly limited to .pdf, .doc, and .docx formats.",
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control mb-3',
            'accept': '.pdf,.doc,.docx'
        })
    )
    
    cover_letter = forms.CharField(
        label="Cover Letter (Optional)",
        required=False,
        widget=forms.HiddenInput(attrs={
            'id': 'trix_cover_letter_input' # Unique ID for the student form
        })
    )
    
    relevant_project_url = forms.URLField(
        label="Relevant Project URL (Optional)",
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control mb-3',
            'placeholder': 'https://github.com/yourusername/awesome-project'
        })
    )
    
    availability = forms.ChoiceField(
        choices=JobApplication.AVAILABILITY_CHOICES,
        label="When can you start?",
        widget=forms.Select(attrs={
            'class': 'form-select mb-3'
        })
    )

    class Meta:
        model = JobApplication
        fields = ['cv', 'cover_letter', 'relevant_project_url', 'availability']
        


        
        
        
        
        
        