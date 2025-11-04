"""
Profile views for Koroh platform.

This module defines API views for profile management including
CRUD operations, CV upload, and profile picture handling.
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

from .models import Profile
from .serializers import (
    ProfileSerializer,
    ProfileCreateSerializer,
    ProfileUpdateSerializer,
    CVUploadSerializer,
    ProfilePublicSerializer
)
from .services import CVProcessingService, CVStorageService
from koroh_platform.permissions import (
    IsProfileOwner,
    SecureFileUploadPermission,
    IsAnonymousOrAuthenticated,
    log_permission_denied
)

logger = logging.getLogger('koroh_platform.security')

User = get_user_model()


class ProfileDetailView(generics.RetrieveAPIView):
    """
    Retrieve the current user's profile.
    
    Returns the authenticated user's profile information.
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsProfileOwner]
    
    def get_object(self):
        """Get or create profile for the current user."""
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile


class ProfileCreateView(generics.CreateAPIView):
    """
    Create a new profile for the current user.
    
    Creates a profile with basic information for the authenticated user.
    """
    serializer_class = ProfileCreateSerializer
    permission_classes = [IsProfileOwner]
    
    def perform_create(self, serializer):
        """Create profile for the current user."""
        serializer.save(user=self.request.user)


class ProfileUpdateView(generics.UpdateAPIView):
    """
    Update the current user's profile.
    
    Allows partial updates to the authenticated user's profile.
    """
    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsProfileOwner]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_object(self):
        """Get profile for the current user."""
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile


