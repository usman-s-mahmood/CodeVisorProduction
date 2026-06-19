from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required(login_url='/auth/login')
def compiler_view(request):
    return render(
        request, 
        'PyCompilerApp/py-index.html'
    )
    
