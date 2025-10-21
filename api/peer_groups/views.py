"""
Views for peer groups app.

This module defines the API views for peer group functionality,
including group management, membership, and communication features.
"""

import logging
from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone

logger = logging.getLogger(__name__)

from .models import (
    PeerGroup, GroupMembership, GroupAdminship,
    GroupPost, GroupComment
)
from .serializers import (
    PeerGroupListSerializer, PeerGroupDetailSerializer,
    PeerGroupCreateSerializer, GroupMembershipSerializer,
    GroupAdminshipSerializer, GroupPostSerializer,
    GroupCommentSerializer, GroupJoinRequestSerializer,
    GroupInviteSerializer, GroupMemberActionSerializer
)

User = get_user_model()


class PeerGroupViewSet(ModelViewSet):
    """
    ViewSet for peer group management.
    
    Provides CRUD operations for peer groups with additional
    actions for membership management and group discovery.
    """
    
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Get queryset with optimized queries."""
        return PeerGroup.objects.select_related('created_by').prefetch_related(
            'admins',
            Prefetch(
                'group_memberships',
                queryset=GroupMembership.objects.filter(status='active').select_related('user')
            )
        ).annotate(
            member_count_actual=Count('members', filter=Q(groupmembership__status='active'))
        )
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return PeerGroupListSerializer
        elif self.action == 'create':
            return PeerGroupCreateSerializer
        else:
            return PeerGroupDetailSerializer
    
    def perform_create(self, serializer):
        """Create group and add creator as admin."""
        group = serializer.save(created_by=self.request.user)
        
        # Add creator as active member
        GroupMembership.objects.create(
            user=self.request.user,
            group=group,
            status='active',
            role='member'
        )
        
        # Add creator as admin
        GroupAdminship.objects.create(
            user=self.request.user,
            group=group,
            role='admin',
            can_manage_members=True,
            can_moderate_content=True,
            can_edit_group=True
        )
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]
    
    def update(self, request, *args, **kwargs):
        """Update group (only admins can edit)."""
        group = self.get_object()
        if not group.is_admin(request.user):
            return Response(
                {'error': 'Only group admins can edit group settings.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete group (only creator can delete)."""
        group = self.get_object()
        if group.created_by != request.user:
            return Response(
                {'error': 'Only the group creator can delete the group.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def discover(self, request):
        """Discover groups based on user profile and preferences."""
        user = request.user
        
        # Allow unauthenticated users to discover public groups
        if not user.is_authenticated:
            queryset = self.get_queryset().filter(
                is_active=True,
                privacy_level='public'
            ).annotate(
                member_count=Count('members', filter=Q(groupmembership__status='active'))
            ).order_by('-member_count', '-created_at')[:10]
            
            serializer = PeerGroupListSerializer(queryset, many=True, context={'request': request})
            return Response({
                'recommendations': [{'group': group} for group in serializer.data],
                'total': len(serializer.data),
                'ai_powered': False
            })
        
        try:
            # Simple discovery based on user profile
            profile = getattr(user, 'profile', None)
            user_skills = profile.skills if profile and profile.skills else []
            user_industry = profile.industry if profile else None
            
            # Build discovery query
            queryset = self.get_queryset().filter(is_active=True)
            
            # Filter by user's industry and skills if available
            if user_industry or user_skills:
                filters = Q()
                if user_industry:
                    filters |= Q(industry__icontains=user_industry)
                if user_skills:
                    filters |= Q(skills__overlap=user_skills)
                queryset = queryset.filter(filters)
            
            # Exclude groups user is already a member of
            if hasattr(user, 'peer_groups'):
                user_groups = user.peer_groups.values_list('id', flat=True)
                queryset = queryset.exclude(id__in=user_groups)
            
            # Order by activity score and member count
            queryset = queryset.annotate(
                member_count=Count('members', filter=Q(groupmembership__status='active'))
            ).order_by('-activity_score', '-member_count')[:20]
            
            serializer = PeerGroupListSerializer(queryset, many=True, context={'request': request})
            return Response({
                'recommendations': [{'group': group} for group in serializer.data],
                'total': len(serializer.data),
                'ai_powered': False
            })
            
        except Exception as e:
            logger.error(f"Error in discovery for user {user.id if user.is_authenticated else 'anonymous'}: {e}")
            
            # Fallback to basic groups
            queryset = self.get_queryset().filter(is_active=True)[:10]
            serializer = PeerGroupListSerializer(queryset, many=True, context={'request': request})
            return Response({
                'recommendations': [{'group': group} for group in serializer.data],
                'total': len(serializer.data),
                'ai_powered': False,
                'fallback': True
            })
    
    @action(detail=False, methods=['get'])
    def my_groups(self, request):
        """Get groups the current user is a member of."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user_groups = self.get_queryset().filter(
            members=request.user,
            groupmembership__status='active'
        ).order_by('-groupmembership__last_activity')
        
        serializer = PeerGroupListSerializer(user_groups, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def join(self, request, slug=None):
        """Join a peer group."""
        group = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            return Response(
                {'error': 'Authentication required.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user can join
        if not group.can_user_join(user):
            return Response(
                {'error': 'Cannot join this group.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if membership already exists
        existing_membership = GroupMembership.objects.filter(
            user=user, group=group
        ).first()
        
        if existing_membership:
            if existing_membership.status == 'active':
                return Response(
                    {'error': 'Already a member of this group.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif existing_membership.status == 'pending':
                return Response(
                    {'error': 'Membership request already pending.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = GroupJoinRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Determine membership status based on group privacy
        if group.can_join_freely:
            membership_status = 'active'
        else:
            membership_status = 'pending'
        
        # Create or update membership
        if existing_membership:
            existing_membership.status = membership_status
            existing_membership.invitation_message = serializer.validated_data.get('message', '')
            existing_membership.save()
            membership = existing_membership
        else:
            membership = GroupMembership.objects.create(
                user=user,
                group=group,
                status=membership_status,
                invitation_message=serializer.validated_data.get('message', '')
            )
        
        return Response({
            'message': 'Successfully joined group.' if membership_status == 'active' 
                      else 'Join request submitted for approval.',
            'status': membership_status
        })
    
    @action(detail=True, methods=['post'])
    def leave(self, request, slug=None):
        """Leave a peer group."""
        group = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            return Response(
                {'error': 'Authentication required.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        membership = GroupMembership.objects.filter(
            user=user, group=group, status='active'
        ).first()
        
        if not membership:
            return Response(
                {'error': 'Not a member of this group.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is the creator
        if group.created_by == user:
            return Response(
                {'error': 'Group creator cannot leave. Transfer ownership or delete the group.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update membership status
        membership.status = 'left'
        membership.save()
        
        # Remove admin privileges if any
        GroupAdminship.objects.filter(user=user, group=group).delete()
        
        return Response({'message': 'Successfully left the group.'})
    
    @action(detail=True, methods=['get'])
    def members(self, request, slug=None):
        """Get group members."""
        group = self.get_object()
        
        # Check if user can view members
        if group.privacy_level == 'private' and not group.is_member(request.user):
            return Response(
                {'error': 'Cannot view members of private group.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        memberships = GroupMembership.objects.filter(
            group=group, status='active'
        ).select_related('user').order_by('-joined_at')
        
        serializer = GroupMembershipSerializer(memberships, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def pending_members(self, request, slug=None):
        """Get pending membership requests (admins only)."""
        group = self.get_object()
        
        if not group.is_admin(request.user):
            return Response(
                {'error': 'Only group admins can view pending requests.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pending_memberships = GroupMembership.objects.filter(
            group=group, status='pending'
        ).select_related('user').order_by('joined_at')
        
        serializer = GroupMembershipSerializer(pending_memberships, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def invite_member(self, request, slug=None):
        """Invite a user to join the group (admins only)."""
        group = self.get_object()
        
        if not group.is_admin(request.user):
            return Response(
                {'error': 'Only group admins can invite members.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = GroupInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_email = serializer.validated_data['user_email']
        message = serializer.validated_data.get('message', '')
        
        try:
            invited_user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is already a member
        if group.is_member(invited_user):
            return Response(
                {'error': 'User is already a member.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update invitation
        membership, created = GroupMembership.objects.get_or_create(
            user=invited_user,
            group=group,
            defaults={
                'status': 'invited',
                'invited_by': request.user,
                'invitation_message': message
            }
        )
        
        if not created:
            membership.status = 'invited'
            membership.invited_by = request.user
            membership.invitation_message = message
            membership.save()
        
        return Response({'message': 'Invitation sent successfully.'})
    
    @action(detail=True, methods=['post'])
    def manage_member(self, request, slug=None):
        """Manage group member (approve, reject, remove, etc.)."""
        group = self.get_object()
        
        if not group.is_admin(request.user):
            return Response(
                {'error': 'Only group admins can manage members.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = GroupMemberActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        reason = serializer.validated_data.get('reason', '')
        
        # Get member from URL parameter or request data
        member_id = request.data.get('member_id')
        if not member_id:
            return Response(
                {'error': 'member_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            membership = GroupMembership.objects.get(
                group=group, user_id=member_id
            )
        except GroupMembership.DoesNotExist:
            return Response(
                {'error': 'Member not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Perform action
        if action_type == 'approve':
            membership.status = 'active'
            membership.save()
            message = 'Member approved successfully.'
        
        elif action_type == 'reject':
            membership.delete()
            message = 'Membership request rejected.'
        
        elif action_type == 'remove':
            membership.status = 'left'
            membership.save()
            # Remove admin privileges
            GroupAdminship.objects.filter(user=membership.user, group=group).delete()
            message = 'Member removed successfully.'
        
        elif action_type == 'ban':
            membership.status = 'banned'
            membership.save()
            # Remove admin privileges
            GroupAdminship.objects.filter(user=membership.user, group=group).delete()
            message = 'Member banned successfully.'
        
        elif action_type == 'promote':
            GroupAdminship.objects.get_or_create(
                user=membership.user,
                group=group,
                defaults={
                    'role': 'admin',
                    'granted_by': request.user,
                    'can_manage_members': True,
                    'can_moderate_content': True,
                    'can_edit_group': False
                }
            )
            message = 'Member promoted to admin.'
        
        elif action_type == 'demote':
            GroupAdminship.objects.filter(user=membership.user, group=group).delete()
            message = 'Admin privileges removed.'
        
        return Response({'message': message})
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending/popular groups."""
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            # Allow unauthenticated users to see trending groups
            limit = int(request.query_params.get('limit', 10))
            
            # Groups with recent activity (last 7 days)
            recent_date = timezone.now() - timedelta(days=7)
            
            trending_groups = self.get_queryset().filter(
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
                total_members=Count(
                    'members',
                    filter=Q(groupmembership__status='active')
                )
            ).filter(
                total_members__gt=0  # Only groups with members
            ).order_by('-recent_members', '-activity_score', '-total_members')[:limit]
            
            serializer = PeerGroupListSerializer(trending_groups, many=True, context={'request': request})
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error getting trending groups: {e}")
            
            # Fallback to most popular groups
            trending_groups = self.get_queryset().filter(
                is_active=True
            ).annotate(
                total_members=Count('members', filter=Q(groupmembership__status='active'))
            ).order_by('-total_members', '-activity_score')[:limit]
            
            serializer = PeerGroupListSerializer(trending_groups, many=True, context={'request': request})
            return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def similar(self, request, slug=None):
        """Get groups similar to the current group."""
        from .services import GroupMatchingService
        
        user = request.user
        if not user.is_authenticated:
            return Response(
                {'error': 'Authentication required.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        group = self.get_object()
        matching_service = GroupMatchingService()
        similar_groups = matching_service.find_similar_groups(
            reference_group=group,
            user=user,
            limit=int(request.query_params.get('limit', 5))
        )
        
        serializer = PeerGroupListSerializer(similar_groups, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search for groups with AI-enhanced results."""
        from .services import GroupMatchingService
        
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Search query is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        filters = {
            'group_type': request.query_params.get('type'),
            'industry': request.query_params.get('industry'),
            'privacy_level': request.query_params.get('privacy'),
            'location': request.query_params.get('location'),
            'min_members': request.query_params.get('min_members'),
            'max_members': request.query_params.get('max_members'),
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        matching_service = GroupMatchingService()
        search_results = matching_service.search_groups(
            query=query,
            user=user,
            filters=filters,
            limit=int(request.query_params.get('limit', 20))
        )
        
        serializer = PeerGroupListSerializer(search_results, many=True, context={'request': request})
        return Response({
            'results': serializer.data,
            'query': query,
            'filters': filters,
            'total': len(serializer.data)
        })
    
    @action(detail=True, methods=['get'])
    def activity_feed(self, request, slug=None):
        """Get activity feed for a specific group."""
        group = self.get_object()
        
        # Check if user can view group activity
        if group.privacy_level == 'private' and not group.is_member(request.user):
            return Response(
                {'error': 'Cannot view activity of private group.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get recent posts and comments
        recent_posts = GroupPost.objects.filter(
            group=group
        ).select_related('author').order_by('-created_at')[:10]
        
        recent_comments = GroupComment.objects.filter(
            post__group=group
        ).select_related('author', 'post').order_by('-created_at')[:10]
        
        # Get recent member joins
        recent_members = GroupMembership.objects.filter(
            group=group,
            status='active'
        ).select_related('user').order_by('-joined_at')[:5]
        
        # Combine and format activity items
        activity_items = []
        
        # Add posts
        for post in recent_posts:
            activity_items.append({
                'type': 'post',
                'id': post.id,
                'timestamp': post.created_at,
                'user': {
                    'id': post.author.id,
                    'name': post.author.get_full_name(),
                    'email': post.author.email,
                    'profile_picture': post.author.profile_picture.url if post.author.profile_picture else None
                },
                'content': {
                    'title': post.title,
                    'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                    'post_type': post.post_type,
                    'like_count': post.like_count,
                    'comment_count': post.comment_count
                }
            })
        
        # Add comments
        for comment in recent_comments:
            activity_items.append({
                'type': 'comment',
                'id': comment.id,
                'timestamp': comment.created_at,
                'user': {
                    'id': comment.author.id,
                    'name': comment.author.get_full_name(),
                    'email': comment.author.email,
                    'profile_picture': comment.author.profile_picture.url if comment.author.profile_picture else None
                },
                'content': {
                    'comment': comment.content[:150] + '...' if len(comment.content) > 150 else comment.content,
                    'post_title': comment.post.title,
                    'post_id': comment.post.id,
                    'like_count': comment.like_count
                }
            })
        
        # Add member joins
        for membership in recent_members:
            activity_items.append({
                'type': 'member_joined',
                'id': f"member_{membership.id}",
                'timestamp': membership.joined_at,
                'user': {
                    'id': membership.user.id,
                    'name': membership.user.get_full_name(),
                    'email': membership.user.email,
                    'profile_picture': membership.user.profile_picture.url if membership.user.profile_picture else None
                },
                'content': {
                    'message': f"joined the group"
                }
            })
        
        # Sort by timestamp (most recent first)
        activity_items.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return Response({
            'activity': activity_items[:20],  # Limit to 20 most recent items
            'group': {
                'id': group.id,
                'name': group.name,
                'slug': group.slug
            }
        })
    
    @action(detail=False, methods=['get'])
    def my_activity_feed(self, request):
        """Get activity feed for all groups the user is a member of."""
        user = request.user
        if not user.is_authenticated:
            return Response(
                {'error': 'Authentication required.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get user's groups
        user_groups = user.peer_groups.filter(
            groupmembership__status='active'
        ).values_list('id', flat=True)
        
        if not user_groups:
            return Response({
                'activity': [],
                'message': 'No group activity found. Join some groups to see activity!'
            })
        
        # Get recent activity from user's groups
        recent_posts = GroupPost.objects.filter(
            group_id__in=user_groups
        ).select_related('author', 'group').order_by('-created_at')[:15]
        
        recent_comments = GroupComment.objects.filter(
            post__group_id__in=user_groups
        ).select_related('author', 'post', 'post__group').order_by('-created_at')[:15]
        
        # Combine and format activity items
        activity_items = []
        
        # Add posts
        for post in recent_posts:
            activity_items.append({
                'type': 'post',
                'id': post.id,
                'timestamp': post.created_at,
                'group': {
                    'id': post.group.id,
                    'name': post.group.name,
                    'slug': post.group.slug
                },
                'user': {
                    'id': post.author.id,
                    'name': post.author.get_full_name(),
                    'email': post.author.email,
                    'profile_picture': post.author.profile_picture.url if post.author.profile_picture else None
                },
                'content': {
                    'title': post.title,
                    'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                    'post_type': post.post_type,
                    'like_count': post.like_count,
                    'comment_count': post.comment_count
                }
            })
        
        # Add comments
        for comment in recent_comments:
            activity_items.append({
                'type': 'comment',
                'id': comment.id,
                'timestamp': comment.created_at,
                'group': {
                    'id': comment.post.group.id,
                    'name': comment.post.group.name,
                    'slug': comment.post.group.slug
                },
                'user': {
                    'id': comment.author.id,
                    'name': comment.author.get_full_name(),
                    'email': comment.author.email,
                    'profile_picture': comment.author.profile_picture.url if comment.author.profile_picture else None
                },
                'content': {
                    'comment': comment.content[:150] + '...' if len(comment.content) > 150 else comment.content,
                    'post_title': comment.post.title,
                    'post_id': comment.post.id,
                    'like_count': comment.like_count
                }
            })
        
        # Sort by timestamp (most recent first)
        activity_items.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return Response({
            'activity': activity_items[:25],  # Limit to 25 most recent items
            'groups_count': len(user_groups)
        })


class GroupPostViewSet(ModelViewSet):
    """
    ViewSet for group posts.
    
    Provides CRUD operations for posts within peer groups.
    """
    
    serializer_class = GroupPostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get posts for a specific group."""
        group_slug = self.kwargs.get('group_slug')
        if group_slug:
            return GroupPost.objects.filter(
                group__slug=group_slug
            ).select_related('group', 'author').order_by('-is_pinned', '-created_at')
        return GroupPost.objects.none()
    
    def perform_create(self, serializer):
        """Create post in the specified group."""
        group_slug = self.kwargs.get('group_slug')
        group = get_object_or_404(PeerGroup, slug=group_slug)
        
        # Check if user is a member
        if not group.is_member(self.request.user):
            raise permissions.PermissionDenied('Must be a group member to post.')
        
        serializer.save(author=self.request.user, group=group)
    
    def update(self, request, *args, **kwargs):
        """Update post (only author or admins can edit)."""
        post = self.get_object()
        if not (post.author == request.user or post.group.is_admin(request.user)):
            return Response(
                {'error': 'Only the author or group admins can edit this post.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete post (only author or admins can delete)."""
        post = self.get_object()
        if not (post.author == request.user or post.group.is_admin(request.user)):
            return Response(
                {'error': 'Only the author or group admins can delete this post.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def like(self, request, group_slug=None, pk=None):
        """Like or unlike a post."""
        post = self.get_object()
        user = request.user
        
        # For now, we'll use a simple approach without a separate Like model
        # In a production system, you'd want a proper Like model to track individual likes
        
        # Check if user has already liked (this is a simplified check)
        # In reality, you'd check a Like model or use a JSONField to track likes
        
        # For demonstration, we'll just increment/decrement the like count
        action_taken = request.data.get('action', 'like')  # 'like' or 'unlike'
        
        if action_taken == 'like':
            post.increment_like_count()
            message = 'Post liked successfully.'
        elif action_taken == 'unlike':
            post.decrement_like_count()
            message = 'Post unliked successfully.'
        else:
            return Response(
                {'error': 'Invalid action. Use "like" or "unlike".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': message,
            'like_count': post.like_count,
            'action': action_taken
        })
    
    @action(detail=True, methods=['post'])
    def pin(self, request, group_slug=None, pk=None):
        """Pin or unpin a post (admins only)."""
        post = self.get_object()
        user = request.user
        
        # Check if user is admin
        if not post.group.is_admin(user):
            return Response(
                {'error': 'Only group admins can pin posts.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        action = request.data.get('action', 'pin')  # 'pin' or 'unpin'
        
        if action == 'pin':
            post.is_pinned = True
            message = 'Post pinned successfully.'
        elif action == 'unpin':
            post.is_pinned = False
            message = 'Post unpinned successfully.'
        else:
            return Response(
                {'error': 'Invalid action. Use "pin" or "unpin".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        post.save(update_fields=['is_pinned'])
        
        return Response({
            'message': message,
            'is_pinned': post.is_pinned
        })
    
    @action(detail=True, methods=['post'])
    def lock(self, request, group_slug=None, pk=None):
        """Lock or unlock a post (admins only)."""
        post = self.get_object()
        user = request.user
        
        # Check if user is admin
        if not post.group.is_admin(user):
            return Response(
                {'error': 'Only group admins can lock posts.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        action = request.data.get('action', 'lock')  # 'lock' or 'unlock'
        
        if action == 'lock':
            post.is_locked = True
            message = 'Post locked successfully. Comments are now disabled.'
        elif action == 'unlock':
            post.is_locked = False
            message = 'Post unlocked successfully. Comments are now enabled.'
        else:
            return Response(
                {'error': 'Invalid action. Use "lock" or "unlock".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        post.save(update_fields=['is_locked'])
        
        return Response({
            'message': message,
            'is_locked': post.is_locked
        })


class GroupCommentViewSet(ModelViewSet):
    """
    ViewSet for group post comments.
    
    Provides CRUD operations for comments on group posts.
    """
    
    serializer_class = GroupCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get comments for a specific post."""
        post_id = self.kwargs.get('post_pk')
        if post_id:
            return GroupComment.objects.filter(
                post_id=post_id
            ).select_related('post', 'author', 'parent').order_by('created_at')
        return GroupComment.objects.none()
    
    def perform_create(self, serializer):
        """Create comment on the specified post."""
        post_id = self.kwargs.get('post_pk')
        post = get_object_or_404(GroupPost, id=post_id)
        
        # Check if user is a member of the group
        if not post.group.is_member(self.request.user):
            raise permissions.PermissionDenied('Must be a group member to comment.')
        
        serializer.save(author=self.request.user, post=post)
    
    def update(self, request, *args, **kwargs):
        """Update comment (only author or admins can edit)."""
        comment = self.get_object()
        if not (comment.author == request.user or comment.post.group.is_admin(request.user)):
            return Response(
                {'error': 'Only the author or group admins can edit this comment.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete comment (only author or admins can delete)."""
        comment = self.get_object()
        if not (comment.author == request.user or comment.post.group.is_admin(request.user)):
            return Response(
                {'error': 'Only the author or group admins can delete this comment.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def like(self, request, group_slug=None, post_pk=None, pk=None):
        """Like or unlike a comment."""
        comment = self.get_object()
        user = request.user
        
        # Simple like/unlike functionality
        action_taken = request.data.get('action', 'like')  # 'like' or 'unlike'
        
        if action_taken == 'like':
            comment.increment_like_count()
            message = 'Comment liked successfully.'
        elif action_taken == 'unlike':
            comment.decrement_like_count()
            message = 'Comment unliked successfully.'
        else:
            return Response(
                {'error': 'Invalid action. Use "like" or "unlike".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': message,
            'like_count': comment.like_count,
            'action': action_taken
        })