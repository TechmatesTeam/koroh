"""
Serializers for Companies app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Company, CompanyFollow, CompanyInsight

User = get_user_model()


class CompanyListSerializer(serializers.ModelSerializer):
    """Serializer for company list view."""
    
    is_following = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'tagline', 'industry', 'company_size',
            'headquarters', 'logo', 'is_verified', 'is_hiring',
            'follower_count', 'job_count', 'is_following'
        ]
        read_only_fields = ['slug', 'follower_count', 'job_count']
    
    def get_is_following(self, obj):
        """Check if current user is following this company."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CompanyFollow.objects.filter(
                user=request.user, company=obj
            ).exists()
        return False


class CompanyDetailSerializer(serializers.ModelSerializer):
    """Serializer for company detail view."""
    
    is_following = serializers.SerializerMethodField()
    recent_jobs = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'description', 'tagline', 'industry',
            'company_size', 'company_type', 'founded_year', 'headquarters',
            'locations', 'website', 'email', 'phone', 'linkedin_url',
            'twitter_url', 'github_url', 'logo', 'cover_image',
            'culture_description', 'benefits', 'tech_stack', 'is_verified',
            'is_active', 'is_hiring', 'follower_count', 'job_count',
            'view_count', 'created_at', 'is_following', 'recent_jobs'
        ]
        read_only_fields = [
            'slug', 'follower_count', 'job_count', 'view_count', 'created_at'
        ]
    
    def get_is_following(self, obj):
        """Check if current user is following this company."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CompanyFollow.objects.filter(
                user=request.user, company=obj
            ).exists()
        return False
    
    def get_recent_jobs(self, obj):
        """Get recent job postings from this company."""
        from jobs.serializers import JobListSerializer
        recent_jobs = obj.jobs.filter(
            is_active=True, status='published'
        ).order_by('-posted_date')[:5]
        return JobListSerializer(recent_jobs, many=True, context=self.context).data


class CompanyCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating companies."""
    
    class Meta:
        model = Company
        fields = [
            'name', 'description', 'tagline', 'industry', 'company_size',
            'company_type', 'founded_year', 'headquarters', 'locations',
            'website', 'email', 'phone', 'linkedin_url', 'twitter_url',
            'github_url', 'logo', 'cover_image', 'culture_description',
            'benefits', 'tech_stack', 'meta_description', 'meta_keywords'
        ]
    
    def validate_website(self, value):
        """Validate website URL."""
        if value and not value.startswith(('http://', 'https://')):
            value = f'https://{value}'
        return value


class CompanyFollowSerializer(serializers.ModelSerializer):
    """Serializer for company follow relationship."""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_slug = serializers.CharField(source='company.slug', read_only=True)
    
    class Meta:
        model = CompanyFollow
        fields = [
            'id', 'company', 'company_name', 'company_slug',
            'followed_at', 'notifications_enabled'
        ]
        read_only_fields = ['followed_at']
    
    def create(self, validated_data):
        """Create company follow relationship."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class CompanyInsightSerializer(serializers.ModelSerializer):
    """Serializer for company insights."""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CompanyInsight
        fields = [
            'id', 'company', 'company_name', 'insight_type', 'title',
            'description', 'data', 'source', 'confidence_score',
            'is_public', 'created_at', 'expires_at', 'is_expired'
        ]
        read_only_fields = ['created_at', 'is_expired']


class CompanySearchSerializer(serializers.Serializer):
    """Serializer for company search parameters."""
    
    query = serializers.CharField(required=False, allow_blank=True)
    industry = serializers.CharField(required=False, allow_blank=True)
    company_size = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    is_hiring = serializers.BooleanField(required=False)
    is_verified = serializers.BooleanField(required=False)
    ordering = serializers.ChoiceField(
        choices=[
            'name', '-name', 'follower_count', '-follower_count',
            'job_count', '-job_count', 'created_at', '-created_at'
        ],
        required=False,
        default='-follower_count'
    )