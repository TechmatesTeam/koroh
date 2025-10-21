import { Metadata } from 'next';
import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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

export const metadata: Metadata = {
  title: 'Dashboard - Koroh',
  description: 'Your personalized professional dashboard',
};

export default function Dashboard() {
  return (
    <ProtectedRoute>
      <AppLayout>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Welcome Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Good morning, John!</h1>
            <p className="text-gray-600 mt-2">Here's what's happening in your professional network today.</p>
          </div>

          {/* Dashboard Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Main Content - 3 columns */}
            <div className="lg:col-span-3 space-y-6">
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
                  <div className="space-y-4">
                    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900">Senior Software Engineer</h3>
                          <p className="text-teal-600 font-medium">TechCorp Inc.</p>
                          <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                            <span className="flex items-center">
                              <MapPin className="w-4 h-4 mr-1" />
                              San Francisco, CA
                            </span>
                            <span className="flex items-center">
                              <Clock className="w-4 h-4 mr-1" />
                              2 days ago
                            </span>
                          </div>
                          <div className="flex items-center mt-2">
                            <div className="flex items-center">
                              <Star className="w-4 h-4 text-yellow-400 fill-current" />
                              <span className="text-sm text-gray-600 ml-1">95% match</span>
                            </div>
                          </div>
                        </div>
                        <Button size="sm" className="bg-teal-600 hover:bg-teal-700">Apply</Button>
                      </div>
                    </div>

                    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900">Full Stack Developer</h3>
                          <p className="text-teal-600 font-medium">StartupXYZ</p>
                          <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                            <span className="flex items-center">
                              <MapPin className="w-4 h-4 mr-1" />
                              Remote
                            </span>
                            <span className="flex items-center">
                              <Clock className="w-4 h-4 mr-1" />
                              1 week ago
                            </span>
                          </div>
                          <div className="flex items-center mt-2">
                            <div className="flex items-center">
                              <Star className="w-4 h-4 text-yellow-400 fill-current" />
                              <span className="text-sm text-gray-600 ml-1">88% match</span>
                            </div>
                          </div>
                        </div>
                        <Button size="sm" variant="outline">View</Button>
                      </div>
                    </div>

                    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900">Frontend Engineer</h3>
                          <p className="text-teal-600 font-medium">DesignCo</p>
                          <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                            <span className="flex items-center">
                              <MapPin className="w-4 h-4 mr-1" />
                              New York, NY
                            </span>
                            <span className="flex items-center">
                              <Clock className="w-4 h-4 mr-1" />
                              3 days ago
                            </span>
                          </div>
                          <div className="flex items-center mt-2">
                            <div className="flex items-center">
                              <Star className="w-4 h-4 text-yellow-400 fill-current" />
                              <span className="text-sm text-gray-600 ml-1">82% match</span>
                            </div>
                          </div>
                        </div>
                        <Button size="sm" variant="outline">View</Button>
                      </div>
                    </div>
                  </div>
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
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-center space-x-3 mb-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg"></div>
                        <div>
                          <h3 className="font-semibold text-gray-900">InnovateTech</h3>
                          <p className="text-sm text-gray-500">AI & Machine Learning</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Growth Score</span>
                        <span className="font-semibold text-green-600">Excellent</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                        <div className="bg-green-500 h-2 rounded-full w-4/5"></div>
                      </div>
                      <div className="flex justify-between items-center mt-3">
                        <span className="text-sm text-gray-600">15 open positions</span>
                        <Button size="sm" variant="outline">Follow</Button>
                      </div>
                    </div>

                    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-center space-x-3 mb-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-teal-600 rounded-lg"></div>
                        <div>
                          <h3 className="font-semibold text-gray-900">GreenTech Solutions</h3>
                          <p className="text-sm text-gray-500">Sustainability</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Growth Score</span>
                        <span className="font-semibold text-blue-600">Very Good</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                        <div className="bg-blue-500 h-2 rounded-full w-3/4"></div>
                      </div>
                      <div className="flex justify-between items-center mt-3">
                        <span className="text-sm text-gray-600">8 open positions</span>
                        <Button size="sm" variant="outline">Follow</Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Peer Group Suggestions */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="flex items-center">
                    <Users className="w-5 h-5 mr-2 text-teal-600" />
                    Recommended Peer Groups
                  </CardTitle>
                  <Link href="/network">
                    <Button variant="ghost" size="sm" className="text-teal-600 hover:text-teal-700">
                      See All <ArrowRight className="w-4 h-4 ml-1" />
                    </Button>
                  </Link>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900">Frontend Developers Network</h3>
                          <p className="text-sm text-gray-600 mt-1">Connect with frontend developers, share best practices, and discuss latest trends in web development.</p>
                          <div className="flex items-center space-x-4 mt-3 text-sm text-gray-500">
                            <span>2,847 members</span>
                            <span>•</span>
                            <span>Very Active</span>
                          </div>
                        </div>
                        <Button size="sm" className="bg-teal-600 hover:bg-teal-700">Join</Button>
                      </div>
                    </div>

                    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900">AI & Machine Learning Professionals</h3>
                          <p className="text-sm text-gray-600 mt-1">Discuss AI trends, share research, and network with ML engineers and data scientists.</p>
                          <div className="flex items-center space-x-4 mt-3 text-sm text-gray-500">
                            <span>1,523 members</span>
                            <span>•</span>
                            <span>Active</span>
                          </div>
                        </div>
                        <Button size="sm" variant="outline">View</Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Sidebar - 1 column */}
            <div className="space-y-6">
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
                      <div className="text-3xl font-bold text-teal-600">75%</div>
                      <div className="text-sm text-gray-600">Profile Complete</div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div className="bg-teal-600 h-3 rounded-full" style={{ width: '75%' }}></div>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center text-green-600">
                        <div className="w-2 h-2 bg-green-600 rounded-full mr-2"></div>
                        Account created
                      </div>
                      <div className="flex items-center text-green-600">
                        <div className="w-2 h-2 bg-green-600 rounded-full mr-2"></div>
                        Profile photo added
                      </div>
                      <div className="flex items-center text-green-600">
                        <div className="w-2 h-2 bg-green-600 rounded-full mr-2"></div>
                        Work experience added
                      </div>
                      <div className="flex items-center text-gray-500">
                        <div className="w-2 h-2 bg-gray-300 rounded-full mr-2"></div>
                        Upload your CV
                      </div>
                      <div className="flex items-center text-gray-500">
                        <div className="w-2 h-2 bg-gray-300 rounded-full mr-2"></div>
                        Generate portfolio
                      </div>
                    </div>
                    <Button className="w-full bg-teal-600 hover:bg-teal-700" size="sm">
                      Complete Profile
                    </Button>
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
                    <Button variant="outline" className="w-full" size="sm">
                      Chat with AI
                    </Button>
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
      </AppLayout>
    </ProtectedRoute>
  );
}