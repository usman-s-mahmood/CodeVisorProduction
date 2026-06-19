# created manullay!
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from . import models

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your registered username'
            }
        ),
        label='Your registered username'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs = {
                'class': 'form-control',
                'placeholder': 'Enter your specified password'
            }
        ),
        label='Your password'
    )
    
class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email'
            }
        ),
        label='Your personal Email'
    )
    first_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name'
            }
        ),
        label='Enter your first name'
    )
    last_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your last name'
            }
        ),
        label='Enter your last name'
    )
    usable_password = None # for avoiding LDAP for front end users
    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2',
        )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['placeholder'] = 'Enter your password'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm your password'
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'Enter your username'
        self.fields['password1'].label = 'Enter your password'
        self.fields['password2'].label = 'Confirm your password'
        self.fields['username'].label = 'Enter your username'
        
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email'
        )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('id_password_helptext', None)
        self.fields['first_name'].widget.attrs['class'] = 'form-control'
        self.fields['first_name'].widget.attrs['placeholder'] = 'first name'
        self.fields['last_name'].widget.attrs['class'] = 'form-control'
        self.fields['last_name'].widget.attrs['placeholder'] = 'last name'
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'username'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['placeholder'] = 'email'
        self.fields['first_name'].label = 'Enter your first name'
        self.fields['last_name'].label = 'Enter your last name'
        self.fields['username'].label = 'Enter your username'
        self.fields['email'].label = 'Enter your email'
        
        self.fields['password'].label = 'Password Change form'
        self.fields['password'].help_text = 'Click Here for password <a href="/auth/edit-password">change</a>'
        
class CustomEditPasswordForm(PasswordChangeForm):
    class Meta:
        model = User
        fields = (
            'old_password',
            'new_password1',
            'new_password2',
        )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs['class'] = 'form-control'
        self.fields['old_password'].widget.attrs['placeholder'] = 'Your Current Password'
        self.fields['old_password'].label = 'Enter your Current Password'
        
        self.fields['new_password1'].widget.attrs['class'] = 'form-control'
        self.fields['new_password1'].widget.attrs['placeholder'] = 'Your New Password'
        self.fields['new_password1'].label = 'Enter your New Password'
        
        self.fields['new_password2'].widget.attrs['class'] = 'form-control'
        self.fields['new_password2'].widget.attrs['placeholder'] = 'Confirm New Password'
        self.fields['new_password2'].label = 'Confirm your New Password'
        
class DeleteConfirmation(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Confirm your password before account deletion'
            }
        ),
        label='Enter your current password'
    )


class ProfileForm(forms.ModelForm):
    ROLE_CHOICES = (
        ('student', 'Student / Developer'),
        ('recruiter', 'Recruiter / Employer'),
    )
    
    SKILL_CHOICES = (
        ('beginner', 'Beginner (0-6 months)'),
        ('intermediate', 'Intermediate (1-2 years)'),
        ('advanced', 'Advanced (2+ years)'),
    )

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select mb-3', 'id': 'id_role'}),
        label="Select Your Role"
    )

    skill_level = forms.ChoiceField(
        choices=SKILL_CHOICES,
        required=False,  # False because recruiters don't need this
        widget=forms.Select(attrs={'class': 'form-select mb-3 student-field'}),
        label="Your Skill Level (Students Only)"
    )

    target_role = forms.CharField(
        required=False, # False because recruiters don't need this
        widget=forms.TextInput(attrs={'class': 'form-control mb-3 student-field', 'placeholder': 'e.g., Backend Developer'}),
        label="Target Career Role (Students Only)"
    )

    interests = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control mb-3 student-field', 'placeholder': 'e.g., Python, Django, React'}),
        label="Your Interests (Comma separated)"
    )

    profile_pic_url = forms.ImageField(
        label='Your Profile Picture (optional)',
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        widget=forms.FileInput(attrs={'class': 'form-control mb-3'})
    )
    
    about_user = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control mb-3', 'placeholder': 'About yourself in 1000 characters', 'rows': 4}),
        label='Write about yourself (required)',
        required=True
    )
    
    social_link = forms.URLField(
        widget=forms.URLInput(attrs={'class': 'form-control mb-3', 'placeholder': 'Your social media handle (optional)'}),
        label='Your social media handle (optional)',
        required=False
    )

    class Meta:
        model = models.Profile
        fields = (
            'role',
            'skill_level',
            'target_role',
            'interests',
            'about_user',
            'profile_pic_url',
            'social_link',
        )

        # SECURE FIELDS AND FORMAT DATA ON EDIT
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        
        # Check if the form is updating an existing profile
        if self.instance and self.instance.pk:
            # 1. Lock the role field
            self.fields['role'].disabled = True
            self.fields['role'].help_text = "You cannot change your role after creating your profile."
            
            # 2. Lock the skill_level field
            # self.fields['skill_level'].disabled = True # CAUTIOUS UPDATE!
            self.fields['skill_level'].help_text = "Your skill level upgrades automatically as you solve coding challenges."

            # 3. Fix the ugly brackets for the interests field
            # Check if interests exist and is actually a list
            if self.instance.interests and isinstance(self.instance.interests, list):
                # Convert the Python list back into a clean comma-separated string
                self.initial['interests'] = ', '.join(self.instance.interests)


    # MAGIC MVP HACK: Handle the logic so the database doesn't crash
    def clean(self):
        cleaned_data = super().clean()
        
        # Safety checks: Fetch from instance if fields are disabled during edit
        role = cleaned_data.get('role')
        if not role and self.instance and self.instance.pk:
            role = self.instance.role

        skill_level = cleaned_data.get('skill_level')
        if not skill_level and self.instance and self.instance.pk:
            skill_level = self.instance.skill_level
            
        interests_string = cleaned_data.get('interests', '')

        # 1. Convert the comma-separated string into a JSON list for the database
        if interests_string and isinstance(interests_string, str):
            cleaned_data['interests'] = [x.strip() for x in interests_string.split(',') if x.strip()]
        elif not interests_string:
            cleaned_data['interests'] = []

        # 2. If it's a recruiter, fill the mandatory student fields with dummy data 
        if role == 'recruiter':
            cleaned_data['skill_level'] = 'N/A'
            cleaned_data['target_role'] = 'Recruiter'
            cleaned_data['interests'] = []

        return cleaned_data

    

# forgot password forms

class CustomPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['email'].label = 'Enter your registered email'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter your email'


class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs['class'] = 'form-control'
        self.fields['new_password1'].widget.attrs['placeholder'] = 'Enter your new password'
        self.fields['new_password1'].label = 'Your New Password'
        
        self.fields['new_password2'].widget.attrs['class'] = 'form-control'
        self.fields['new_password2'].widget.attrs['placeholder'] = 'Confirm your new password'
        self.fields['new_password2'].label = 'Confirm New Password'