class CVUploadView(generics.UpdateAPIView):
    """
    Upload CV file for the current user's profile.
    
    Handles CV file upload with validation and metadata extraction.
    """
    serializer_class = CVUploadSerializer
    permission_classes = [SecureFileUploadPermission, IsProfileOwner]
    parser_classes = [MultiPartParser, FormParser]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cv_processor = CVProcessingService()
        self.cv_storage = CVStorageService()
    
    def get_object(self):
        """Get profile for the current user."""
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile
    
    def update(self, request, *args, **kwargs):
        """Handle CV upload with processing and validation."""
        instance = self.get_object()
        
        # Get uploaded file
        cv_file = request.FILES.get('cv_file')
        if not cv_file:
            return Response(
                {'error': 'No CV file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process CV file
        processing_result = self.cv_processor.process_cv_upload(cv_file)
        
        if not processing_result['success']:
            return Response(
                {
                    'error': processing_result['message'],
                    'validation_errors': processing_result.get('validation', {}).get('errors', []),
                    'details': processing_result.get('error')
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Clean up old CV file if exists
        if instance.cv_file:
            old_cv_path = instance.cv_file.path
            self.cv_storage.cleanup_old_cv(old_cv_path)
        
        # Update profile with new CV and metadata
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Save with metadata and timestamp
        serializer.save(
            cv_uploaded_at=timezone.now(),
            cv_metadata=processing_result['metadata']
        )
        
        # Return full profile data with processing results
        profile_serializer = ProfileSerializer(instance)
        response_data = profile_serializer.data
        response_data['processing_result'] = {
            'success': processing_result['success'],
            'message': processing_result['message'],
            'warnings': processing_result.get('validation', {}).get('warnings', [])
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class ProfilePublicView(generics.RetrieveAPIView):
    """
    Retrieve a public profile by user ID.
    
    Returns public profile information for any user.
    """
    serializer_class = ProfilePublicSerializer
    permission_classes = [IsAnonymousOrAuthenticated]
    lookup_field = 'user_id'
    
    def get_object(self):
        """Get public profile by user ID."""
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        profile = get_object_or_404(Profile, user=user, is_public=True)
        return profile


@api_view(['POST'])
@permission_classes([IsProfileOwner])
def add_skill(request):
    """
    Add a skill to the current user's profile.
    
    Expects: {"skill": "skill_name"}
    """
    skill = request.data.get('skill')
    if not skill:
        return Response(
            {'error': 'Skill is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    try:
        profile.add_skill(skill.strip())
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsProfileOwner])
def remove_skill(request):
    """
    Remove a skill from the current user's profile.
    
    Expects: {"skill": "skill_name"}
    """
    skill = request.data.get('skill')
    if not skill:
        return Response(
            {'error': 'Skill is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    try:
        profile.remove_skill(skill.strip())
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsProfileOwner])
def profile_stats(request):
    """
    Get profile completion statistics for the current user.
    
    Returns profile completion status and recommendations.
    """
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # Calculate completion percentage
    completion_fields = [
        'headline', 'summary', 'location', 'industry', 'experience_level'
    ]
    completed_fields = sum(1 for field in completion_fields if getattr(profile, field))
    completion_percentage = (completed_fields / len(completion_fields)) * 100
    
    # Generate recommendations
    recommendations = []
    if not profile.headline:
        recommendations.append("Add a professional headline")
    if not profile.summary:
        recommendations.append("Write a professional summary")
    if not profile.location:
        recommendations.append("Add your location")
    if not profile.industry:
        recommendations.append("Specify your industry")
    if not profile.experience_level:
        recommendations.append("Set your experience level")
    if not profile.skills:
        recommendations.append("Add your skills")
    if not profile.cv_file:
        recommendations.append("Upload your CV")
    
    return Response({
        'completion_percentage': completion_percentage,
        'is_complete': profile.is_complete,
        'has_cv': profile.has_cv,
        'has_portfolio': profile.has_portfolio,
        'recommendations': recommendations,
        'total_skills': len(profile.skills) if profile.skills else 0
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsProfileOwner])
def analyze_cv(request):
    """
    Analyze the current user's CV and extract metadata.
    
    Re-processes the uploaded CV to extract or update metadata.
    """
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if not profile.cv_file:
        return Response(
            {'error': 'No CV file found. Please upload a CV first.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Initialize CV processor
        cv_processor = CVProcessingService()
        
        # Re-open the file for processing
        with profile.cv_file.open('rb') as cv_file:
            # Create a temporary uploaded file object for processing
            from django.core.files.uploadedfile import InMemoryUploadedFile
            temp_file = InMemoryUploadedFile(
                cv_file,
                None,
                profile.cv_file.name,
                None,
                profile.cv_file.size,
                None
            )
            
            # Extract metadata
            metadata = cv_processor.extract_cv_metadata(temp_file)
            
            # Update profile with new metadata
            profile.update_cv_metadata(metadata)
            
            return Response({
                'success': True,
                'message': 'CV analysis completed successfully',
                'metadata': metadata
            }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {
                'error': 'Failed to analyze CV',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsProfileOwner])
def cv_metadata(request):
    """
    Get CV metadata for the current user.
    
    Returns extracted metadata from the user's uploaded CV.
    """
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if not profile.cv_file:
        return Response(
            {'error': 'No CV file found. Please upload a CV first.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response({
        'cv_filename': profile.get_cv_filename(),
        'cv_uploaded_at': profile.cv_uploaded_at,
        'cv_metadata': profile.cv_metadata,
        'has_metadata': bool(profile.cv_metadata)
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsProfileOwner])
def generate_portfolio(request):
    """
    Generate a portfolio for the current user.
    
    Expects: {"template": "template_name", "portfolioName": "optional_name"}
    """
    try:
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        template = request.data.get('template', 'modern-pro')
        portfolio_name = request.data.get('portfolioName', '')
        
        # Generate portfolio URL
        username = request.user.username or f"user{request.user.id}"
        if portfolio_name:
            portfolio_url = f"https://koroh.dev/@{username}/{portfolio_name}"
        else:
            portfolio_url = f"https://koroh.dev/@{username}"
        
        # Update profile with portfolio information
        profile.portfolio_url = portfolio_url
        profile.portfolio_settings = {
            'template': template,
            'portfolioName': portfolio_name,
            'generated_at': timezone.now().isoformat(),
            'customizations': {
                'theme': 'light',
                'primaryColor': '#0d9488',
                'font': 'inter',
                'layout': 'standard',
            }
        }
        profile.save()
        
        # Create portfolio data response
        portfolio_data = {
            'id': str(profile.id),
            'url': portfolio_url,
            'template': template,
            'username': username,
            'portfolioName': portfolio_name,
            'customizations': profile.portfolio_settings.get('customizations', {}),
            'content': {
                'title': f"{request.user.first_name} {request.user.last_name}".strip() or username,
                'subtitle': profile.headline or 'Professional',
                'bio': profile.summary or 'Professional portfolio',
                'skills': profile.skills or [],
            },
            'generated_at': profile.portfolio_settings.get('generated_at')
        }
        
        return Response({
            'success': True,
            'message': 'Portfolio generated successfully',
            'portfolio': portfolio_data,
            **portfolio_data  # Include portfolio data at root level for compatibility
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'error': 'Failed to generate portfolio',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsProfileOwner])
def list_portfolios(request):
    """
    List portfolios for the current user.
    
    Returns a list of user's portfolios.
    """
    try:
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        portfolios = []
        if profile.portfolio_url and profile.portfolio_settings:
            username = request.user.username or f"user{request.user.id}"
            portfolio_data = {
                'id': str(profile.id),
                'url': profile.portfolio_url,
                'template': profile.portfolio_settings.get('template', 'modern-pro'),
                'username': username,
                'portfolioName': profile.portfolio_settings.get('portfolioName', ''),
                'customizations': profile.portfolio_settings.get('customizations', {}),
                'content': {
                    'title': f"{request.user.first_name} {request.user.last_name}".strip() or username,
                    'subtitle': profile.headline or 'Professional',
                    'bio': profile.summary or 'Professional portfolio',
                    'skills': profile.skills or [],
                },
                'generated_at': profile.portfolio_settings.get('generated_at')
            }
            portfolios.append(portfolio_data)
        
        return Response(portfolios, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'error': 'Failed to retrieve portfolios',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@permission_classes([IsProfileOwner])
def update_portfolio(request, portfolio_id):
    """
    Update portfolio customizations and content.
    
    Expects: {"customizations": {...}, "content": {...}}
    """
    try:
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        if str(profile.id) != portfolio_id:
            return Response(
                {'error': 'Portfolio not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update portfolio settings
        if not profile.portfolio_settings:
            profile.portfolio_settings = {}
        
        if 'customizations' in request.data:
            profile.portfolio_settings['customizations'] = request.data['customizations']
        
        if 'content' in request.data:
            content = request.data['content']
            # Update profile fields based on content
            if 'title' in content:
                # Split title into first and last name if possible
                name_parts = content['title'].split(' ', 1)
                if len(name_parts) >= 2:
                    request.user.first_name = name_parts[0]
                    request.user.last_name = name_parts[1]
                    request.user.save()
            
            if 'subtitle' in content:
                profile.headline = content['subtitle']
            
            if 'bio' in content:
                profile.summary = content['bio']
        
        profile.portfolio_settings['updated_at'] = timezone.now().isoformat()
        profile.save()
        
        # Return updated portfolio data
        username = request.user.username or f"user{request.user.id}"
        portfolio_data = {
            'id': str(profile.id),
            'url': profile.portfolio_url,
            'template': profile.portfolio_settings.get('template', 'modern-pro'),
            'username': username,
            'portfolioName': profile.portfolio_settings.get('portfolioName', ''),
            'customizations': profile.portfolio_settings.get('customizations', {}),
            'content': {
                'title': f"{request.user.first_name} {request.user.last_name}".strip() or username,
                'subtitle': profile.headline or 'Professional',
                'bio': profile.summary or 'Professional portfolio',
                'skills': profile.skills or [],
            },
            'updated_at': profile.portfolio_settings.get('updated_at')
        }
        
        return Response(portfolio_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'error': 'Failed to update portfolio',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )