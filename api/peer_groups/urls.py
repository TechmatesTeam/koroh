"""
URL configuration for peer groups app.

This module defines the URL patterns for peer group API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PeerGroupViewSet, GroupPostViewSet, GroupCommentViewSet

app_name = 'peer_groups'

# Main router for peer groups
router = DefaultRouter()
router.register(r'groups', PeerGroupViewSet, basename='peergroup')

# Additional URL patterns for nested resources
urlpatterns = [
    path('', include(router.urls)),
    
    # Group posts endpoints
    path('groups/<slug:group_slug>/posts/', 
         GroupPostViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='group-posts-list'),
    path('groups/<slug:group_slug>/posts/<int:pk>/', 
         GroupPostViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), 
         name='group-posts-detail'),
    
    # Post comments endpoints
    path('groups/<slug:group_slug>/posts/<int:post_pk>/comments/', 
         GroupCommentViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='post-comments-list'),
    path('groups/<slug:group_slug>/posts/<int:post_pk>/comments/<int:pk>/', 
         GroupCommentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), 
         name='post-comments-detail'),
]