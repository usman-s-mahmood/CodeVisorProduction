from django.contrib import admin
from django.urls import path, include
from decouple import config
from django.conf import settings
from django.conf.urls.static import static
import BlogApp.views as blog_views
import django.conf.urls as conf_urls

urlpatterns = [
    path(f'{config('ADMIN_URL', cast=str)}/', admin.site.urls),
    path('auth/', include('AuthApp.urls')),
    path('', include('BlogApp.urls'), name='index'),
    path('ai/', include('AIChatbotApp.urls')),
    path('py-comp', include('PyCompilerApp.urls')),
    path('practice/', include('PracticeApp.urls')),
    path('marketplace/', include('JobsApp.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
admin.site.site_header = 'CodeVisor'
admin.site.index_title = 'Code Visor Admin Panel'
admin.site.site_title = 'CMS Admin Panel'

conf_urls.handler404 = blog_views.not_found
conf_urls.handler500 = blog_views.server_error
conf_urls.handler403 = blog_views.forbiden_error



    
    
