'use client';

import { useEffect } from 'react';
import { Metadata } from 'next';
import Link from 'next/link';
import { usePreventRefresh } from '@/lib/hooks/use-prevent-refresh';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { DashboardSkeleton } from '@/components/ui/skeleton';
import { useAuth } from '@/contexts/auth-context';
import { useDashboard } from '@/lib/hooks/use-dashboard';
import { useDashboardRealtime, useRealtimeNotifications } from '@/lib/hooks/use-realtime';
import { RealtimeStatus } from '@/components/ui/realtime-indicator';
import { RealtimeJobUpdates } from '@/components/jobs/realtime-job-updates';
import { 
  Upload, 
  FileText, 
  Briefcase, 
  Building2, 
  Users, 
  TrendingUp, 
  Star,
  MapPin,
  Clock,
  ArrowRight,
  Sparkles,
  Target,
  MessageSquare
} from 'lucide-react';

interface JobRecommendation {
  id: string;
  title: string;
  company: {
    id: string;
    name: string;
    logo?: string;
    industry: string;
  };
  location: string;
  type: string;
  remote: boolean;
  salary_range?: string;
  match_score?: number;
  match_reasons?: string[];
  posted_date: string;
}

interface Company {
  id: string;
  name: string;
  logo?: string;
  industry: string;
  size: string;
  location: string;
  description: string;
  is_following: boolean;
  open_positions: number;
  rating?: number;
}

interface PeerGroup {
  id: string;
  name: string;
  slug: string;
  description: string;
  member_count: number;
  activity_score: number;
  is_member: boolean;
}

