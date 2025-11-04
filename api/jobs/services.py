"""
Services for Jobs app including AI-powered recommendations and search.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from django.db.models import Q, F, Count, Avg, Case, When, FloatField
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from koroh_platform.utils.ai_services import ContentGenerationService, AIServiceConfig, ModelType
from profiles.models import Profile
from companies.models import Company
from .models import Job, JobApplication, JobSavedByUser

User = get_user_model()
logger = logging.getLogger(__name__)


class JobSearchService:
    """Service for job search functionality."""
    
    @staticmethod
    def search_jobs(search_params: Dict[str, Any], user=None) -> Dict[str, Any]:
        """
        Search jobs based on parameters.
        
        Args:
            search_params: Dictionary of search parameters
            user: Optional user for personalized results
            
        Returns:
            Dictionary with queryset and metadata
        """
        queryset = Job.objects.filter(
            is_active=True,
            status='published'
        ).select_related('company').prefetch_related('applications', 'saved_by_users')
        
        # Text search
        query = search_params.get('query', '').strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(skills_required__icontains=query) |
                Q(skills_preferred__icontains=query) |
                Q(company__name__icontains=query) |
                Q(search_keywords__icontains=query)
            )
        
        # Location filter
        location = search_params.get('location', '').strip()
        if location:
            queryset = queryset.filter(
                Q(location__icontains=location) |
                Q(company__headquarters__icontains=location)
            )
        
        # Job type filter
        job_type = search_params.get('job_type')
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        
        # Experience level filter
        experience_level = search_params.get('experience_level')
        if experience_level:
            queryset = queryset.filter(experience_level=experience_level)
        
        # Work arrangement filter
        work_arrangement = search_params.get('work_arrangement')
        if work_arrangement:
            queryset = queryset.filter(work_arrangement=work_arrangement)
        
        # Company filter
        company = search_params.get('company', '').strip()
        if company:
            queryset = queryset.filter(company__name__icontains=company)
        
        # Industry filter
        industry = search_params.get('industry', '').strip()
        if industry:
            queryset = queryset.filter(company__industry__icontains=industry)
        
        # Salary filters
        salary_min = search_params.get('salary_min')
        if salary_min:
            queryset = queryset.filter(
                Q(salary_min__gte=salary_min) | Q(salary_min__isnull=True)
            )
        
        salary_max = search_params.get('salary_max')
        if salary_max:
            queryset = queryset.filter(
                Q(salary_max__lte=salary_max) | Q(salary_max__isnull=True)
            )
        
        # Boolean filters
        if search_params.get('is_remote_friendly'):
            queryset = queryset.filter(is_remote_friendly=True)
        
        if search_params.get('equity_offered'):
            queryset = queryset.filter(equity_offered=True)
        
        if search_params.get('is_featured'):
            queryset = queryset.filter(is_featured=True)
        
        # Posted within days filter
        posted_within_days = search_params.get('posted_within_days')
        if posted_within_days:
            cutoff_date = timezone.now() - timedelta(days=posted_within_days)
            queryset = queryset.filter(posted_date__gte=cutoff_date)
        
        # Skills filter
        skills = search_params.get('skills', [])
        if skills:
            skill_queries = Q()
            for skill in skills:
                skill_queries |= (
                    Q(skills_required__icontains=skill) |
                    Q(skills_preferred__icontains=skill)
                )
            queryset = queryset.filter(skill_queries)
        
        # Ordering
        ordering = search_params.get('ordering', '-posted_date')
        queryset = queryset.order_by(ordering)
        
        # Add user-specific annotations if user is provided
        if user and user.is_authenticated:
            queryset = queryset.annotate(
                is_saved=Case(
                    When(saved_by_users__user=user, then=True),
                    default=False,
                    output_field=FloatField()
                ),
                has_applied=Case(
                    When(applications__user=user, then=True),
                    default=False,
                    output_field=FloatField()
                )
            )
        
        return {
            'queryset': queryset,
            'total_count': queryset.count(),
            'search_params': search_params
        }


class JobRecommendationService:
    """Service for AI-powered job recommendations."""
    
    def __init__(self):
        config = AIServiceConfig(
            model_type=ModelType.CLAUDE_3_SONNET,
            max_tokens=1000,
            temperature=0.3
        )
        self.ai_service = ContentGenerationService(config)
    
    def get_recommendations_for_user(
        self, 
        user: User, 
        limit: int = 10,
        include_applied: bool = False,
        include_saved: bool = True,
        min_match_score: float = 0.3
    ) -> List[Job]:
        """
        Get AI-powered job recommendations for a user.
        
        Args:
            user: User to get recommendations for
            limit: Maximum number of recommendations
            include_applied: Whether to include jobs user has applied to
            include_saved: Whether to include jobs user has saved
            min_match_score: Minimum AI match score threshold
            
        Returns:
            List of recommended Job objects
        """
        try:
            # Get user profile
            profile = getattr(user, 'profile', None)
            if not profile:
                logger.warning(f"No profile found for user {user.id}")
                return self._get_fallback_recommendations(limit)
            
            # Build user context for AI
            user_context = self._build_user_context(profile)
            
            # Get candidate jobs
            candidate_jobs = self._get_candidate_jobs(
                user, include_applied, include_saved
            )
            
            if not candidate_jobs.exists():
                logger.info(f"No candidate jobs found for user {user.id}")
                return []
            
            # Calculate AI match scores
            recommended_jobs = []
            for job in candidate_jobs[:limit * 3]:  # Get more candidates for better filtering
                try:
                    match_score = self._calculate_ai_match_score(user_context, job)
                    if match_score >= min_match_score:
                        job.ai_match_score = match_score
                        job.save(update_fields=['ai_match_score'])
                        recommended_jobs.append(job)
                except Exception as e:
                    logger.error(f"Error calculating match score for job {job.id}: {e}")
                    continue
            
            # Sort by match score and return top results
            recommended_jobs.sort(key=lambda x: x.ai_match_score, reverse=True)
            
            # Send real-time notification about new recommendations
            if recommended_jobs:
                self._send_realtime_job_recommendations(user.id, recommended_jobs[:3])
            
            return recommended_jobs[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recommendations for user {user.id}: {e}")
            return self._get_fallback_recommendations(limit)
    
    def _build_user_context(self, profile: Profile) -> Dict[str, Any]:
        """Build user context for AI matching."""
        return {
            'skills': profile.skills or [],
            'experience_level': profile.experience_level or '',
            'industry': profile.industry or '',
            'location': profile.location or '',
            'headline': profile.headline or '',
            'summary': profile.summary or '',
            'cv_metadata': profile.cv_metadata or {}
        }
    
    def _get_candidate_jobs(
        self, 
        user: User, 
        include_applied: bool, 
        include_saved: bool
    ) -> 'QuerySet[Job]':
        """Get candidate jobs for recommendation."""
        queryset = Job.objects.filter(
            is_active=True,
            status='published'
        ).select_related('company')
        
        # Exclude expired jobs
        queryset = queryset.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
        
        # Filter based on user preferences
        if not include_applied:
            applied_job_ids = JobApplication.objects.filter(
                user=user
            ).values_list('job_id', flat=True)
            queryset = queryset.exclude(id__in=applied_job_ids)
        
        if not include_saved:
            saved_job_ids = JobSavedByUser.objects.filter(
                user=user
            ).values_list('job_id', flat=True)
            queryset = queryset.exclude(id__in=saved_job_ids)
        
        # Prioritize recent jobs
        return queryset.order_by('-posted_date')
    
    def _calculate_ai_match_score(self, user_context: Dict[str, Any], job: Job) -> float:
        """Calculate AI match score between user and job."""
        try:
            # Build job context
            job_context = {
                'title': job.title,
                'description': job.description,
                'skills_required': job.skills_required or [],
                'skills_preferred': job.skills_preferred or [],
                'experience_level': job.experience_level,
                'industry': job.company.industry,
                'location': job.location,
                'work_arrangement': job.work_arrangement,
                'requirements': job.requirements or []
            }
            
            # Create AI prompt for matching
            prompt = self._create_matching_prompt(user_context, job_context)
            
            # Get AI response
            response = self.ai_service.process({
                'data': {'prompt': prompt},
                'template_type': 'analysis',
                'style': 'analytical'
            })
            
            # Parse match score from response
            return self._parse_match_score(response)
            
        except Exception as e:
            logger.error(f"Error calculating AI match score: {e}")
            return self._calculate_fallback_score(user_context, job)
    
    def _create_matching_prompt(
        self, 
        user_context: Dict[str, Any], 
        job_context: Dict[str, Any]
    ) -> str:
        """Create AI prompt for job matching."""
        return f"""
        Analyze the compatibility between this user profile and job posting. 
        Return only a match score between 0.0 and 1.0.

        User Profile:
        - Skills: {', '.join(user_context.get('skills', []))}
        - Experience Level: {user_context.get('experience_level', 'Not specified')}
        - Industry: {user_context.get('industry', 'Not specified')}
        - Location: {user_context.get('location', 'Not specified')}
        - Summary: {user_context.get('summary', 'Not provided')[:200]}

        Job Posting:
        - Title: {job_context.get('title', '')}
        - Required Skills: {', '.join(job_context.get('skills_required', []))}
        - Preferred Skills: {', '.join(job_context.get('skills_preferred', []))}
        - Experience Level: {job_context.get('experience_level', '')}
        - Industry: {job_context.get('industry', '')}
        - Location: {job_context.get('location', '')}
        - Work Arrangement: {job_context.get('work_arrangement', '')}

        Consider:
        1. Skill alignment (40% weight)
        2. Experience level match (25% weight)
        3. Industry relevance (20% weight)
        4. Location compatibility (15% weight)

        Match Score (0.0-1.0):
        """
    
    def _parse_match_score(self, response: str) -> float:
        """Parse match score from AI response."""
        try:
            # Extract number from response
            import re
            numbers = re.findall(r'0\.\d+|1\.0|0|1', response)
            if numbers:
                score = float(numbers[-1])  # Take the last number found
                return max(0.0, min(1.0, score))  # Clamp between 0 and 1
            return 0.5  # Default score if parsing fails
        except (ValueError, IndexError):
            return 0.5
    
    def _calculate_fallback_score(
        self, 
        user_context: Dict[str, Any], 
        job: Job
    ) -> float:
        """Calculate fallback match score without AI."""
        score = 0.0
        
        # Skill matching (40% weight)
        user_skills = set(skill.lower() for skill in user_context.get('skills', []))
        job_required_skills = set(skill.lower() for skill in (job.skills_required or []))
        job_preferred_skills = set(skill.lower() for skill in (job.skills_preferred or []))
        
        if job_required_skills:
            required_match = len(user_skills & job_required_skills) / len(job_required_skills)
            score += required_match * 0.3
        
        if job_preferred_skills:
            preferred_match = len(user_skills & job_preferred_skills) / len(job_preferred_skills)
            score += preferred_match * 0.1
        
        # Experience level match (25% weight)
        if user_context.get('experience_level') == job.experience_level:
            score += 0.25
        
        # Industry match (20% weight)
        if (user_context.get('industry', '').lower() == 
            job.company.industry.lower()):
            score += 0.20
        
        # Location compatibility (15% weight)
        user_location = user_context.get('location', '').lower()
        job_location = job.location.lower()
        if (job.is_remote_friendly or 
            user_location in job_location or 
            job_location in user_location):
            score += 0.15
        
        return min(1.0, score)
    
    def _get_fallback_recommendations(self, limit: int) -> List[Job]:
        """Get fallback recommendations when AI fails."""
        return list(Job.objects.filter(
            is_active=True,
            status='published',
            is_featured=True
        ).order_by('-posted_date')[:limit])
    
    def update_job_recommendations(self, job: Job) -> None:
        """Update AI recommendations for a specific job."""
        try:
            # Get job context for AI tagging
            job_context = {
                'title': job.title,
                'description': job.description,
                'skills_required': job.skills_required or [],
                'skills_preferred': job.skills_preferred or [],
                'requirements': job.requirements or []
            }
            
            # Generate AI tags
            tags = self._generate_ai_tags(job_context)
            job.ai_tags = tags
            job.save(update_fields=['ai_tags'])
            
        except Exception as e:
            logger.error(f"Error updating recommendations for job {job.id}: {e}")
    
    def _generate_ai_tags(self, job_context: Dict[str, Any]) -> List[str]:
        """Generate AI tags for better job matching."""
        try:
            prompt = f"""
            Analyze this job posting and generate 5-10 relevant tags for better matching.
            Focus on key skills, technologies, and job characteristics.

            Job Title: {job_context.get('title', '')}
            Description: {job_context.get('description', '')[:500]}
            Required Skills: {', '.join(job_context.get('skills_required', []))}

            Generate tags as a comma-separated list:
            """
            
            response = self.ai_service.process({
                'data': {'prompt': prompt},
                'template_type': 'tags',
                'style': 'concise'
            })
            
            # Parse tags from response
            tags = [tag.strip() for tag in response.split(',')]
            return [tag for tag in tags if tag and len(tag) > 2][:10]
            
        except Exception as e:
            logger.error(f"Error generating AI tags: {e}")
            return []
    
    def _send_realtime_job_recommendations(self, user_id: int, jobs: List[Job]) -> None:
        """Send real-time job recommendation updates to user."""
        try:
            from koroh_platform.realtime import send_dashboard_update
            
            job_data = []
            for job in jobs:
                job_data.append({
                    'id': str(job.id),
                    'title': job.title,
                    'company': {
                        'name': job.company.name,
                        'logo': job.company.logo.url if job.company.logo else None
                    },
                    'location': job.location,
                    'job_type': job.job_type,
                    'match_score': getattr(job, 'ai_match_score', 0) * 100,
                    'posted_date': job.posted_date.isoformat(),
                    'salary_range': job.salary_range_display
                })
            
            send_dashboard_update(user_id, 'job_recommendation', {
                'recommendations': job_data,
                'count': len(job_data),
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to send real-time job recommendations: {e}")


class CompanySearchService:
    """Service for company search functionality."""
    
    @staticmethod
    def search_companies(search_params: Dict[str, Any], user=None) -> Dict[str, Any]:
        """
        Search companies based on parameters.
        
        Args:
            search_params: Dictionary of search parameters
            user: Optional user for personalized results
            
        Returns:
            Dictionary with queryset and metadata
        """
        queryset = Company.objects.filter(
            is_active=True
        ).prefetch_related('followers')
        
        # Text search
        query = search_params.get('query', '').strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(industry__icontains=query) |
                Q(tech_stack__icontains=query) |
                Q(meta_keywords__icontains=query)
            )
        
        # Industry filter
        industry = search_params.get('industry', '').strip()
        if industry:
            queryset = queryset.filter(industry__icontains=industry)
        
        # Company size filter
        company_size = search_params.get('company_size')
        if company_size:
            queryset = queryset.filter(company_size=company_size)
        
        # Location filter
        location = search_params.get('location', '').strip()
        if location:
            queryset = queryset.filter(
                Q(headquarters__icontains=location) |
                Q(locations__icontains=location)
            )
        
        # Boolean filters
        if search_params.get('is_hiring'):
            queryset = queryset.filter(is_hiring=True)
        
        if search_params.get('is_verified'):
            queryset = queryset.filter(is_verified=True)
        
        # Ordering
        ordering = search_params.get('ordering', '-follower_count')
        queryset = queryset.order_by(ordering)
        
        # Add user-specific annotations if user is provided
        if user and user.is_authenticated:
            queryset = queryset.annotate(
                is_following=Case(
                    When(followers=user, then=True),
                    default=False,
                    output_field=FloatField()
                )
            )
        
        return {
            'queryset': queryset,
            'total_count': queryset.count(),
            'search_params': search_params
        }