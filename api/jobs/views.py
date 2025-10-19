"""
Views for Jobs app.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F
from django.utils import timezone
from .models import Job, JobApplication, JobSavedByUser
from .serializers import (
    JobListSerializer, JobDetailSerializer, JobCreateUpdateSerializer,
    JobApplicationSerializer, JobSavedSerializer, JobSearchSerializer,
    JobRecommendationSerializer
)
from .services import JobSearchService, JobRecommendationService


class JobViewSet(viewsets.ModelViewSet):
    """ViewSet for Job model."""
    
    queryset = Job.objects.filter(is_active=True, status='published')
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'job_type', 'experience_level', 'work_arrangement', 'company',
        'is_remote_friendly', 'equity_offered', 'is_featured', 'is_urgent'
    ]
    search_fields = [
        'title', 'description', 'skills_required', 'skills_preferred',
        'company__name', 'location'
    ]
    ordering_fields = [
        'title', 'posted_date', 'salary_min', 'application_count',
        'view_count', 'ai_match_score'
    ]
    ordering = ['-posted_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'list':
            return JobListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return JobCreateUpdateSerializer
        return JobDetailSerializer
    
    def get_queryset(self):
        """Get queryset with optimizations."""
        queryset = super().get_queryset()
        
        # Filter out expired jobs
        from django.db import models
        queryset = queryset.filter(
            models.Q(expires_at__isnull=True) | 
            models.Q(expires_at__gt=timezone.now())
        )
        
        if self.action == 'list':
            queryset = queryset.select_related('company').prefetch_related(
                'applications', 'saved_by_users'
            )
        elif self.action == 'retrieve':
            queryset = queryset.select_related('company').prefetch_related(
                'applications', 'saved_by_users'
            )
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve job and increment view count."""
        instance = self.get_object()
        
        # Increment view count
        Job.objects.filter(id=instance.id).update(
            view_count=F('view_count') + 1
        )
        instance.refresh_from_db()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """Advanced job search."""
        serializer = JobSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        search_result = JobSearchService.search_jobs(
            serializer.validated_data,
            user=request.user if request.user.is_authenticated else None
        )
        
        # Paginate results
        page = self.paginate_queryset(search_result['queryset'])
        if page is not None:
            job_serializer = JobListSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(job_serializer.data)
        
        job_serializer = JobListSerializer(
            search_result['queryset'], many=True, context={'request': request}
        )
        return Response({
            'results': job_serializer.data,
            'total_count': search_result['total_count'],
            'search_params': search_result['search_params']
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def recommendations(self, request):
        """Get AI-powered job recommendations."""
        serializer = JobRecommendationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        recommendation_service = JobRecommendationService()
        
        user_id = serializer.validated_data.get('user_id')
        user = request.user
        if user_id and request.user.is_staff:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        recommended_jobs = recommendation_service.get_recommendations_for_user(
            user=user,
            limit=serializer.validated_data.get('limit', 10),
            include_applied=serializer.validated_data.get('include_applied', False),
            include_saved=serializer.validated_data.get('include_saved', True),
            min_match_score=serializer.validated_data.get('min_match_score', 0.3)
        )
        
        job_serializer = JobListSerializer(
            recommended_jobs, many=True, context={'request': request}
        )
        return Response({
            'recommendations': job_serializer.data,
            'total_count': len(recommended_jobs),
            'user_id': user.id
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def apply(self, request, pk=None):
        """Apply to a job."""
        job = self.get_object()
        
        # Check if user already applied
        if JobApplication.objects.filter(user=request.user, job=job).exists():
            return Response(
                {'message': 'You have already applied to this job'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create application
        application_data = {
            'job': job.id,
            'cover_letter': request.data.get('cover_letter', ''),
            'custom_responses': request.data.get('custom_responses', {}),
            'source': request.data.get('source', 'platform')
        }
        
        serializer = JobApplicationSerializer(
            data=application_data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        
        return Response(
            {
                'message': f'Successfully applied to {job.title}',
                'application': JobApplicationSerializer(application).data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def save(self, request, pk=None):
        """Save a job."""
        job = self.get_object()
        
        saved_job, created = JobSavedByUser.objects.get_or_create(
            user=request.user,
            job=job,
            defaults={'notes': request.data.get('notes', '')}
        )
        
        if created:
            return Response(
                {'message': f'Job "{job.title}" has been saved'},
                status=status.HTTP_201_CREATED
            )
        else:
            # Update notes if provided
            notes = request.data.get('notes')
            if notes is not None:
                saved_job.notes = notes
                saved_job.save(update_fields=['notes'])
            
            return Response(
                {'message': f'Job "{job.title}" was already saved'},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unsave(self, request, pk=None):
        """Unsave a job."""
        job = self.get_object()
        
        try:
            saved_job = JobSavedByUser.objects.get(user=request.user, job=job)
            saved_job.delete()
            return Response(
                {'message': f'Job "{job.title}" has been removed from saved jobs'},
                status=status.HTTP_200_OK
            )
        except JobSavedByUser.DoesNotExist:
            return Response(
                {'message': f'Job "{job.title}" was not in your saved jobs'},
                status=status.HTTP_400_BAD_REQUEST
            )


class JobApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for JobApplication model."""
    
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'job__company', 'job__job_type']
    ordering_fields = ['applied_at', 'updated_at', 'ai_match_score']
    ordering = ['-applied_at']
    
    def get_queryset(self):
        """Get user's job applications."""
        return JobApplication.objects.filter(
            user=self.request.user
        ).select_related('job', 'job__company').order_by('-applied_at')
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update application status (for employers)."""
        application = self.get_object()
        
        # Only allow job poster or company admin to update status
        if (request.user != application.job.company.created_by and 
            not request.user.is_staff):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        if new_status not in dict(JobApplication.APPLICATION_STATUSES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.update_status(new_status)
        
        serializer = self.get_serializer(application)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get application statistics for user."""
        applications = self.get_queryset()
        
        stats = {
            'total_applications': applications.count(),
            'pending': applications.filter(status='pending').count(),
            'reviewing': applications.filter(status='reviewing').count(),
            'shortlisted': applications.filter(status='shortlisted').count(),
            'interview': applications.filter(status='interview').count(),
            'offer': applications.filter(status='offer').count(),
            'accepted': applications.filter(status='accepted').count(),
            'rejected': applications.filter(status='rejected').count(),
            'withdrawn': applications.filter(status='withdrawn').count(),
        }
        
        return Response(stats)


class JobSavedViewSet(viewsets.ModelViewSet):
    """ViewSet for JobSavedByUser model."""
    
    serializer_class = JobSavedSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-saved_at']
    
    def get_queryset(self):
        """Get user's saved jobs."""
        return JobSavedByUser.objects.filter(
            user=self.request.user
        ).select_related('job', 'job__company').order_by('-saved_at')
    
    @action(detail=False, methods=['get'])
    def jobs(self, request):
        """Get saved jobs as job objects."""
        saved_jobs = self.get_queryset()
        jobs = [saved.job for saved in saved_jobs]
        
        page = self.paginate_queryset(jobs)
        if page is not None:
            serializer = JobListSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = JobListSerializer(
            jobs, many=True, context={'request': request}
        )
        return Response(serializer.data)