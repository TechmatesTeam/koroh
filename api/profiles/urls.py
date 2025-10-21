"""
URL configuration for profiles app.

This module defines URL patterns for profile-related API endpoints.
"""

from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    # Profile CRUD endpoints
    path('me/', views.ProfileDetailView.as_view(), name='detail'),
    path('create/', views.ProfileCreateView.as_view(), name='create'),
    path('update/', views.ProfileUpdateView.as_view(), name='update'),
    
    # CV upload endpoint
    path('upload-cv/', views.CVUploadView.as_view(), name='upload-cv'),
    
    # Public profile endpoint
    path('public/<int:user_id>/', views.ProfilePublicView.as_view(), name='public'),
    
    # Skill management endpoints
    path('skills/add/', views.add_skill, name='add-skill'),
    path('skills/remove/', views.remove_skill, name='remove-skill'),
    
    # Profile statistics endpoint
    path('stats/', views.profile_stats, name='stats'),
    
    # CV analysis endpoints
    path('cv/analyze/', views.analyze_cv, name='analyze-cv'),
    path('cv/metadata/', views.cv_metadata, name='cv-metadata'),
    
    # Portfolio generation endpoints
    path('generate-portfolio/', views.generate_portfolio, name='generate-portfolio'),
    path('portfolios/', views.list_portfolios, name='list-portfolios'),
    path('portfolios/<str:portfolio_id>/', views.update_portfolio, name='update-portfolio'),
]