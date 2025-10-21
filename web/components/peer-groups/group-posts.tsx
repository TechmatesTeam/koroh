'use client';

import React, { useState, useEffect } from 'react';
import { GroupPost, User } from '@/types/peer-groups';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar } from '@/components/ui/avatar';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Modal } from '@/components/ui/modal';
import { api } from '@/lib/api';
import { useNotifications } from '@/contexts/notification-context';

interface GroupPostsProps {
  groupSlug: string;
  canPost?: boolean;
  className?: string;
}

const GroupPosts: React.FC<GroupPostsProps> = ({
  groupSlug,
  canPost = false,
  className = ''
}) => {
  const [posts, setPosts] = useState<GroupPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [likeLoading, setLikeLoading] = useState<string | null>(null);
  const { addNotification } = useNotifications();

  // Form state for creating posts
  const [newPost, setNewPost] = useState({
    title: '',
    content: '',
    post_type: 'discussion' as const,
    tags: [] as string[]
  });

  useEffect(() => {
    loadPosts();
  }, [groupSlug]);

  const loadPosts = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.peerGroups.getPosts(groupSlug);
      setPosts(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load posts');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePost = async () => {
    if (!newPost.title.trim() || !newPost.content.trim()) {
      addNotification({
        type: 'error',
        title: 'Validation Error',
        message: 'Title and content are required'
      });
      return;
    }

    setCreateLoading(true);
    try {
      const response = await api.peerGroups.createPost(groupSlug, newPost);
      
      addNotification({
        type: 'success',
        title: 'Success',
        message: 'Post created successfully'
      });
      
      setShowCreateModal(false);
      setNewPost({
        title: '',
        content: '',
        post_type: 'discussion',
        tags: []
      });
      
      // Reload posts
      await loadPosts();
    } catch (err: any) {
      addNotification({
        type: 'error',
        title: 'Error',
        message: err.response?.data?.error || 'Failed to create post'
      });
    } finally {
      setCreateLoading(false);
    }
  };

  const handleLikePost = async (postId: string, currentlyLiked: boolean) => {
    setLikeLoading(postId);
    
    try {
      const action = currentlyLiked ? 'unlike' : 'like';
      await api.peerGroups.likePost(groupSlug, postId, action);
      
      // Update post in local state
      setPosts(prevPosts => 
        prevPosts.map(post => 
          post.id === postId 
            ? { 
                ...post, 
                like_count: currentlyLiked ? post.like_count - 1 : post.like_count + 1 
              }
            : post
        )
      );
    } catch (err: any) {
      addNotification({
        type: 'error',
        title: 'Error',
        message: 'Failed to update like'
      });
    } finally {
      setLikeLoading(null);
    }
  };

  const getPostTypeColor = (type: string) => {
    switch (type) {
      case 'announcement': return 'bg-red-100 text-red-800';
      case 'question': return 'bg-blue-100 text-blue-800';
      case 'resource': return 'bg-green-100 text-green-800';
      case 'event': return 'bg-purple-100 text-purple-800';
      case 'job': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${Math.floor(diffInHours)}h ago`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className={`flex justify-center py-8 ${className}`}>
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <p className="text-red-600">{error}</p>
        <Button onClick={loadPosts} className="mt-4">
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Create Post Button */}
      {canPost && (
        <div className="mb-6">
          <Button onClick={() => setShowCreateModal(true)}>
            Create New Post
          </Button>
        </div>
      )}

      {/* Posts List */}
      <div className="space-y-6">
        {posts.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Posts Yet</h3>
              <p className="text-gray-600">
                {canPost ? 'Be the first to start a discussion!' : 'No discussions have been started yet.'}
              </p>
            </div>
          </div>
        ) : (
          posts.map((post) => (
            <div key={post.id} className="bg-white border border-gray-200 rounded-lg p-6">
              {/* Post Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start space-x-3">
                  <Avatar
                    src={post.author.profile_picture}
                    alt={post.author.full_name}
                    size="md"
                  />
                  
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium text-gray-900">
                        {post.author.full_name}
                      </h4>
                      <span className="text-sm text-gray-500">
                        {formatDate(post.created_at)}
                      </span>
                      {post.is_pinned && (
                        <Badge className="bg-yellow-100 text-yellow-800">
                          Pinned
                        </Badge>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge className={getPostTypeColor(post.post_type)}>
                        {post.post_type}
                      </Badge>
                      {post.tags && post.tags.length > 0 && (
                        <div className="flex space-x-1">
                          {post.tags.slice(0, 3).map((tag, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              #{tag}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Post Actions Menu */}
                {post.can_edit && (
                  <div className="flex space-x-2">
                    <Button variant="ghost" size="sm">
                      Edit
                    </Button>
                    {post.can_delete && (
                      <Button variant="ghost" size="sm" className="text-red-600">
                        Delete
                      </Button>
                    )}
                  </div>
                )}
              </div>

              {/* Post Content */}
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {post.title}
                </h3>
                <div className="text-gray-700 whitespace-pre-wrap">
                  {post.content}
                </div>
              </div>

              {/* Post Stats and Actions */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                <div className="flex items-center space-x-6 text-sm text-gray-500">
                  <span>{post.view_count} views</span>
                  <span>{post.comment_count} comments</span>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleLikePost(post.id, false)} // TODO: Track user likes
                    disabled={likeLoading === post.id}
                    className="flex items-center space-x-1"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                    </svg>
                    <span>{post.like_count}</span>
                  </Button>
                  
                  <Button variant="ghost" size="sm" className="flex items-center space-x-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    <span>Reply</span>
                  </Button>
                  
                  <Button variant="ghost" size="sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
                    </svg>
                  </Button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Post Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Post"
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="post-type">Post Type</Label>
            <select
              id="post-type"
              value={newPost.post_type}
              onChange={(e) => setNewPost({ ...newPost, post_type: e.target.value as any })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="discussion">Discussion</option>
              <option value="question">Question</option>
              <option value="announcement">Announcement</option>
              <option value="resource">Resource Share</option>
              <option value="event">Event</option>
              <option value="job">Job Posting</option>
            </select>
          </div>

          <div>
            <Label htmlFor="post-title">Title</Label>
            <Input
              id="post-title"
              value={newPost.title}
              onChange={(e) => setNewPost({ ...newPost, title: e.target.value })}
              placeholder="Enter post title..."
              className="mt-1"
            />
          </div>

          <div>
            <Label htmlFor="post-content">Content</Label>
            <Textarea
              id="post-content"
              value={newPost.content}
              onChange={(e) => setNewPost({ ...newPost, content: e.target.value })}
              placeholder="Share your thoughts, ask a question, or start a discussion..."
              rows={6}
              className="mt-1"
            />
          </div>

          <div className="flex justify-end space-x-3">
            <Button
              variant="outline"
              onClick={() => setShowCreateModal(false)}
              disabled={createLoading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreatePost}
              disabled={createLoading || !newPost.title.trim() || !newPost.content.trim()}
            >
              {createLoading ? 'Creating...' : 'Create Post'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default GroupPosts;