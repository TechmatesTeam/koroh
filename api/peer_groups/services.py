"""
Services for peer groups app.

This module provides AI-powered services for peer group recommendations,
matching algorithms, and group discovery functionality.
"""

import logging
from typing import Dict, List, Any, Optional
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg
from koroh_platform.utils.ai_services import (
    AIServiceFactory, AIServiceConfig, ModelType, RecommendationService
)
from .models import PeerGroup, GroupMembership

User = get_user_model()
logger = logging.getLogger(__name__)


class PeerGroupRecommendationService:
    """
    AI-powered peer group recommendation service.
    
    Uses AWS Bedrock to analyze user profiles and suggest relevant peer groups
    based on skills, industry, experience level, and interests.
    """
    
    def __init__(self):
        """Initialize the recommendation service."""
        self.ai_service = AIServiceFactory.create_recommendation_service(
            AIServiceConfig(
                model_type=ModelType.CLAUDE_3_SONNET,
                max_tokens=2000,
                temperature=0.4,  # Lower temperature for consistent recommendations
                max_retries=2
            )
        )
    
    def get_recommendations_for_user(
        self, 
        user: User, 
        limit: int = 10,
        exclude_joined: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get AI-powered peer group recommendations for a user.
        
        Args:
            user: User to get recommendations for
            limit: Maximum number of recommendations to return
            exclude_joined: Whether to exclude groups user has already joined
            
        Returns:
            List of recommended groups with match scores and explanations
        """
        try:
            # Get user profile data
            user_profile = self._build_user_profile(user)
            
            # Get available groups
            available_groups = self._get_available_groups(user, exclude_joined, limit * 2)
            
            if not available_groups:
                logger.info(f"No available groups found for user {user.id}")
                return []
            
            # Prepare data for AI service
            input_data = {
                'user_profile': user_profile,
                'options': available_groups,
                'type': 'peer_group'
            }
            
            # Get AI recommendations
            ai_recommendations = self.ai_service.process(input_data)
            
            # Process and enhance recommendations
            recommendations = self._process_ai_recommendations(
                ai_recommendations, 
                user, 
                limit
            )
            
            logger.info(f"Generated {len(recommendations)} recommendations for user {user.id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations for user {user.id}: {e}")
            # Fallback to rule-based recommendations
            return self._get_fallback_recommendations(user, limit, exclude_joined)
    
    def _build_user_profile(self, user: User) -> Dict[str, Any]:
        """
        Build user profile data for AI analysis.
        
        Args:
            user: User to build profile for
            
        Returns:
            Dictionary containing user profile information
        """
        profile = getattr(user, 'profile', None)
        
        user_profile = {
            'user_id': user.id,
            'name': user.get_full_name(),
            'email': user.email,
            'skills': [],
            'industry': '',
            'experience_level': '',
            'location': '',
            'interests': [],
            'current_groups': [],
            'career_goals': []
        }
        
        if profile:
            user_profile.update({
                'skills': profile.skills or [],
                'industry': profile.industry or '',
                'experience_level': profile.experience_level or '',
                'location': profile.location or '',
                'headline': profile.headline or '',
                'summary': profile.summary or ''
            })
        
        # Get current group memberships
        current_groups = GroupMembership.objects.filter(
            user=user, 
            status='active'
        ).select_related('group').values_list('group__name', 'group__group_type', 'group__industry')
        
        user_profile['current_groups'] = [
            {
                'name': name,
                'type': group_type,
                'industry': industry
            }
            for name, group_type, industry in current_groups
        ]
        
        return user_profile
    
    def _get_available_groups(
        self, 
        user: User, 
        exclude_joined: bool, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Get available peer groups for recommendation.
        
        Args:
            user: User to get groups for
            exclude_joined: Whether to exclude joined groups
            limit: Maximum number of groups to return
            
        Returns:
            List of group data dictionaries
        """
        queryset = PeerGroup.objects.filter(
            is_active=True
        ).annotate(
            active_member_count=Count(
                'members', 
                filter=Q(groupmembership__status='active')
            )
        )
        
        # Exclude groups user has already joined
        if exclude_joined:
            joined_groups = user.peer_groups.values_list('id', flat=True)
            queryset = queryset.exclude(id__in=joined_groups)
        
        # Exclude private groups unless user is invited
        queryset = queryset.exclude(
            Q(privacy_level='private') & 
            ~Q(groupmembership__user=user, groupmembership__status='invited')
        )
        
        # Order by activity and member count
        queryset = queryset.order_by('-activity_score', '-active_member_count')[:limit]
        
        groups = []
        for group in queryset:
            group_data = {
                'id': group.id,
                'name': group.name,
                'slug': group.slug,
                'description': group.description,
                'tagline': group.tagline,
                'group_type': group.group_type,
                'industry': group.industry,
                'skills': group.skills or [],
                'experience_level': group.experience_level,
                'location': group.location,
                'privacy_level': group.privacy_level,
                'member_count': group.active_member_count,
                'activity_score': float(group.activity_score),
                'created_by': group.created_by.get_full_name(),
                'is_featured': group.is_featured,
                'rules': group.rules,
                'welcome_message': group.welcome_message
            }
            groups.append(group_data)
        
        return groups
    
    def _process_ai_recommendations(
        self, 
        ai_recommendations: List[Dict[str, Any]], 
        user: User, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Process AI recommendations and add additional metadata.
        
        Args:
            ai_recommendations: Raw AI recommendations
            user: User the recommendations are for
            limit: Maximum number to return
            
        Returns:
            Processed recommendations with additional metadata
        """
        processed_recommendations = []
        
        for rec in ai_recommendations[:limit]:
            try:
                group_id = rec.get('option_id')
                if not group_id:
                    continue
                
                # Get the actual group object
                try:
                    group = PeerGroup.objects.get(id=group_id)
                except PeerGroup.DoesNotExist:
                    continue
                
                # Build recommendation data
                recommendation = {
                    'group': {
                        'id': group.id,
                        'name': group.name,
                        'slug': group.slug,
                        'description': group.description,
                        'tagline': group.tagline,
                        'group_type': group.group_type,
                        'industry': group.industry,
                        'privacy_level': group.privacy_level,
                        'member_count': group.member_count,
                        'activity_score': float(group.activity_score),
                        'image': group.image.url if group.image else None,
                        'is_featured': group.is_featured
                    },
                    'match_score': rec.get('match_score', 0),
                    'match_reasons': rec.get('match_reasons', []),
                    'recommendation_text': rec.get('recommendation_text', ''),
                    'confidence': rec.get('confidence', 'medium'),
                    'can_join': group.can_user_join(user),
                    'requires_approval': group.requires_approval
                }
                
                processed_recommendations.append(recommendation)
                
            except Exception as e:
                logger.warning(f"Error processing recommendation: {e}")
                continue
        
        return processed_recommendations
    
    def _get_fallback_recommendations(
        self, 
        user: User, 
        limit: int, 
        exclude_joined: bool
    ) -> List[Dict[str, Any]]:
        """
        Get fallback recommendations using rule-based matching.
        
        Args:
            user: User to get recommendations for
            limit: Maximum number of recommendations
            exclude_joined: Whether to exclude joined groups
            
        Returns:
            List of rule-based recommendations
        """
        logger.info(f"Using fallback recommendations for user {user.id}")
        
        profile = getattr(user, 'profile', None)
        queryset = PeerGroup.objects.filter(is_active=True)
        
        # Exclude joined groups
        if exclude_joined:
            joined_groups = user.peer_groups.values_list('id', flat=True)
            queryset = queryset.exclude(id__in=joined_groups)
        
        # Rule-based filtering
        if profile:
            # Match by industry
            if profile.industry:
                queryset = queryset.filter(
                    Q(industry__icontains=profile.industry) |
                    Q(industry='') |
                    Q(industry__isnull=True)
                )
            
            # Match by skills (if group has overlapping skills)
            if profile.skills:
                for skill in profile.skills[:3]:  # Top 3 skills
                    queryset = queryset.filter(
                        Q(skills__icontains=skill) |
                        Q(skills=[]) |
                        Q(skills__isnull=True)
                    )
                    break  # Just use first matching skill
        
        # Order by activity and member count
        groups = queryset.annotate(
            active_member_count=Count(
                'members', 
                filter=Q(groupmembership__status='active')
            )
        ).order_by('-is_featured', '-activity_score', '-active_member_count')[:limit]
        
        recommendations = []
        for group in groups:
            recommendation = {
                'group': {
                    'id': group.id,
                    'name': group.name,
                    'slug': group.slug,
                    'description': group.description,
                    'tagline': group.tagline,
                    'group_type': group.group_type,
                    'industry': group.industry,
                    'privacy_level': group.privacy_level,
                    'member_count': group.active_member_count,
                    'activity_score': float(group.activity_score),
                    'image': group.image.url if group.image else None,
                    'is_featured': group.is_featured
                },
                'match_score': self._calculate_rule_based_score(user, group),
                'match_reasons': self._get_rule_based_reasons(user, group),
                'recommendation_text': f"This {group.group_type} group might interest you based on your profile.",
                'confidence': 'medium',
                'can_join': group.can_user_join(user),
                'requires_approval': group.requires_approval
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_rule_based_score(self, user: User, group: PeerGroup) -> int:
        """Calculate a simple rule-based match score."""
        score = 50  # Base score
        profile = getattr(user, 'profile', None)
        
        if not profile:
            return score
        
        # Industry match
        if profile.industry and group.industry:
            if profile.industry.lower() in group.industry.lower():
                score += 20
        
        # Skills match
        if profile.skills and group.skills:
            common_skills = set(profile.skills) & set(group.skills)
            score += min(len(common_skills) * 5, 20)
        
        # Activity bonus
        if group.activity_score > 50:
            score += 10
        
        # Featured bonus
        if group.is_featured:
            score += 5
        
        return min(score, 100)
    
    def _get_rule_based_reasons(self, user: User, group: PeerGroup) -> List[str]:
        """Get rule-based match reasons."""
        reasons = []
        profile = getattr(user, 'profile', None)
        
        if not profile:
            reasons.append("Active group with good engagement")
            return reasons
        
        # Industry match
        if profile.industry and group.industry:
            if profile.industry.lower() in group.industry.lower():
                reasons.append(f"Matches your {profile.industry} industry background")
        
        # Skills match
        if profile.skills and group.skills:
            common_skills = set(profile.skills) & set(group.skills)
            if common_skills:
                reasons.append(f"Shares skills: {', '.join(list(common_skills)[:3])}")
        
        # Group type
        reasons.append(f"Focused on {group.group_type} networking")
        
        # Activity
        if group.activity_score > 50:
            reasons.append("Highly active group with regular discussions")
        
        return reasons[:3]  # Limit to 3 reasons


class GroupMatchingService:
    """
    Service for matching users to peer groups based on various criteria.
    
    Provides different matching algorithms for different use cases.
    """
    
    def __init__(self):
        """Initialize the matching service."""
        self.recommendation_service = PeerGroupRecommendationService()
    
    def find_similar_groups(
        self, 
        reference_group: PeerGroup, 
        user: User, 
        limit: int = 5
    ) -> List[PeerGroup]:
        """
        Find groups similar to a reference group.
        
        Args:
            reference_group: Group to find similar groups to
            user: User requesting similar groups
            limit: Maximum number of groups to return
            
        Returns:
            List of similar groups
        """
        queryset = PeerGroup.objects.filter(
            is_active=True
        ).exclude(
            id=reference_group.id
        )
        
        # Exclude groups user has already joined
        joined_groups = user.peer_groups.values_list('id', flat=True)
        queryset = queryset.exclude(id__in=joined_groups)
        
        # Match by similar criteria
        similar_groups = queryset.filter(
            Q(group_type=reference_group.group_type) |
            Q(industry=reference_group.industry) |
            Q(skills__overlap=reference_group.skills)
        ).annotate(
            active_member_count=Count(
                'members', 
                filter=Q(groupmembership__status='active')
            )
        ).order_by('-activity_score', '-active_member_count')[:limit]
        
        return list(similar_groups)
    
    def get_trending_groups(self, user: User, limit: int = 10) -> List[PeerGroup]:
        """
        Get trending/popular groups.
        
        Args:
            user: User requesting trending groups
            limit: Maximum number of groups to return
            
        Returns:
            List of trending groups
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Groups with recent activity and growth
        recent_date = timezone.now() - timedelta(days=7)
        
        trending_groups = PeerGroup.objects.filter(
            is_active=True,
            last_activity__gte=recent_date
        ).annotate(
            recent_members=Count(
                'members',
                filter=Q(
                    groupmembership__status='active',
                    groupmembership__joined_at__gte=recent_date
                )
            ),
            active_member_count=Count(
                'members',
                filter=Q(groupmembership__status='active')
            )
        ).filter(
            recent_members__gt=0
        ).order_by('-recent_members', '-activity_score', '-active_member_count')[:limit]
        
        return list(trending_groups)
    
    def search_groups(
        self, 
        query: str, 
        user: User, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20
    ) -> List[PeerGroup]:
        """
        Search for groups based on query and filters.
        
        Args:
            query: Search query string
            user: User performing the search
            filters: Additional filters to apply
            limit: Maximum number of results
            
        Returns:
            List of matching groups
        """
        queryset = PeerGroup.objects.filter(is_active=True)
        
        # Text search
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(tagline__icontains=query) |
                Q(industry__icontains=query) |
                Q(skills__icontains=query)
            )
        
        # Apply filters
        if filters:
            if filters.get('group_type'):
                queryset = queryset.filter(group_type=filters['group_type'])
            
            if filters.get('industry'):
                queryset = queryset.filter(industry__icontains=filters['industry'])
            
            if filters.get('privacy_level'):
                queryset = queryset.filter(privacy_level=filters['privacy_level'])
            
            if filters.get('location'):
                queryset = queryset.filter(location__icontains=filters['location'])
            
            if filters.get('min_members'):
                queryset = queryset.filter(member_count__gte=filters['min_members'])
            
            if filters.get('max_members'):
                queryset = queryset.filter(member_count__lte=filters['max_members'])
        
        # Order results
        results = queryset.annotate(
            active_member_count=Count(
                'members',
                filter=Q(groupmembership__status='active')
            )
        ).order_by('-activity_score', '-active_member_count', 'name')[:limit]
        
        return list(results)