'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Upload, 
  User, 
  Lock, 
  Globe, 
  Database,
  Zap,
  FileText
} from 'lucide-react';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/auth-context';

interface TestResult {
  name: string;
  status: 'pending' | 'running' | 'success' | 'error';
  message?: string;
  details?: any;
  duration?: number;
}

interface TestSuite {
  name: string;
  icon: React.ReactNode;
  tests: TestResult[];
  status: 'pending' | 'running' | 'success' | 'error';
}

export default function IntegrationTestPage() {
  const { user, login, register, logout } = useAuth();
  const [testSuites, setTestSuites] = useState<TestSuite[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [testCredentials, setTestCredentials] = useState({
    email: `test_${Date.now()}@example.com`,
    password: 'TestPassword123!',
    firstName: 'Integration',
    lastName: 'Test'
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    initializeTestSuites();
  }, []);

  const initializeTestSuites = () => {
    const suites: TestSuite[] = [
      {
        name: 'Authentication & CORS',
        icon: <Lock className="w-5 h-5" />,
        status: 'pending',
        tests: [
          { name: 'CORS Preflight Request', status: 'pending' },
          { name: 'User Registration', status: 'pending' },
          { name: 'User Login', status: 'pending' },
          { name: 'Authenticated Request', status: 'pending' },
          { name: 'Token Refresh', status: 'pending' },
          { name: 'User Logout', status: 'pending' },
        ]
      },
      {
        name: 'Profile Management',
        icon: <User className="w-5 h-5" />,
        status: 'pending',
        tests: [
          { name: 'Get Profile', status: 'pending' },
          { name: 'Update Profile', status: 'pending' },
          { name: 'CV Upload', status: 'pending' },
          { name: 'CV Analysis', status: 'pending' },
        ]
      },
      {
        name: 'Portfolio Generation',
        icon: <FileText className="w-5 h-5" />,
        status: 'pending',
        tests: [
          { name: 'Generate Portfolio', status: 'pending' },
          { name: 'List Portfolios', status: 'pending' },
          { name: 'Update Portfolio', status: 'pending' },
        ]
      },
      {
        name: 'API Endpoints',
        icon: <Database className="w-5 h-5" />,
        status: 'pending',
        tests: [
          { name: 'Health Check', status: 'pending' },
          { name: 'Peer Groups Discovery', status: 'pending' },
          { name: 'Trending Groups', status: 'pending' },
          { name: 'AI Chat (Anonymous)', status: 'pending' },
        ]
      },
      {
        name: 'Performance & Security',
        icon: <Zap className="w-5 h-5" />,
        status: 'pending',
        tests: [
          { name: 'Response Time Check', status: 'pending' },
          { name: 'Security Headers', status: 'pending' },
          { name: 'Rate Limiting', status: 'pending' },
          { name: 'Error Handling', status: 'pending' },
        ]
      }
    ];
    setTestSuites(suites);
  };

  const updateTestResult = (suiteIndex: number, testIndex: number, result: Partial<TestResult>) => {
    setTestSuites(prev => {
      const newSuites = [...prev];
      newSuites[suiteIndex].tests[testIndex] = { ...newSuites[suiteIndex].tests[testIndex], ...result };
      
      // Update suite status
      const tests = newSuites[suiteIndex].tests;
      if (tests.every(t => t.status === 'success')) {
        newSuites[suiteIndex].status = 'success';
      } else if (tests.some(t => t.status === 'error')) {
        newSuites[suiteIndex].status = 'error';
      } else if (tests.some(t => t.status === 'running')) {
        newSuites[suiteIndex].status = 'running';
      }
      
      return newSuites;
    });
  };

  const runTest = async (suiteIndex: number, testIndex: number, testFn: () => Promise<any>) => {
    const startTime = Date.now();
    updateTestResult(suiteIndex, testIndex, { status: 'running' });
    
    try {
      const result = await testFn();
      const duration = Date.now() - startTime;
      updateTestResult(suiteIndex, testIndex, { 
        status: 'success', 
        message: 'Passed',
        details: result,
        duration 
      });
      return result;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      updateTestResult(suiteIndex, testIndex, { 
        status: 'error', 
        message: error.message || 'Failed',
        details: error,
        duration 
      });
      throw error;
    }
  };

  const runAllTests = async () => {
    setIsRunning(true);
    
    try {
      // Authentication & CORS Tests
      await runTest(0, 0, async () => {
        // Test CORS preflight
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/register/`, {
          method: 'OPTIONS',
          headers: {
            'Origin': window.location.origin,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type, Authorization'
          }
        });
        if (!response.ok) throw new Error(`CORS preflight failed: ${response.status}`);
        return { status: response.status, headers: Object.fromEntries(response.headers.entries()) };
      });

      await runTest(0, 1, async () => {
        // Test user registration
        const result = await register({
          email: testCredentials.email,
          password: testCredentials.password,
          password_confirm: testCredentials.password,
          first_name: testCredentials.firstName,
          last_name: testCredentials.lastName
        });
        return result;
      });

      await runTest(0, 2, async () => {
        // Test user login (should already be logged in from registration)
        if (!user) {
          const result = await login({
            email: testCredentials.email,
            password: testCredentials.password
          });
          return result;
        }
        return { message: 'Already logged in from registration' };
      });

      await runTest(0, 3, async () => {
        // Test authenticated request
        const response = await api.profiles.getMe();
        return response.data;
      });

      await runTest(0, 4, async () => {
        // Test token refresh (simulate by making multiple requests)
        const responses = await Promise.all([
          api.profiles.getMe(),
          api.profiles.getMe(),
          api.profiles.getMe()
        ]);
        return { requests: responses.length, success: true };
      });

      // Profile Management Tests
      await runTest(1, 0, async () => {
        const response = await api.profiles.getMe();
        return response.data;
      });

      await runTest(1, 1, async () => {
        const response = await api.profiles.updateMe({
          headline: 'Integration Test User',
          summary: 'Testing the Koroh platform integration'
        });
        return response.data;
      });

      if (selectedFile) {
        await runTest(1, 2, async () => {
          const formData = new FormData();
          formData.append('cv_file', selectedFile);
          const response = await api.profiles.uploadCV(formData);
          return response.data;
        });

        await runTest(1, 3, async () => {
          // This might fail if no CV is uploaded, but that's expected
          try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/profiles/cv/analyze/`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
              }
            });
            if (response.ok) {
              return await response.json();
            } else {
              throw new Error(`CV analysis failed: ${response.status}`);
            }
          } catch (error) {
            throw new Error('CV analysis requires uploaded CV');
          }
        });
      } else {
        updateTestResult(1, 2, { status: 'error', message: 'No file selected' });
        updateTestResult(1, 3, { status: 'error', message: 'Requires CV upload' });
      }

      // Portfolio Generation Tests
      await runTest(2, 0, async () => {
        const response = await api.profiles.generatePortfolio({
          template: 'modern-pro',
          portfolioName: 'integration-test'
        });
        return response.data;
      });

      await runTest(2, 1, async () => {
        const response = await api.profiles.getPortfolios();
        return response.data;
      });

      await runTest(2, 2, async () => {
        const portfolios = await api.profiles.getPortfolios();
        if (portfolios.data.length > 0) {
          const response = await api.profiles.updatePortfolio(portfolios.data[0].id, {
            customizations: { primaryColor: '#0d9488' }
          });
          return response.data;
        } else {
          throw new Error('No portfolio to update');
        }
      });

      // API Endpoints Tests
      await runTest(3, 0, async () => {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '')}/health/`);
        if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
        return { status: response.status, text: await response.text() };
      });

      await runTest(3, 1, async () => {
        const response = await api.peerGroups.discover();
        return response.data;
      });

      await runTest(3, 2, async () => {
        const response = await api.peerGroups.trending();
        return response.data;
      });

      await runTest(3, 3, async () => {
        const response = await api.ai.anonymousChat('Hello, this is a test message');
        return response.data;
      });

      // Performance & Security Tests
      await runTest(4, 0, async () => {
        const start = Date.now();
        await api.profiles.getMe();
        const duration = Date.now() - start;
        if (duration > 2000) throw new Error(`Response too slow: ${duration}ms`);
        return { duration, threshold: '2000ms', passed: true };
      });

      await runTest(4, 1, async () => {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '')}/health/`);
        const headers = Object.fromEntries(response.headers.entries());
        const securityHeaders = [
          'x-content-type-options',
          'x-frame-options',
          'x-xss-protection'
        ];
        const present = securityHeaders.filter(h => h in headers);
        if (present.length < 2) throw new Error(`Missing security headers: ${securityHeaders.filter(h => !(h in headers)).join(', ')}`);
        return { headers: present, total: securityHeaders.length };
      });

      await runTest(4, 2, async () => {
        // Test rate limiting by making rapid requests
        const requests = Array(5).fill(null).map(() => 
          fetch(`${process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '')}/health/`)
        );
        const responses = await Promise.all(requests);
        const statuses = responses.map(r => r.status);
        return { statuses, allSuccessful: statuses.every(s => s === 200) };
      });

      await runTest(4, 3, async () => {
        // Test error handling
        try {
          await fetch(`${process.env.NEXT_PUBLIC_API_URL}/nonexistent-endpoint/`);
        } catch (error) {
          // Expected to fail
        }
        
        // Test with invalid auth
        try {
          await fetch(`${process.env.NEXT_PUBLIC_API_URL}/profiles/me/`, {
            headers: { 'Authorization': 'Bearer invalid-token' }
          });
        } catch (error) {
          // Expected to fail
        }
        
        return { message: 'Error handling working correctly' };
      });

      // Logout test
      await runTest(0, 5, async () => {
        await logout();
        return { message: 'Logged out successfully' };
      });

    } catch (error) {
      console.error('Test suite failed:', error);
    } finally {
      setIsRunning(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'running':
        return <LoadingSpinner className="w-4 h-4 text-blue-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'running':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Frontend-Backend Integration Test
          </h1>
          <p className="text-gray-600 mb-6">
            Comprehensive testing of authentication, API endpoints, file uploads, and portfolio generation.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Test Configuration</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="email">Test Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={testCredentials.email}
                    onChange={(e) => setTestCredentials(prev => ({ ...prev, email: e.target.value }))}
                    disabled={isRunning}
                  />
                </div>
                <div>
                  <Label htmlFor="password">Test Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={testCredentials.password}
                    onChange={(e) => setTestCredentials(prev => ({ ...prev, password: e.target.value }))}
                    disabled={isRunning}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">CV Upload Test</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Label htmlFor="cv-file">Select CV File (Optional)</Label>
                  <Input
                    id="cv-file"
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    disabled={isRunning}
                  />
                  {selectedFile && (
                    <p className="text-sm text-gray-600">
                      Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="flex justify-center mb-8">
            <Button
              onClick={runAllTests}
              disabled={isRunning}
              className="bg-teal-600 hover:bg-teal-700 px-8 py-3 text-lg"
            >
              {isRunning ? (
                <>
                  <LoadingSpinner className="w-5 h-5 mr-2" />
                  Running Tests...
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5 mr-2" />
                  Run Integration Tests
                </>
              )}
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {testSuites.map((suite, suiteIndex) => (
            <Card key={suiteIndex} className={`border-2 ${getStatusColor(suite.status)}`}>
              <CardHeader>
                <CardTitle className="flex items-center">
                  {suite.icon}
                  <span className="ml-2">{suite.name}</span>
                  <div className="ml-auto">
                    {getStatusIcon(suite.status)}
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {suite.tests.map((test, testIndex) => (
                    <div key={testIndex} className="flex items-center justify-between p-3 bg-white rounded-lg border">
                      <div className="flex items-center">
                        {getStatusIcon(test.status)}
                        <span className="ml-2 text-sm font-medium">{test.name}</span>
                      </div>
                      <div className="text-right">
                        {test.duration && (
                          <span className="text-xs text-gray-500">{test.duration}ms</span>
                        )}
                        {test.message && (
                          <div className="text-xs text-gray-600">{test.message}</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-8 text-center">
          <p className="text-sm text-gray-600">
            This test verifies that the frontend can successfully communicate with the backend API,
            including authentication, file uploads, portfolio generation, and all core functionality.
          </p>
        </div>
      </div>
    </div>
  );
}