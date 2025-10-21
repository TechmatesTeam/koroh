// Enhanced Peer Group Types
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  profile_picture?: string;
}

export interface PeerGroup {
  id: string;
  name: string;
  slug: string;
  description: string;
  tagline?: string;
  group_type: 'industry' | 'skill' | 'location' | 'experience' | 'interest' | 'company' | 'education' | 'general';
  industry?: string;
  skills: string[];
  experience_level?: string;
  location?: string;
  privacy_level: 'public' | 'private' | 'restricted';
  max_members?: number;
  created_by: User;
  admins: User[];
  image?: string;
  cover_image?: string;
  rules?: string;
  welcome_message?: string;
  is_active: boolean;
  is_featured: boolean;
  member_count: number;
  post_count: number;
  activity_score: number;
  created_at: string;
  updated_at: string;
  last_activity: string;
  recent_members?: User[];
  is_member: boolean;
  is_admin: boolean;
  can_join: boolean;
  membership_status?: 'active' | 'pending' | 'invited' | 'banned' | 'left';
}

export interface GroupMembership {
  id: string;
  user: User;
  group: string;
  group_name: string;
  status: 'active' | 'pending' | 'invited' | 'banned' | 'left';
  role: 'member' | 'moderator' | 'admin';
  joined_at: string;
  invited_by?: User;
  invitation_message?: string;
  last_activity: string;
  post_count: number;
  comment_count: number;
  notifications_enabled: boolean;
  email_notifications: boolean;
}

export interface GroupPost {
  id: string;
  group: string;
  group_name: string;
  author: User;
  title: string;
  content: string;
  post_type: 'discussion' | 'question' | 'announcement' | 'resource' | 'event' | 'job';
  is_pinned: boolean;
  is_locked: boolean;
  tags: string[];
  like_count: number;
  comment_count: number;
  view_count: number;
  created_at: string;
  updated_at: string;
  can_edit: boolean;
  can_delete: boolean;
}

export interface GroupComment {
  id: string;
  post: string;
  author: User;
  parent?: string;
  content: string;
  like_count: number;
  created_at: string;
  updated_at: string;
  replies: GroupComment[];
  can_edit: boolean;
  can_delete: boolean;
}

export interface GroupRecommendation {
  group: PeerGroup;
  score?: number;
  reason?: string;
  matching_skills?: string[];
  matching_industry?: boolean;
}

export interface GroupSearchFilters {
  group_type?: string;
  industry?: string;
  privacy?: string;
  location?: string;
  min_members?: number;
  max_members?: number;
}

export interface GroupSearchParams extends GroupSearchFilters {
  q?: string;
  limit?: number;
  exclude_joined?: boolean;
}

export interface ActivityItem {
  type: 'post' | 'comment' | 'member_joined';
  id: string;
  timestamp: string;
  user: User;
  group?: {
    id: string;
    name: string;
    slug: string;
  };
  content: {
    title?: string;
    content?: string;
    comment?: string;
    post_title?: string;
    post_id?: string;
    message?: string;
    like_count?: number;
    comment_count?: number;
    post_type?: string;
  };
}

export interface JoinGroupRequest {
  message?: string;
}

export interface InviteUserRequest {
  user_email: string;
  message?: string;
}

export interface MemberActionRequest {
  action: 'approve' | 'reject' | 'remove' | 'promote' | 'demote' | 'ban';
  reason?: string;
}