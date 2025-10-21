'use client';

import { ProtectedRoute } from '@/components/auth/protected-route';
import { AppLayout } from '@/components/layout/app-layout';
import { PortfolioGenerator } from '@/components/portfolio/portfolio-generator';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Sparkles, Zap, Globe, TrendingUp } from 'lucide-react';

export default function PortfolioGeneratePage() {
  return (
    <ProtectedRoute>
      <AppLayout>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Generate Your Professional Portfolio
            </h1>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Transform your CV into a stunning professional portfolio website using AI. 
              Choose from beautiful templates and customize to match your personal brand.
            </p>
          </div>

          {/* Benefits Section */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card className="text-center">
              <CardContent className="pt-6">
                <div className="w-12 h-12 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="w-6 h-6 text-teal-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">AI-Powered</h3>
                <p className="text-sm text-gray-600">
                  Intelligent content generation from your CV data
                </p>
              </CardContent>
            </Card>

            <Card className="text-center">
              <CardContent className="pt-6">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Zap className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Fast Setup</h3>
                <p className="text-sm text-gray-600">
                  Generate a complete portfolio in minutes, not hours
                </p>
              </CardContent>
            </Card>

            <Card className="text-center">
              <CardContent className="pt-6">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Globe className="w-6 h-6 text-green-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Shareable</h3>
                <p className="text-sm text-gray-600">
                  Get a professional URL to share with employers
                </p>
              </CardContent>
            </Card>

            <Card className="text-center">
              <CardContent className="pt-6">
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <TrendingUp className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">SEO Optimized</h3>
                <p className="text-sm text-gray-600">
                  Built for search engines and professional visibility
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Portfolio Generator */}
          <PortfolioGenerator />

          {/* Help Section */}
          <div className="mt-12">
            <Card>
              <CardHeader>
                <CardTitle className="text-center">Need Help Getting Started?</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">1. Upload Your CV</h4>
                    <p className="text-sm text-gray-600">
                      Make sure you've uploaded your CV first so our AI can extract your information
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">2. Choose Template</h4>
                    <p className="text-sm text-gray-600">
                      Select a template that matches your industry and personal style
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">3. Customize & Share</h4>
                    <p className="text-sm text-gray-600">
                      Personalize colors, fonts, and content, then share your professional URL
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </AppLayout>
    </ProtectedRoute>
  );
}