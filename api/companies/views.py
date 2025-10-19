"""
Views for Companies app.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F
from jobs.services import CompanySearchService
from .models import Company, CompanyFollow, CompanyInsight
from .serializers import (
    CompanyListSerializer, CompanyDetailSerializer, CompanyCreateUpdateSerializer,
    CompanyFollowSerializer, CompanyInsightSerializer, CompanySearchSerializer
)


class CompanyViewSet(viewsets.ModelViewSet):
    """ViewSet for Company model."""
    
    queryset = Company.objects.filter(is_active=True)
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['industry', 'company_size', 'company_type', 'is_hiring', 'is_verified']
    search_fields = ['name', 'description', 'industry', 'headquarters']
    ordering_fields = ['name', 'follower_count', 'job_count', 'created_at']
    ordering = ['-follower_count']
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'list':
            return CompanyListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CompanyCreateUpdateSerializer
        return CompanyDetailSerializer
    
    def get_queryset(self):
        """Get queryset with optimizations."""
        queryset = super().get_queryset()
        
        if self.action == 'list':
            queryset = queryset.select_related().prefetch_related('followers')
        elif self.action == 'retrieve':
            queryset = queryset.select_related().prefetch_related(
                'followers', 'jobs', 'insights'
            )
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve company and increment view count."""
        instance = self.get_object()
        
        # Increment view count
        Company.objects.filter(id=instance.id).update(
            view_count=F('view_count') + 1
        )
        instance.refresh_from_db()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """Advanced company search."""
        serializer = CompanySearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        search_result = CompanySearchService.search_companies(
            serializer.validated_data,
            user=request.user if request.user.is_authenticated else None
        )
        
        # Paginate results
        page = self.paginate_queryset(search_result['queryset'])
        if page is not None:
            company_serializer = CompanyListSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(company_serializer.data)
        
        company_serializer = CompanyListSerializer(
            search_result['queryset'], many=True, context={'request': request}
        )
        return Response({
            'results': company_serializer.data,
            'total_count': search_result['total_count'],
            'search_params': search_result['search_params']
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def follow(self, request, pk=None):
        """Follow a company."""
        company = self.get_object()
        
        follow, created = CompanyFollow.objects.get_or_create(
            user=request.user,
            company=company,
            defaults={'notifications_enabled': True}
        )
        
        if created:
            return Response(
                {'message': f'You are now following {company.name}'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': f'You are already following {company.name}'},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unfollow(self, request, pk=None):
        """Unfollow a company."""
        company = self.get_object()
        
        try:
            follow = CompanyFollow.objects.get(user=request.user, company=company)
            follow.delete()
            return Response(
                {'message': f'You have unfollowed {company.name}'},
                status=status.HTTP_200_OK
            )
        except CompanyFollow.DoesNotExist:
            return Response(
                {'message': f'You are not following {company.name}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def insights(self, request, pk=None):
        """Get company insights."""
        company = self.get_object()
        insights = company.insights.filter(is_public=True).order_by('-created_at')
        
        page = self.paginate_queryset(insights)
        if page is not None:
            serializer = CompanyInsightSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CompanyInsightSerializer(insights, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def jobs(self, request, pk=None):
        """Get company jobs."""
        from jobs.serializers import JobListSerializer
        from jobs.models import Job
        
        company = self.get_object()
        jobs = Job.objects.filter(
            company=company,
            is_active=True,
            status='published'
        ).order_by('-posted_date')
        
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
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get company statistics."""
        from .services import CompanyTrackingService
        
        company = self.get_object()
        stats = CompanyTrackingService.get_follow_stats(company)
        
        # Add additional stats
        stats.update({
            'total_jobs': company.job_count,
            'profile_views': company.view_count,
            'is_hiring': company.is_hiring,
            'is_verified': company.is_verified,
            'founded_year': company.founded_year,
            'company_size': company.company_size,
        })
        
        return Response(stats)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_insights(self, request, pk=None):
        """Update company insights (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from .services import CompanyInsightService
        
        company = self.get_object()
        result = CompanyInsightService.update_company_insights(company)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        """Get company followers (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from .services import CompanyTrackingService
        from authentication.serializers import UserSerializer
        
        company = self.get_object()
        followers = CompanyTrackingService.get_company_followers(company)
        
        page = self.paginate_queryset(followers)
        if page is not None:
            serializer = UserSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UserSerializer(followers, many=True)
        return Response(serializer.data)


class CompanyFollowViewSet(viewsets.ModelViewSet):
    """ViewSet for CompanyFollow model."""
    
    serializer_class = CompanyFollowSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get user's company follows."""
        return CompanyFollow.objects.filter(
            user=self.request.user
        ).select_related('company').order_by('-followed_at')
    
    @action(detail=False, methods=['get'])
    def companies(self, request):
        """Get companies followed by user."""
        follows = self.get_queryset()
        companies = [follow.company for follow in follows]
        
        page = self.paginate_queryset(companies)
        if page is not None:
            serializer = CompanyListSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = CompanyListSerializer(
            companies, many=True, context={'request': request}
        )
        return Response(serializer.data)


class CompanyInsightViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for CompanyInsight model (read-only)."""
    
    serializer_class = CompanyInsightSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['insight_type', 'company', 'is_public']
    ordering_fields = ['created_at', 'confidence_score']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get public insights."""
        return CompanyInsight.objects.filter(
            is_public=True
        ).select_related('company')