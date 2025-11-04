/**
 * Mock API service for frontend-only authentication
 * This simulates a backend API using localStorage for persistence
 */

import { User, LoginCredentials, RegisterData } from '@/types';

// Mock database using localStorage
const STORAGE_KEYS = {
  USERS: 'koroh_users',
  CURRENT_USER: 'koroh_current_user',
  RESET_TOKENS: 'koroh_reset_tokens',
  PORTFOLIOS: 'koroh_portfolios',
};

// Utility functions
const generateId = () => Math.random().toString(36).substr(2, 9);
const generateToken = () => Math.random().toString(36).substr(2, 32);

// Mock delay to simulate network requests
const mockDelay = (ms: number = 500) => new Promise(resolve => setTimeout(resolve, ms));

// Storage helpers
const getUsers = (): User[] => {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.USERS) || '[]');
  } catch {
    return [];
  }
};

const saveUsers = (users: User[]) => {
  localStorage.setItem(STORAGE_KEYS.USERS, JSON.stringify(users));
};

const getCurrentUser = (): User | null => {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.CURRENT_USER) || 'null');
  } catch {
    return null;
  }
};

const setCurrentUser = (user: User | null) => {
  if (user) {
    localStorage.setItem(STORAGE_KEYS.CURRENT_USER, JSON.stringify(user));
  } else {
    localStorage.removeItem(STORAGE_KEYS.CURRENT_USER);
  }
};

const getResetTokens = (): Record<string, { email: string; expires: number }> => {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.RESET_TOKENS) || '{}');
  } catch {
    return {};
  }
};

const saveResetTokens = (tokens: Record<string, { email: string; expires: number }>) => {
  localStorage.setItem(STORAGE_KEYS.RESET_TOKENS, JSON.stringify(tokens));
};

const getPortfolios = (): any[] => {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.PORTFOLIOS) || '[]');
  } catch {
    return [];
  }
};

const savePortfolios = (portfolios: any[]) => {
  localStorage.setItem(STORAGE_KEYS.PORTFOLIOS, JSON.stringify(portfolios));
};