export default function Dashboard() {
  const { user } = useAuth();
  const { handleClick } = usePreventRefresh();
  const {
    data,
    isLoading,
    error,
    followCompany,
    joinPeerGroup,
    applyToJob,
    refresh,
  } = useDashboard();

  // Real-time connections
  const dashboardRealtime = useDashboardRealtime({
    autoConnect: !!user,
    onConnect: () => {
      console.log('Dashboard WebSocket connected');
    }
  });

  const notificationRealtime = useRealtimeNotifications({
    autoConnect: !!user,
    onConnect: () => {
      console.log('Notifications WebSocket connected');
    }
  });

  // Extract data from the dashboard hook
  const {
    jobRecommendations,
    companies,
    peerGroups,
    profileCompletion,
    stats,
  } = data;

  // Handle real-time dashboard updates
  useEffect(() => {
    if (dashboardRealtime.shouldRefresh) {
      refresh();
      dashboardRealtime.clearUpdates();
    }
  }, [dashboardRealtime.shouldRefresh, dashboardRealtime, refresh]);

  // Handle real-time updates - the dashboard hook manages the data updates
  useEffect(() => {
    if (!dashboardRealtime.connection) return;

    const handleJobRecommendationUpdate = (data: any) => {
      if (data.recommendations && data.recommendations.length > 0) {
        refresh(); // Refresh dashboard data
      }
    };

    const handleCompanyUpdate = (data: any) => {
      refresh(); // Refresh dashboard data
    };

    const handleProfileUpdate = (data: any) => {
      refresh(); // Refresh dashboard data
    };

    dashboardRealtime.on('job_recommendation_update', handleJobRecommendationUpdate);
    dashboardRealtime.on('company_update', handleCompanyUpdate);
    dashboardRealtime.on('profile_update', handleProfileUpdate);

    return () => {
      dashboardRealtime.off('job_recommendation_update', handleJobRecommendationUpdate);
      dashboardRealtime.off('company_update', handleCompanyUpdate);
      dashboardRealtime.off('profile_update', handleProfileUpdate);
    };
  }, [dashboardRealtime, refresh]);

  // Optimized action handlers to prevent page refreshes
  const handleApplyToJob = async (jobId: string) => {
    try {
      await applyToJob(jobId);
      // Component-based update - no page refresh needed
    } catch (error) {
      console.error('Failed to apply to job:', error);
    }
  };

  const handleFollowCompany = async (companyId: string) => {
    try {
      await followCompany(companyId);
      // Component-based update - no page refresh needed
    } catch (error) {
      console.error('Failed to follow company:', error);
    }
  };

  const handleJoinPeerGroup = async (groupSlug: string) => {
    try {
      await joinPeerGroup(groupSlug);
      // Component-based update - no page refresh needed
    } catch (error) {
      console.error('Failed to join peer group:', error);
    }
  };

  if (isLoading) {
    return (
      <ProtectedRoute>
        <AppLayout>
          <div className="animate-fade-in">
            <DashboardSkeleton />
          </div>
        </AppLayout>
      </ProtectedRoute>
    );
  }
  return (
    <ProtectedRoute>
      <AppLayout>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Welcome Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Good morning, {user?.first_name || 'there'}!
                </h1>
                <p className="text-gray-600 mt-2">Here's what's happening in your professional network today.</p>
              </div>
              <RealtimeStatus className="hidden md:flex" />
            </div>
          </div>

          {/* Dashboard Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
            {/* Main Content - 3 columns */}
            <div className="lg:col-span-3 space-y-6 animate-fade-in-left animate-delay-200">
              {/* Quick Actions */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Sparkles className="w-5 h-5 mr-2 text-teal-600" />
                    Quick Actions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Link href="/profile/cv-upload">
                      <div className="p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-teal-500 hover:bg-teal-50 transition-all cursor-pointer group">
                        <div className="text-center">
                          <Upload className="w-8 h-8 text-gray-400 group-hover:text-teal-600 mx-auto mb-3 transition-colors" />
                          <p className="font-medium text-gray-900 group-hover:text-teal-900">Upload CV</p>
                          <p className="text-sm text-gray-500 mt-1">Get AI-powered insights</p>
                        </div>
                      </div>
                    </Link>
                    <Link href="/portfolio/generate">
                      <div className="p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-teal-500 hover:bg-teal-50 transition-all cursor-pointer group">
                        <div className="text-center">
                          <FileText className="w-8 h-8 text-gray-400 group-hover:text-teal-600 mx-auto mb-3 transition-colors" />
                          <p className="font-medium text-gray-900 group-hover:text-teal-900">Generate Portfolio</p>
                          <p className="text-sm text-gray-500 mt-1">Create professional site</p>
                        </div>
                      </div>
                    </Link>
                    <Link href="/network/discover">
                      <div className="p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-teal-500 hover:bg-teal-50 transition-all cursor-pointer group">
                        <div className="text-center">
                          <Users className="w-8 h-8 text-gray-400 group-hover:text-teal-600 mx-auto mb-3 transition-colors" />
                          <p className="font-medium text-gray-900 group-hover:text-teal-900">Find Peers</p>
                          <p className="text-sm text-gray-500 mt-1">Expand your network</p>
                        </div>
                      </div>
                    </Link>
                  </div>
                </CardContent>
              </Card>

              {/* AI Job Recommendations */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="flex items-center">
                    <Target className="w-5 h-5 mr-2 text-teal-600" />
                    AI Job Recommendations
                  </CardTitle>
                  <Link href="/jobs">
                    <Button variant="ghost" size="sm" className="text-teal-600 hover:text-teal-700">
                      View All <ArrowRight className="w-4 h-4 ml-1" />
                    </Button>
                  </Link>
                </CardHeader>
                <CardContent>
                  {jobRecommendations.length > 0 ? (
                    <div className="space-y-4">
                      {jobRecommendations.slice(0, 3).map((job, index) => (
                        <div 
                          key={job.id} 
                          className="border border-gray-200 rounded-lg p-4 hover-lift hover:border-indigo-200 transition-all duration-300 animate-fade-in-up group cursor-pointer"
                          style={{ animationDelay: `${index * 0.1}s` }}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h3 className="font-semibold text-gray-900">{job.title}</h3>
                              <p className="text-teal-600 font-medium">{job.company.name}</p>
                              <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                                <span className="flex items-center">
                                  <MapPin className="w-4 h-4 mr-1" />
                                  {job.location}
                                </span>
                                <span className="flex items-center">
                                  <Clock className="w-4 h-4 mr-1" />
                                  {new Date(job.posted_date).toLocaleDateString()}
                                </span>
                              </div>
                              {job.match_score && (
                                <div className="flex items-center mt-2">
                                  <div className="flex items-center">
                                    <Star className="w-4 h-4 text-yellow-400 fill-current" />
                                    <span className="text-sm text-gray-600 ml-1">{job.match_score}% match</span>
                                  </div>
                                </div>
                              )}
                            </div>
                            <Button 
                              size="sm" 
                              className="bg-gradient-to-r from-teal-600 to-blue-600 hover:from-teal-700 hover:to-blue-700 transform transition-all duration-300 group-hover:scale-105"
                              onClick={handleClick(() => handleApplyToJob(job.id))}
                              animated={true}
                            >
                              Apply
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Briefcase className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600">No job recommendations available yet.</p>
                      <p className="text-sm text-gray-500 mt-1">Upload your CV to get personalized recommendations.</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Company Insights */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="flex items-center">
                    <Building2 className="w-5 h-5 mr-2 text-teal-600" />
                    Companies to Watch
                  </CardTitle>
                  <Link href="/companies">
                    <Button variant="ghost" size="sm" className="text-teal-600 hover:text-teal-700">
                      Explore <ArrowRight className="w-4 h-4 ml-1" />
                    </Button>
                  </Link>
                </CardHeader>
                <CardContent>
                  {companies.length > 0 ? (
                    <div className="grid md:grid-cols-2 gap-4">
                      {companies.slice(0, 2).map((company, index) => (
                        <div 
                          key={company.id} 
                          className="border border-gray-200 rounded-lg p-4 hover-lift hover:border-blue-200 transition-all duration-300 animate-fade-in-up group cursor-pointer"
                          style={{ animationDelay: `${index * 0.15}s` }}
                        >
                          <div className="flex items-center space-x-3 mb-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                              {company.logo ? (
                                <img src={company.logo} alt={company.name} className="w-8 h-8 rounded" />
                              ) : (
                                <span className="text-white font-semibold text-sm">
                                  {company.name.charAt(0)}
                                </span>
                              )}
                            </div>
                            <div>
                              <h3 className="font-semibold text-gray-900">{company.name}</h3>
                              <p className="text-sm text-gray-500">{company.industry}</p>
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">Rating</span>
                            <span className="font-semibold text-green-600">
                              {company.rating ? `${company.rating}/5` : 'N/A'}
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                            <div 
                              className="bg-green-500 h-2 rounded-full" 
                              style={{ width: `${(company.rating || 0) * 20}%` }}
                            ></div>
                          </div>
                          <div className="flex justify-between items-center mt-3">
                            <span className="text-sm text-gray-600">{company.open_positions} open positions</span>
                            <Button 
                              size="sm" 
                              variant={company.is_following ? "default" : "outline"}
                              onClick={handleClick(() => {
                                if (!company.is_following) {
                                  handleFollowCompany(company.id);
                                }
                              })}
                              disabled={company.is_following}
                            >
                              {company.is_following ? 'Following' : 'Follow'}
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Building2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600">No company recommendations available yet.</p>
                      <p className="text-sm text-gray-500 mt-1">Complete your profile to get company suggestions.</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Peer Group Suggestions */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="flex items-center">
                    <Users className="w-5 h-5 mr-2 text-teal-600" />
                    Recommended Peer Groups
                  </CardTitle>
                  <Link href="/peer-groups">
                    <Button variant="ghost" size="sm" className="text-teal-600 hover:text-teal-700">
                      See All <ArrowRight className="w-4 h-4 ml-1" />
                    </Button>
                  </Link>
                </CardHeader>
                <CardContent>
                  {peerGroups.length > 0 ? (
                    <div className="space-y-4">
                      {peerGroups.slice(0, 2).map((group) => (
                        <div key={group.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h3 className="font-semibold text-gray-900">{group.name}</h3>
                              <p className="text-sm text-gray-600 mt-1">{group.description}</p>
                              <div className="flex items-center space-x-4 mt-3 text-sm text-gray-500">
                                <span>{group.member_count.toLocaleString()} members</span>
                                <span>•</span>
                                <span>
                                  {group.activity_score > 80 ? 'Very Active' : 
                                   group.activity_score > 60 ? 'Active' : 'Moderate'}
                                </span>
                              </div>
                            </div>
                            <Button 
                              size="sm" 
                              className={group.is_member ? "bg-gray-600" : "bg-teal-600 hover:bg-teal-700"}
                              onClick={handleClick(() => {
                                if (!group.is_member) {
                                  handleJoinPeerGroup(group.slug);
                                }
                              })}
                              disabled={group.is_member}
                            >
                              {group.is_member ? 'Joined' : 'Join'}
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600">No peer group recommendations available yet.</p>
                      <p className="text-sm text-gray-500 mt-1">Complete your profile to find relevant groups.</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Sidebar - 1 column */}
            <div className="space-y-6 animate-fade-in-right animate-delay-400">
              {/* Profile Completion */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2 text-teal-600" />
                    Profile Strength
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-teal-600">{profileCompletion}%</div>
                      <div className="text-sm text-gray-600">Profile Complete</div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div className="bg-teal-600 h-3 rounded-full" style={{ width: `${profileCompletion}%` }}></div>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center text-green-600">
                        <div className="w-2 h-2 bg-green-600 rounded-full mr-2"></div>
                        Account created
                      </div>
                      <div className={`flex items-center ${user?.first_name && user?.last_name ? 'text-green-600' : 'text-gray-500'}`}>
                        <div className={`w-2 h-2 ${user?.first_name && user?.last_name ? 'bg-green-600' : 'bg-gray-300'} rounded-full mr-2`}></div>
                        Profile information added
                      </div>
                      <div className="flex items-center text-gray-500">
                        <div className="w-2 h-2 bg-gray-300 rounded-full mr-2"></div>
                        Upload your CV
                      </div>
                      <div className="flex items-center text-gray-500">
                        <div className="w-2 h-2 bg-gray-300 rounded-full mr-2"></div>
                        Generate portfolio
                      </div>
                      <div className="flex items-center text-gray-500">
                        <div className="w-2 h-2 bg-gray-300 rounded-full mr-2"></div>
                        Join peer groups
                      </div>
                    </div>
                    <Link href="/profile/cv-upload">
                      <Button className="w-full bg-teal-600 hover:bg-teal-700" size="sm">
                        Complete Profile
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>

              {/* AI Assistant */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center">
                    <MessageSquare className="w-5 h-5 mr-2 text-teal-600" />
                    AI Career Assistant
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <p className="text-sm text-gray-600">
                      Get personalized career advice and insights powered by AI.
                    </p>
                    <div className="bg-teal-50 border border-teal-200 rounded-lg p-3">
                      <p className="text-sm text-teal-800">
                        💡 <strong>Tip:</strong> Upload your CV to get tailored job recommendations and skill gap analysis.
                      </p>
                    </div>
                    <Link href="/ai-chat">
                      <Button variant="outline" className="w-full" size="sm">
                        Chat with AI
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>

              {/* Recent Activity */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Recent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-teal-500 rounded-full mt-2"></div>
                      <div className="text-sm">
                        <p className="text-gray-900">Profile viewed by <span className="font-medium">TechCorp Inc.</span></p>
                        <p className="text-gray-500">2 hours ago</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                      <div className="text-sm">
                        <p className="text-gray-900">New job match found</p>
                        <p className="text-gray-500">1 day ago</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                      <div className="text-sm">
                        <p className="text-gray-900">Joined <span className="font-medium">Frontend Developers</span> group</p>
                        <p className="text-gray-500">3 days ago</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Quick Stats */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Your Network</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Profile Views</span>
                      <span className="font-semibold">127</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Connections</span>
                      <span className="font-semibold">89</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Groups Joined</span>
                      <span className="font-semibold">3</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Job Applications</span>
                      <span className="font-semibold">12</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>

        {/* Real-time Job Updates */}
        <RealtimeJobUpdates
          onJobUpdate={() => {
            // Refresh dashboard data when new jobs are available
            refresh();
          }}
          showNotifications={true}
        />
      </AppLayout>
    </ProtectedRoute>
  );
}