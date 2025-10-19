"""
URL configuration for Jobs app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobViewSet, JobApplicationViewSet, JobSavedViewSet

app_name = 'jobs'

# Router for API endpoints
router = DefaultRouter()
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'applications', JobApplicationViewSet, basename='jobapplication')
router.register(r'saved', JobSavedViewSet, basename='jobsaved')

urlpatterns = [
    path('', include(router.urls)),
]