// Mock API implementation
export const mockApi = {
  auth: {
    async login(credentials: LoginCredentials) {
      await mockDelay();
      
      const users = getUsers();
      const user = users.find(u => u.email === credentials.email);
      
      if (!user) {
        throw new Error('User not found');
      }
      
      // In a real app, you'd hash and compare passwords
      // For this mock, we'll store a simple password field
      const userWithPassword = user as User & { password: string };
      if (userWithPassword.password !== credentials.password) {
        throw new Error('Invalid password');
      }
      
      // Check if user is verified
      if (!user.is_verified) {
        const error = new Error('Please verify your email address before logging in.');
        (error as any).verification_required = true;
        (error as any).email = user.email;
        throw error;
      }
      
      setCurrentUser(user);
      
      return {
        data: {
          access: generateToken(),
          refresh: generateToken(),
          user,
        },
      };
    },

    async register(userData: RegisterData) {
      await mockDelay();
      
      const users = getUsers();
      
      // Check if user already exists
      if (users.find(u => u.email === userData.email)) {
        throw new Error('User with this email already exists');
      }
      
      // Validate password confirmation
      if (userData.password !== userData.password_confirm) {
        throw new Error('Password confirmation does not match');
      }
      
      const newUser: User & { password: string } = {
        id: generateId(),
        email: userData.email,
        first_name: userData.first_name,
        last_name: userData.last_name,
        is_verified: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        password: userData.password, // In real app, this would be hashed
      };
      
      users.push(newUser);
      saveUsers(users);
      
      // Remove password from returned user object
      const { password, ...userWithoutPassword } = newUser;
      
      // For mock API, simulate email verification requirement
      console.log(`Verification email sent to ${userData.email}`);
      
      return {
        data: {
          message: 'Account created successfully. Please check your email to verify your account.',
          user: userWithoutPassword,
          verification_required: true,
          email: userData.email,
        },
      };
    },

    async logout() {
      await mockDelay(200);
      setCurrentUser(null);
      return { data: { message: 'Logged out successfully' } };
    },

    async requestPasswordReset(email: string) {
      await mockDelay();
      
      const users = getUsers();
      const user = users.find(u => u.email === email);
      
      if (!user) {
        // Don't reveal if user exists for security
        return { data: { message: 'If an account with this email exists, a reset link has been sent.' } };
      }
      
      const resetToken = generateToken();
      const resetTokens = getResetTokens();
      
      // Token expires in 1 hour
      resetTokens[resetToken] = {
        email,
        expires: Date.now() + 60 * 60 * 1000,
      };
      
      saveResetTokens(resetTokens);
      
      // In a real app, you'd send an email here
      // For this mock, we'll store the token and show it to the user
      console.log(`Password reset token for ${email}: ${resetToken}`);
      
      return { 
        data: { 
          message: 'If an account with this email exists, a reset link has been sent.',
          resetToken, // Only for demo purposes
        } 
      };
    },

    async resetPassword(token: string, newPassword: string) {
      await mockDelay();
      
      const resetTokens = getResetTokens();
      const tokenData = resetTokens[token];
      
      if (!tokenData || tokenData.expires < Date.now()) {
        throw new Error('Invalid or expired reset token');
      }
      
      const users = getUsers();
      const userIndex = users.findIndex(u => u.email === tokenData.email);
      
      if (userIndex === -1) {
        throw new Error('User not found');
      }
      
      // Update password
      (users[userIndex] as any).password = newPassword;
      saveUsers(users);
      
      // Remove used token
      delete resetTokens[token];
      saveResetTokens(resetTokens);
      
      return { data: { message: 'Password reset successfully' } };
    },

    async refresh(refreshToken: string) {
      await mockDelay(200);
      
      const currentUser = getCurrentUser();
      if (!currentUser) {
        throw new Error('No user logged in');
      }
      
      return {
        data: {
          access: generateToken(),
        },
      };
    },

    async verifyEmail(token: string) {
      await mockDelay();
      
      // For mock API, we'll just mark any user as verified
      const currentUser = getCurrentUser();
      if (!currentUser) {
        throw new Error('No user found for verification');
      }
      
      // Update user verification status
      const users = getUsers();
      const userIndex = users.findIndex(u => u.id === currentUser.id);
      
      if (userIndex !== -1) {
        users[userIndex].is_verified = true;
        saveUsers(users);
        
        const updatedUser = users[userIndex];
        setCurrentUser(updatedUser);
        
        return {
          data: {
            message: 'Email verified successfully',
            user: updatedUser,
            tokens: {
              access: generateToken(),
              refresh: generateToken(),
            },
          },
        };
      }
      
      throw new Error('User not found');
    },

    async resendVerification(email: string) {
      await mockDelay();
      
      const users = getUsers();
      const user = users.find(u => u.email === email);
      
      if (!user) {
        // Don't reveal if user exists for security
        return { data: { message: 'If this email is registered, a verification email will be sent.' } };
      }
      
      if (user.is_verified) {
        return { data: { message: 'This email address is already verified.' } };
      }
      
      // In a real app, you'd send an email here
      console.log(`Verification email sent to ${email}`);
      
      return { data: { message: 'Verification email sent. Please check your inbox.' } };
    },
  },

  profiles: {
    async getMe() {
      await mockDelay(200);
      
      const currentUser = getCurrentUser();
      if (!currentUser) {
        throw new Error('Not authenticated');
      }
      
      return { data: { user: currentUser } };
    },

    async updateMe(data: Partial<User>) {
      await mockDelay();
      
      const currentUser = getCurrentUser();
      if (!currentUser) {
        throw new Error('Not authenticated');
      }
      
      const updatedUser = { ...currentUser, ...data, updated_at: new Date().toISOString() };
      setCurrentUser(updatedUser);
      
      // Update in users list
      const users = getUsers();
      const userIndex = users.findIndex(u => u.id === currentUser.id);
      if (userIndex !== -1) {
        users[userIndex] = updatedUser;
        saveUsers(users);
      }
      
      return { data: { user: updatedUser } };
    },

    async getPortfolios() {
      await mockDelay(300);
      
      const currentUser = getCurrentUser();
      if (!currentUser) {
        throw new Error('Not authenticated');
      }
      
      const portfolios = getPortfolios();
      const userPortfolios = portfolios.filter(p => p.userId === currentUser.id);
      
      return { data: userPortfolios };
    },

    async generatePortfolio(data?: { portfolioName?: string; template?: string }) {
      await mockDelay(2000); // Simulate AI generation time
      
      const currentUser = getCurrentUser();
      if (!currentUser) {
        throw new Error('Not authenticated');
      }
      
      const portfolios = getPortfolios();
      const portfolioId = generateId();
      
      // Generate username from email (before @ symbol) or use first+last name
      const username = currentUser.email.split('@')[0] || 
                      `${currentUser.first_name.toLowerCase()}.${currentUser.last_name.toLowerCase()}`;
      
      // Use provided portfolio name or generate default
      const portfolioName = data?.portfolioName || 
                           `${currentUser.first_name.toLowerCase()}-${currentUser.last_name.toLowerCase()}-portfolio`;
      
      // Get current host (for development, use localhost:3000)
      const currentHost = typeof window !== 'undefined' 
        ? window.location.host 
        : 'localhost:3000';
      
      // Use http for localhost, https for production
      const protocol = currentHost.includes('localhost') ? 'http' : 'https';
      
      const newPortfolio = {
        id: portfolioId,
        userId: currentUser.id,
        username: username,
        portfolioName: portfolioName,
        url: `${protocol}://${currentHost}/@${username}/${portfolioName}`,
        template: data?.template || 'modern-pro',
        customizations: {
          theme: 'light',
          primaryColor: '#0d9488',
          font: 'inter',
          layout: 'standard',
        },
        content: {
          title: `${currentUser.first_name} ${currentUser.last_name}`,
          subtitle: 'Professional Portfolio',
          bio: 'Welcome to my professional portfolio. I am passionate about creating innovative solutions and driving meaningful impact.',
          skills: ['JavaScript', 'React', 'Node.js', 'Python', 'AWS'],
          experience: [
            {
              title: 'Senior Software Engineer',
              company: 'Tech Corp',
              duration: '2022 - Present',
              description: 'Leading development of scalable web applications.',
            }
          ],
          education: [
            {
              degree: 'Bachelor of Computer Science',
              institution: 'University of Technology',
              year: '2020',
            }
          ],
          projects: [
            {
              name: 'AI-Powered Portfolio Generator',
              description: 'Built an intelligent portfolio generation system using AWS Bedrock.',
              technologies: ['React', 'Django', 'AWS Bedrock'],
            }
          ],
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      
      portfolios.push(newPortfolio);
      savePortfolios(portfolios);
      
      return { data: newPortfolio };
    },

    async updatePortfolio(portfolioId: string, data: any) {
      await mockDelay(500);
      
      const currentUser = getCurrentUser();
      if (!currentUser) {
        throw new Error('Not authenticated');
      }
      
      const portfolios = getPortfolios();
      const portfolioIndex = portfolios.findIndex(p => p.id === portfolioId && p.userId === currentUser.id);
      
      if (portfolioIndex === -1) {
        throw new Error('Portfolio not found');
      }
      
      const updatedPortfolio = {
        ...portfolios[portfolioIndex],
        ...data,
        updated_at: new Date().toISOString(),
      };
      
      portfolios[portfolioIndex] = updatedPortfolio;
      savePortfolios(portfolios);
      
      return { data: updatedPortfolio };
    },
  },

  peerGroups: {
    async discover(params?: any) {
      await mockDelay(800);
      
      const currentUser = getCurrentUser();
      if (!currentUser) {
        throw new Error('Not authenticated');
      }
      
      // Mock AI-powered recommendations
      const mockGroups = [
        {
          id: '1',
          name: 'React Developers Network',
          slug: 'react-developers-network',
          description: 'A community for React developers to share knowledge, best practices, and collaborate on projects.',
          tagline: 'Building the future with React',
          group_type: 'skill',
          industry: 'Technology',
          skills: ['React', 'JavaScript', 'TypeScript', 'Next.js'],
          privacy_level: 'public',
          created_by: {
            id: 'user-1',
            email: 'sarah@example.com',
            first_name: 'Sarah',
            last_name: 'Johnson',
            full_name: 'Sarah Johnson',
            profile_picture: null
          },
          admins: [],
          member_count: 1247,
          post_count: 89,
          activity_score: 85.5,
          is_active: true,
          is_featured: true,
          created_at: '2024-01-15T10:00:00Z',
          updated_at: '2024-01-20T15:30:00Z',
          last_activity: '2024-01-20T15:30:00Z',
          is_member: false,
          is_admin: false,
          can_join: true,
          membership_status: null
        },
        {
          id: '2',
          name: 'AI & Machine Learning Enthusiasts',
          slug: 'ai-ml-enthusiasts',
          description: 'Exploring the frontiers of artificial intelligence and machine learning. Share research, discuss trends, and collaborate on AI projects.',
          tagline: 'Shaping the future with AI',
          group_type: 'industry',
          industry: 'Technology',
          skills: ['Machine Learning', 'Python', 'TensorFlow', 'PyTorch', 'Data Science'],
          privacy_level: 'public',
          created_by: {
            id: 'user-2',
            email: 'alex@example.com',
            first_name: 'Alex',
            last_name: 'Chen',
            full_name: 'Alex Chen',
            profile_picture: null
          },
          admins: [],
          member_count: 892,
          post_count: 156,
          activity_score: 92.3,
          is_active: true,
          is_featured: true,
          created_at: '2024-01-10T08:00:00Z',
          updated_at: '2024-01-20T14:20:00Z',
          last_activity: '2024-01-20T14:20:00Z',
          is_member: false,
          is_admin: false,
          can_join: true,
          membership_status: null
        },
        {
          id: '3',
          name: 'Startup Founders Circle',
          slug: 'startup-founders-circle',
          description: 'A private community for startup founders to share experiences, seek advice, and build meaningful connections.',
          tagline: 'Building tomorrow, together',
          group_type: 'experience',
          industry: 'Startup',
          skills: ['Entrepreneurship', 'Leadership', 'Product Management', 'Fundraising'],
          privacy_level: 'restricted',
          created_by: {
            id: 'user-3',
            email: 'maria@example.com',
            first_name: 'Maria',
            last_name: 'Rodriguez',
            full_name: 'Maria Rodriguez',
            profile_picture: null
          },
          admins: [],
          member_count: 234,
          post_count: 67,
          activity_score: 78.9,
          is_active: true,
          is_featured: false,
          created_at: '2024-01-05T12:00:00Z',
          updated_at: '2024-01-19T16:45:00Z',
          last_activity: '2024-01-19T16:45:00Z',
          is_member: false,
          is_admin: false,
          can_join: true,
          membership_status: null
        }
      ];
      
      const recommendations = mockGroups.map(group => ({
        group,
        score: Math.random() * 100,
        reason: 'Based on your skills and interests',
        matching_skills: group.skills.slice(0, 2)
      }));
      
      return {
        data: {
          recommendations,
          total: recommendations.length,
          ai_powered: true
        }
      };
    },

    async search(params: any) {
      await mockDelay(600);
      
      // Mock search results based on query
      const mockResults = [
        {
          id: '4',
          name: 'UX/UI Designers Hub',
          slug: 'ux-ui-designers-hub',
          description: 'A creative space for UX/UI designers to showcase work, get feedback, and discuss design trends.',
          tagline: 'Design that matters',
          group_type: 'skill',
          industry: 'Design',
          skills: ['UI Design', 'UX Research', 'Figma', 'Prototyping'],
          privacy_level: 'public',
          created_by: {
            id: 'user-4',
            email: 'emma@example.com',
            first_name: 'Emma',
            last_name: 'Wilson',
            full_name: 'Emma Wilson',
            profile_picture: null
          },
          admins: [],
          member_count: 567,
          post_count: 123,
          activity_score: 88.7,
          is_active: true,
          is_featured: false,
          created_at: '2024-01-12T09:00:00Z',
          updated_at: '2024-01-20T11:15:00Z',
          last_activity: '2024-01-20T11:15:00Z',
          is_member: false,
          is_admin: false,
          can_join: true,
          membership_status: null
        }
      ];
      
      return {
        data: {
          results: mockResults,
          query: params.q || '',
          filters: params,
          total: mockResults.length
        }
      };
    },

    async trending(params?: any) {
      await mockDelay(500);
      
      const mockTrending = [
        {
          id: '5',
          name: 'Remote Work Champions',
          slug: 'remote-work-champions',
          description: 'Tips, tools, and strategies for thriving in remote work environments.',
          tagline: 'Work from anywhere, excel everywhere',
          group_type: 'interest',
          industry: 'General',
          skills: ['Remote Work', 'Productivity', 'Communication', 'Time Management'],
          privacy_level: 'public',
          created_by: {
            id: 'user-5',
            email: 'david@example.com',
            first_name: 'David',
            last_name: 'Kim',
            full_name: 'David Kim',
            profile_picture: null
          },
          admins: [],
          member_count: 1834,
          post_count: 245,
          activity_score: 95.2,
          is_active: true,
          is_featured: true,
          created_at: '2024-01-08T14:00:00Z',
          updated_at: '2024-01-20T17:00:00Z',
          last_activity: '2024-01-20T17:00:00Z',
          is_member: false,
          is_admin: false,
          can_join: true,
          membership_status: null
        }
      ];
      
      return { data: mockTrending };
    },

    async get(slug: string) {
      await mockDelay(400);
      
      // Mock detailed group data
      const mockGroup = {
        id: '1',
        name: 'React Developers Network',
        slug: 'react-developers-network',
        description: 'A community for React developers to share knowledge, best practices, and collaborate on projects. We welcome developers of all skill levels, from beginners learning their first hooks to senior engineers architecting complex applications.',
        tagline: 'Building the future with React',
        group_type: 'skill',
        industry: 'Technology',
        skills: ['React', 'JavaScript', 'TypeScript', 'Next.js', 'Redux', 'GraphQL'],
        experience_level: 'All Levels',
        location: 'Global',
        privacy_level: 'public',
        max_members: null,
        created_by: {
          id: 'user-1',
          email: 'sarah@example.com',
          first_name: 'Sarah',
          last_name: 'Johnson',
          full_name: 'Sarah Johnson',
          profile_picture: null
        },
        admins: [],
        image: null,
        cover_image: null,
        rules: 'Be respectful and constructive in all interactions.\nShare knowledge and help others learn.\nNo spam or self-promotion without context.\nKeep discussions relevant to React and web development.',
        welcome_message: 'Welcome to the React Developers Network! We\'re excited to have you join our community of passionate React developers.',
        is_active: true,
        is_featured: true,
        member_count: 1247,
        post_count: 89,
        activity_score: 85.5,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-20T15:30:00Z',
        last_activity: '2024-01-20T15:30:00Z',
        recent_members: [
          {
            id: 'user-6',
            email: 'jane@example.com',
            first_name: 'Jane',
            last_name: 'Smith',
            full_name: 'Jane Smith',
            profile_picture: null
          }
        ],
        is_member: false,
        is_admin: false,
        can_join: true,
        membership_status: null
      };
      
      return { data: mockGroup };
    },

    async join(slug: string, data?: any) {
      await mockDelay(800);
      
      return {
        data: {
          message: 'Successfully joined the group!',
          status: 'active'
        }
      };
    },

    async leave(slug: string) {
      await mockDelay(600);
      
      return {
        data: {
          message: 'Successfully left the group.'
        }
      };
    },

    async getMembers(slug: string) {
      await mockDelay(400);
      
      const mockMembers = [
        {
          id: '1',
          user: {
            id: 'user-1',
            email: 'sarah@example.com',
            first_name: 'Sarah',
            last_name: 'Johnson',
            full_name: 'Sarah Johnson',
            profile_picture: null
          },
          group: '1',
          group_name: 'React Developers Network',
          status: 'active',
          role: 'admin',
          joined_at: '2024-01-15T10:00:00Z',
          last_activity: '2024-01-20T15:30:00Z',
          post_count: 15,
          comment_count: 42,
          notifications_enabled: true,
          email_notifications: true
        }
      ];
      
      return { data: mockMembers };
    },

    async getPendingMembers(slug: string) {
      await mockDelay(400);
      return { data: [] };
    },

    async getActivityFeed(slug: string) {
      await mockDelay(500);
      
      const mockActivity = [
        {
          type: 'post',
          id: 'post-1',
          timestamp: '2024-01-20T15:30:00Z',
          user: {
            id: 'user-1',
            email: 'sarah@example.com',
            first_name: 'Sarah',
            last_name: 'Johnson',
            full_name: 'Sarah Johnson',
            profile_picture: null
          },
          content: {
            title: 'Best practices for React hooks',
            content: 'Let\'s discuss some advanced patterns for using React hooks effectively...',
            post_type: 'discussion',
            like_count: 12,
            comment_count: 5
          }
        }
      ];
      
      return {
        data: {
          activity: mockActivity,
          group: {
            id: '1',
            name: 'React Developers Network',
            slug: 'react-developers-network'
          }
        }
      };
    },

    // Placeholder methods for other endpoints
    async myGroups() { await mockDelay(400); return { data: [] }; },
    async list(params?: any) { await mockDelay(400); return { data: [] }; },
    async create(data: any) { await mockDelay(800); return { data: {} }; },
    async update(slug: string, data: any) { await mockDelay(600); return { data: {} }; },
    async delete(slug: string) { await mockDelay(600); return { data: {} }; },
    async inviteMember(slug: string, data: any) { await mockDelay(600); return { data: {} }; },
    async manageMember(slug: string, data: any) { await mockDelay(600); return { data: {} }; },
    async getMyActivityFeed() { await mockDelay(500); return { data: { activity: [] } }; },
    async getSimilar(slug: string, params?: any) { await mockDelay(400); return { data: [] }; },
    async getPosts(slug: string, params?: any) { await mockDelay(400); return { data: [] }; },
    async createPost(slug: string, data: any) { await mockDelay(600); return { data: {} }; },
    async updatePost(slug: string, postId: string, data: any) { await mockDelay(600); return { data: {} }; },
    async deletePost(slug: string, postId: string) { await mockDelay(600); return { data: {} }; },
    async likePost(slug: string, postId: string, action: string) { await mockDelay(300); return { data: {} }; },
    async getComments(slug: string, postId: string, params?: any) { await mockDelay(400); return { data: [] }; },
    async createComment(slug: string, postId: string, data: any) { await mockDelay(600); return { data: {} }; },
    async updateComment(slug: string, postId: string, commentId: string, data: any) { await mockDelay(600); return { data: {} }; },
    async deleteComment(slug: string, postId: string, commentId: string) { await mockDelay(600); return { data: {} }; },
    async likeComment(slug: string, postId: string, commentId: string, action: string) { await mockDelay(300); return { data: {} }; },
  },

  // Initialize with demo users
  async initializeDemoData() {
    const users = getUsers();
    
    if (users.length === 0) {
      const demoUsers = [
        {
          id: 'demo-user-1',
          email: 'demo@koroh.com',
          first_name: 'Demo',
          last_name: 'User',
          is_verified: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          password: 'demo123',
        },
        {
          id: 'john-doe',
          email: 'john@example.com',
          first_name: 'John',
          last_name: 'Doe',
          is_verified: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          password: 'password123',
        },
      ];
      
      saveUsers(demoUsers);
    }
  },

  jobs: {
    async search(params: any) {
      await mockDelay(600);
      
      const mockJobs = [
        {
          id: '1',
          title: 'Senior Frontend Developer',
          company: {
            id: 'comp-1',
            name: 'TechCorp Inc.',
            logo: null,
            industry: 'Technology',
            size: '100-500',
            location: 'San Francisco, CA'
          },
          location: 'San Francisco, CA',
          type: 'Full-time',
          remote: true,
          salary_range: '$120,000 - $160,000',
          description: 'We are looking for a Senior Frontend Developer to join our growing team. You will be responsible for building modern web applications using React and TypeScript.',
          requirements: [
            '5+ years of experience with React',
            'Strong TypeScript skills',
            'Experience with modern build tools',
            'Knowledge of testing frameworks'
          ],
          skills: ['React', 'TypeScript', 'JavaScript', 'CSS', 'HTML'],
          posted_date: '2024-01-18T10:00:00Z',
          application_deadline: '2024-02-18T23:59:59Z',
          is_applied: false,
          is_saved: false,
          match_score: 85
        },
        {
          id: '2',
          title: 'Full Stack Engineer',
          company: {
            id: 'comp-2',
            name: 'StartupXYZ',
            logo: null,
            industry: 'Fintech',
            size: '10-50',
            location: 'New York, NY'
          },
          location: 'New York, NY',
          type: 'Full-time',
          remote: false,
          salary_range: '$100,000 - $140,000',
          description: 'Join our fast-growing fintech startup as a Full Stack Engineer. You will work on both frontend and backend systems.',
          requirements: [
            '3+ years of full stack development',
            'Experience with Node.js and React',
            'Database design experience',
            'API development skills'
          ],
          skills: ['React', 'Node.js', 'PostgreSQL', 'REST APIs', 'AWS'],
          posted_date: '2024-01-17T14:30:00Z',
          application_deadline: '2024-02-17T23:59:59Z',
          is_applied: false,
          is_saved: true,
          match_score: 78
        },
        {
          id: '3',
          title: 'AI/ML Engineer',
          company: {
            id: 'comp-3',
            name: 'AI Innovations',
            logo: null,
            industry: 'Artificial Intelligence',
            size: '50-100',
            location: 'Seattle, WA'
          },
          location: 'Seattle, WA',
          type: 'Full-time',
          remote: true,
          salary_range: '$140,000 - $180,000',
          description: 'We are seeking an AI/ML Engineer to develop and deploy machine learning models at scale.',
          requirements: [
            'PhD or Masters in Computer Science/ML',
            'Experience with TensorFlow/PyTorch',
            'Strong Python programming skills',
            'Experience with cloud platforms'
          ],
          skills: ['Python', 'TensorFlow', 'PyTorch', 'AWS', 'Machine Learning'],
          posted_date: '2024-01-16T09:15:00Z',
          application_deadline: '2024-02-16T23:59:59Z',
          is_applied: true,
          is_saved: false,
          match_score: 92
        }
      ];

      // Filter based on search params
      let filteredJobs = mockJobs;
      
      if (params?.search) {
        const searchTerm = params.search.toLowerCase();
        filteredJobs = filteredJobs.filter(job => 
          job.title.toLowerCase().includes(searchTerm) ||
          job.company.name.toLowerCase().includes(searchTerm) ||
          job.skills.some(skill => skill.toLowerCase().includes(searchTerm))
        );
      }

      if (params?.location) {
        filteredJobs = filteredJobs.filter(job => 
          job.location.toLowerCase().includes(params.location.toLowerCase())
        );
      }

      if (params?.remote !== undefined) {
        filteredJobs = filteredJobs.filter(job => job.remote === params.remote);
      }

      if (params?.job_type) {
        filteredJobs = filteredJobs.filter(job => job.type === params.job_type);
      }

      // Pagination
      const page = parseInt(params?.page) || 1;
      const pageSize = parseInt(params?.page_size) || 10;
      const startIndex = (page - 1) * pageSize;
      const endIndex = startIndex + pageSize;
      const paginatedJobs = filteredJobs.slice(startIndex, endIndex);

      return {
        data: {
          results: paginatedJobs,
          count: filteredJobs.length,
          next: endIndex < filteredJobs.length ? `?page=${page + 1}` : null,
          previous: page > 1 ? `?page=${page - 1}` : null
        }
      };
    },

    async getRecommendations() {
      await mockDelay(800);
      
      const mockRecommendations = [
        {
          id: '1',
          title: 'Senior Frontend Developer',
          company: {
            id: 'comp-1',
            name: 'TechCorp Inc.',
            logo: null,
            industry: 'Technology'
          },
          location: 'San Francisco, CA',
          type: 'Full-time',
          remote: true,
          salary_range: '$120,000 - $160,000',
          match_score: 95,
          match_reasons: ['Skills match', 'Experience level', 'Location preference']
        }
      ];

      return { data: { recommendations: mockRecommendations } };
    },

    async apply(jobId: string) {
      await mockDelay(500);
      
      return {
        data: {
          message: 'Application submitted successfully',
          application_id: generateId()
        }
      };
    }
  },

  companies: {
    async search(params: any) {
      await mockDelay(500);
      
      const mockCompanies = [
        {
          id: 'comp-1',
          name: 'TechCorp Inc.',
          logo: null,
          industry: 'Technology',
          size: '100-500',
          location: 'San Francisco, CA',
          description: 'Leading technology company focused on innovative software solutions.',
          website: 'https://techcorp.com',
          founded: 2015,
          employees: 350,
          is_following: false,
          open_positions: 12,
          rating: 4.5,
          culture_tags: ['Innovation', 'Work-life balance', 'Growth opportunities']
        },
        {
          id: 'comp-2',
          name: 'StartupXYZ',
          logo: null,
          industry: 'Fintech',
          size: '10-50',
          location: 'New York, NY',
          description: 'Fast-growing fintech startup revolutionizing digital payments.',
          website: 'https://startupxyz.com',
          founded: 2020,
          employees: 25,
          is_following: true,
          open_positions: 5,
          rating: 4.2,
          culture_tags: ['Fast-paced', 'Equity', 'Remote-friendly']
        },
        {
          id: 'comp-3',
          name: 'AI Innovations',
          logo: null,
          industry: 'Artificial Intelligence',
          size: '50-100',
          location: 'Seattle, WA',
          description: 'Cutting-edge AI research and development company.',
          website: 'https://ai-innovations.com',
          founded: 2018,
          employees: 75,
          is_following: false,
          open_positions: 8,
          rating: 4.7,
          culture_tags: ['Research', 'Innovation', 'Flexible hours']
        }
      ];

      // Filter based on search params
      let filteredCompanies = mockCompanies;
      
      if (params?.search) {
        const searchTerm = params.search.toLowerCase();
        filteredCompanies = filteredCompanies.filter(company => 
          company.name.toLowerCase().includes(searchTerm) ||
          company.industry.toLowerCase().includes(searchTerm) ||
          company.description.toLowerCase().includes(searchTerm)
        );
      }

      if (params?.industry) {
        filteredCompanies = filteredCompanies.filter(company => 
          company.industry.toLowerCase().includes(params.industry.toLowerCase())
        );
      }

      if (params?.location) {
        filteredCompanies = filteredCompanies.filter(company => 
          company.location.toLowerCase().includes(params.location.toLowerCase())
        );
      }

      if (params?.size) {
        filteredCompanies = filteredCompanies.filter(company => company.size === params.size);
      }

      // Pagination
      const page = parseInt(params?.page) || 1;
      const pageSize = parseInt(params?.page_size) || 10;
      const startIndex = (page - 1) * pageSize;
      const endIndex = startIndex + pageSize;
      const paginatedCompanies = filteredCompanies.slice(startIndex, endIndex);

      return {
        data: {
          results: paginatedCompanies,
          count: filteredCompanies.length,
          next: endIndex < filteredCompanies.length ? `?page=${page + 1}` : null,
          previous: page > 1 ? `?page=${page - 1}` : null
        }
      };
    },

    async follow(companyId: string) {
      await mockDelay(300);
      
      return {
        data: {
          message: 'Company followed successfully',
          is_following: true
        }
      };
    },

    async unfollow(companyId: string) {
      await mockDelay(300);
      
      return {
        data: {
          message: 'Company unfollowed successfully',
          is_following: false
        }
      };
    },

    async getInsights(companyId: string) {
      await mockDelay(700);
      
      return {
        data: {
          company_id: companyId,
          insights: {
            growth_trend: 'positive',
            hiring_trend: 'increasing',
            recent_news: [
              'Raised $50M Series B funding',
              'Expanded to European markets',
              'Launched new AI product line'
            ],
            employee_satisfaction: 4.3,
            work_life_balance: 4.1,
            career_opportunities: 4.5
          }
        }
      };
    }
  },
};

// Initialize demo data on module load
if (typeof window !== 'undefined') {
  mockApi.initializeDemoData();
}