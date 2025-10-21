'use client';

import { ProtectedRoute } from '@/components/auth/protected-route';
import { AppLayout } from '@/components/layout/app-layout';
import { CVUpload } from '@/components/cv/cv-upload';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText, Sparkles, TrendingUp } from 'lucide-react';

export default function CVUploadPage() {

  return (
    <ProtectedRoute>
      <AppLayout>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Upload Your CV</h1>
            <p className="text-gray-600 mt-2">
              Let our AI analyze your CV to generate personalized insights and create your professional portfolio.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Upload Area */}
            <div className="lg:col-span-2">
              <CVUpload />
            </div>

            {/* Sidebar with Benefits */}
            <div className="space-y-6">
              {/* AI Analysis Benefits */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-lg">
                    <Sparkles className="w-5 h-5 mr-2 text-teal-600" />
                    AI Analysis Benefits
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-teal-500 rounded-full mt-2"></div>
                    <div>
                      <h4 className="font-medium text-gray-900">Skills Extraction</h4>
                      <p className="text-sm text-gray-600">
                        Automatically identify and categorize your technical and soft skills
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-teal-500 rounded-full mt-2"></div>
                    <div>
                      <h4 className="font-medium text-gray-900">Experience Analysis</h4>
                      <p className="text-sm text-gray-600">
                        Parse your work history and highlight key achievements
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-teal-500 rounded-full mt-2"></div>
                    <div>
                      <h4 className="font-medium text-gray-900">Career Insights</h4>
                      <p className="text-sm text-gray-600">
                        Get personalized recommendations for career growth
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-teal-500 rounded-full mt-2"></div>
                    <div>
                      <h4 className="font-medium text-gray-900">Portfolio Generation</h4>
                      <p className="text-sm text-gray-600">
                        Create a professional portfolio website automatically
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* What Happens Next */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-lg">
                    <TrendingUp className="w-5 h-5 mr-2 text-teal-600" />
                    What Happens Next?
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-teal-100 text-teal-600 rounded-full flex items-center justify-center text-sm font-medium">
                      1
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">AI Analysis</h4>
                      <p className="text-sm text-gray-600">
                        Our AI will analyze your CV and extract key information
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-teal-100 text-teal-600 rounded-full flex items-center justify-center text-sm font-medium">
                      2
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">Profile Enhancement</h4>
                      <p className="text-sm text-gray-600">
                        Your profile will be automatically updated with extracted data
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-teal-100 text-teal-600 rounded-full flex items-center justify-center text-sm font-medium">
                      3
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">Portfolio Creation</h4>
                      <p className="text-sm text-gray-600">
                        Generate a professional portfolio website ready to share
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-teal-100 text-teal-600 rounded-full flex items-center justify-center text-sm font-medium">
                      4
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">Job Matching</h4>
                      <p className="text-sm text-gray-600">
                        Receive personalized job recommendations based on your skills
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Privacy & Security */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-lg">
                    <FileText className="w-5 h-5 mr-2 text-teal-600" />
                    Privacy & Security
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-gray-600">
                    Your CV is processed securely using enterprise-grade encryption. We never share your personal information with third parties.
                  </p>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="text-sm text-green-800">
                      🔒 <strong>Secure:</strong> All files are encrypted and stored securely
                    </p>
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-sm text-blue-800">
                      🤖 <strong>AI-Powered:</strong> Advanced AI analyzes your CV for insights
                    </p>
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