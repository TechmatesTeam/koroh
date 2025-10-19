"""
URL configuration for Companies app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, CompanyFollowViewSet, CompanyInsightViewSet

app_name = 'companies'

# Router for API endpoints
router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'follows', CompanyFollowViewSet, basename='companyfollow')
router.register(r'insights', CompanyInsightViewSet, basename='companyinsight')

urlpatterns = [
    path('', include(router.urls)),
]