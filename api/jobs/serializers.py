"""
Serializers for Jobs app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from companies.serializers import CompanyListSerializer
from .models import Job, JobApplication, JobSavedByUser

User = get_user_model()


class JobListSerializer(serializers.ModelSerializer):
    """Serializer for job list view."""
    
    company = CompanyListSerializer(read_only=True)
    salary_range_display = serializers.CharField(read_only=True)
    is_saved = serializers.SerializerMethodField()
    has_applied = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'slug', 'company', 'summary', 'job_type',
            'experience_level', 'work_arrangement', 'location',
            'is_remote_friendly', 'salary_range_display', 'equity_offered',
            'is_featured', 'is_urgent', 'posted_date', 'application_deadline',
            'view_count', 'application_count', 'is_saved', 'has_applied'
        ]
    
    def get_is_saved(self, obj):
        """Check if current user has saved this job."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return JobSavedByUser.objects.filter(
                user=request.user, job=obj
            ).exists()
        return False
    
    def get_has_applied(self, obj):
        """Check if current user has applied to this job."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return JobApplication.objects.filter(
                user=request.user, job=obj
            ).exists()
        return False


class JobDetailSerializer(serializers.ModelSerializer):
    """Serializer for job detail view."""
    
    company = CompanyListSerializer(read_only=True)
    salary_range_display = serializers.CharField(read_only=True)
    is_published = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_saved = serializers.SerializerMethodField()
    has_applied = serializers.SerializerMethodField()
    application_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'slug', 'company', 'description', 'summary',
            'job_type', 'experience_level', 'work_arrangement', 'location',
            'is_remote_friendly', 'timezone_requirements', 'salary_min',
            'salary_max', 'salary_currency', 'salary_period', 'salary_range_display',
            'equity_offered', 'requirements', 'skills_required', 'skills_preferred',
            'education_requirements', 'benefits', 'application_deadline',
            'application_url', 'application_email', 'application_instructions',
            'is_featured', 'is_urgent', 'is_published', 'is_expired',
            'posted_date', 'expires_at', 'view_count', 'application_count',
            'ai_match_score', 'ai_tags', 'is_saved', 'has_applied', 'application_status'
        ]
    
    def get_is_saved(self, obj):
        """Check if current user has saved this job."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return JobSavedByUser.objects.filter(
                user=request.user, job=obj
            ).exists()
        return False
    
    def get_has_applied(self, obj):
        """Check if current user has applied to this job."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return JobApplication.objects.filter(
                user=request.user, job=obj
            ).exists()
        return False
    
    def get_application_status(self, obj):
        """Get current user's application status for this job."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                application = JobApplication.objects.get(
                    user=request.user, job=obj
                )
                return application.status
            except JobApplication.DoesNotExist:
                return None
        return None


class JobCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating jobs."""
    
    class Meta:
        model = Job
        fields = [
            'title', 'company', 'description', 'summary', 'job_type',
            'experience_level', 'work_arrangement', 'location',
            'is_remote_friendly', 'timezone_requirements', 'salary_min',
            'salary_max', 'salary_currency', 'salary_period', 'equity_offered',
            'requirements', 'skills_required', 'skills_preferred',
            'education_requirements', 'benefits', 'application_deadline',
            'application_url', 'application_email', 'application_instructions',
            'status', 'is_featured', 'is_urgent', 'expires_at',
            'meta_description', 'search_keywords'
        ]
    
    def validate(self, data):
        """Validate job data."""
        # Ensure salary_min is not greater than salary_max
        salary_min = data.get('salary_min')
        salary_max = data.get('salary_max')
        
        if salary_min and salary_max and salary_min > salary_max:
            raise serializers.ValidationError(
                "Minimum salary cannot be greater than maximum salary."
            )
        
        return data


class JobApplicationSerializer(serializers.ModelSerializer):
    """Serializer for job applications."""
    
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_slug = serializers.CharField(source='job.slug', read_only=True)
    company_name = serializers.CharField(source='job.company.name', read_only=True)
    applicant_name = serializers.CharField(source='user.get_full_name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'job_title', 'job_slug', 'company_name',
            'applicant_name', 'status', 'cover_letter', 'custom_responses',
            'ai_match_score', 'ai_summary', 'source', 'applied_at',
            'updated_at', 'reviewed_at', 'is_active'
        ]
        read_only_fields = [
            'applied_at', 'updated_at', 'reviewed_at', 'ai_match_score', 'ai_summary'
        ]
    
    def create(self, validated_data):
        """Create job application."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class JobSavedSerializer(serializers.ModelSerializer):
    """Serializer for saved jobs."""
    
    job = JobListSerializer(read_only=True)
    
    class Meta:
        model = JobSavedByUser
        fields = ['id', 'job', 'saved_at', 'notes']
        read_only_fields = ['saved_at']
    
    def create(self, validated_data):
        """Create saved job."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class JobSearchSerializer(serializers.Serializer):
    """Serializer for job search parameters."""
    
    query = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    job_type = serializers.CharField(required=False, allow_blank=True)
    experience_level = serializers.CharField(required=False, allow_blank=True)
    work_arrangement = serializers.CharField(required=False, allow_blank=True)
    company = serializers.CharField(required=False, allow_blank=True)
    industry = serializers.CharField(required=False, allow_blank=True)
    salary_min = serializers.IntegerField(required=False, min_value=0)
    salary_max = serializers.IntegerField(required=False, min_value=0)
    is_remote_friendly = serializers.BooleanField(required=False)
    equity_offered = serializers.BooleanField(required=False)
    is_featured = serializers.BooleanField(required=False)
    posted_within_days = serializers.IntegerField(required=False, min_value=1, max_value=365)
    skills = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True
    )
    ordering = serializers.ChoiceField(
        choices=[
            'title', '-title', 'posted_date', '-posted_date',
            'salary_min', '-salary_min', 'application_count', '-application_count',
            'view_count', '-view_count', 'ai_match_score', '-ai_match_score'
        ],
        required=False,
        default='-posted_date'
    )
    
    def validate(self, data):
        """Validate search parameters."""
        salary_min = data.get('salary_min')
        salary_max = data.get('salary_max')
        
        if salary_min and salary_max and salary_min > salary_max:
            raise serializers.ValidationError(
                "Minimum salary cannot be greater than maximum salary."
            )
        
        return data


class JobRecommendationSerializer(serializers.Serializer):
    """Serializer for job recommendation parameters."""
    
    user_id = serializers.IntegerField(required=False)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=50, default=10)
    include_applied = serializers.BooleanField(required=False, default=False)
    include_saved = serializers.BooleanField(required=False, default=True)
    min_match_score = serializers.FloatField(
        required=False, min_value=0.0, max_value=1.0, default=0.3
    )