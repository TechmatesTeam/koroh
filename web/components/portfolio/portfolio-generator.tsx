'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { 
  Palette, 
  Eye, 
  Share2, 
  Download, 
  Sparkles, 
  Monitor, 
  Smartphone, 
  Tablet,
  Copy,
  ExternalLink,
  RefreshCw
} from 'lucide-react';
import { api } from '@/lib/api';
import { useNotifications } from '@/contexts/notification-context';
import { PortfolioShare } from './portfolio-share';
import { PortfolioUrlPreview } from './portfolio-url-preview';

interface PortfolioTemplate {
  id: string;
  name: string;
  description: string;
  preview: string;
  category: 'modern' | 'classic' | 'creative' | 'minimal';
  features: string[];
}

interface PortfolioData {
  id: string;
  url: string;
  template: string;
  customizations: {
    theme: string;
    primaryColor: string;
    font: string;
    layout: string;
  };
  content: {
    title: string;
    subtitle: string;
    bio: string;
    skills: string[];
    experience: any[];
    education: any[];
    projects: any[];
  };
}

const PORTFOLIO_TEMPLATES: PortfolioTemplate[] = [
  {
    id: 'modern-pro',
    name: 'Modern Professional',
    description: 'Clean, modern design perfect for tech professionals',
    preview: '/templates/modern-pro.jpg',
    category: 'modern',
    features: ['Responsive Design', 'Dark Mode', 'Animations', 'Contact Form'],
  },
  {
    id: 'classic-elegant',
    name: 'Classic Elegant',
    description: 'Timeless design suitable for all industries',
    preview: '/templates/classic-elegant.jpg',
    category: 'classic',
    features: ['Professional Layout', 'PDF Export', 'Social Links', 'Timeline'],
  },
  {
    id: 'creative-bold',
    name: 'Creative Bold',
    description: 'Eye-catching design for creative professionals',
    preview: '/templates/creative-bold.jpg',
    category: 'creative',
    features: ['Portfolio Gallery', 'Video Background', 'Custom Colors', 'Parallax'],
  },
  {
    id: 'minimal-clean',
    name: 'Minimal Clean',
    description: 'Simple, focused design that highlights content',
    preview: '/templates/minimal-clean.jpg',
    category: 'minimal',
    features: ['Fast Loading', 'Typography Focus', 'Mobile First', 'SEO Optimized'],
  },
];

const COLOR_THEMES = [
  { name: 'Teal', value: '#0d9488', class: 'bg-teal-600' },
  { name: 'Blue', value: '#2563eb', class: 'bg-blue-600' },
  { name: 'Purple', value: '#7c3aed', class: 'bg-purple-600' },
  { name: 'Green', value: '#059669', class: 'bg-green-600' },
  { name: 'Orange', value: '#ea580c', class: 'bg-orange-600' },
  { name: 'Pink', value: '#db2777', class: 'bg-pink-600' },
];

const FONT_OPTIONS = [
  { name: 'Inter', value: 'inter', preview: 'Modern & Clean' },
  { name: 'Playfair Display', value: 'playfair', preview: 'Elegant & Classic' },
  { name: 'Roboto', value: 'roboto', preview: 'Professional & Readable' },
  { name: 'Poppins', value: 'poppins', preview: 'Friendly & Approachable' },
];

export function PortfolioGenerator() {
  const [step, setStep] = useState<'template' | 'customize' | 'preview'>('template');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [customizations, setCustomizations] = useState({
    theme: 'light',
    primaryColor: '#0d9488',
    font: 'inter',
    layout: 'standard',
  });
  const [content, setContent] = useState({
    title: '',
    subtitle: '',
    bio: '',
    portfolioName: '',
  });
  const [previewDevice, setPreviewDevice] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [showShareModal, setShowShareModal] = useState(false);
  const { addNotification } = useNotifications();

  useEffect(() => {
    // Load existing portfolio data if available
    loadExistingPortfolio();
  }, []);

  const loadExistingPortfolio = async () => {
    try {
      const response = await api.profiles.getPortfolios();
      if (response.data.length > 0) {
        const portfolio = response.data[0];
        setPortfolioData(portfolio);
        setSelectedTemplate(portfolio.template);
        setCustomizations(portfolio.customizations);
        setContent(portfolio.content);
      }
    } catch (error) {
      console.error('Failed to load existing portfolio:', error);
    }
  };

  const generatePortfolio = async () => {
    if (!selectedTemplate) {
      addNotification({ 
        title: 'Template Required',
        message: 'Please select a template first', 
        type: 'error' 
      });
      return;
    }

    setIsGenerating(true);
    try {
      const response = await api.profiles.generatePortfolio({
        template: selectedTemplate,
        portfolioName: content.portfolioName || undefined
      });
      setPortfolioData(response.data);
      setStep('customize');
      addNotification({ 
        title: 'Portfolio Generated',
        message: 'Portfolio generated successfully!', 
        type: 'success' 
      });
    } catch (error: any) {
      addNotification({
        title: 'Generation Failed',
        message: error.response?.data?.message || 'Failed to generate portfolio',
        type: 'error'
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const updateCustomizations = (key: string, value: string) => {
    setCustomizations(prev => ({ ...prev, [key]: value }));
  };

  const updateContent = (key: string, value: string) => {
    // For portfolio name, ensure it's URL-safe
    if (key === 'portfolioName') {
      value = value
        .toLowerCase()
        .replace(/[^a-z0-9-]/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');
    }
    setContent(prev => ({ ...prev, [key]: value }));
  };

  const saveCustomizations = async () => {
    if (!portfolioData) return;

    try {
      const response = await api.profiles.updatePortfolio(portfolioData.id, {
        customizations,
        content,
      });
      setPortfolioData(response.data);
      addNotification({ 
        title: 'Portfolio Updated',
        message: 'Portfolio updated successfully!', 
        type: 'success' 
      });
    } catch (error: any) {
      addNotification({
        title: 'Update Failed',
        message: error.response?.data?.message || 'Failed to update portfolio',
        type: 'error'
      });
    }
  };

  const copyPortfolioUrl = () => {
    if (portfolioData?.url) {
      navigator.clipboard.writeText(portfolioData.url);
      addNotification({ 
        title: 'URL Copied',
        message: 'Portfolio URL copied to clipboard!', 
        type: 'success' 
      });
    }
  };

  const regeneratePortfolio = async () => {
    setIsGenerating(true);
    try {
      const response = await api.profiles.generatePortfolio({
        template: selectedTemplate,
        portfolioName: content.portfolioName || undefined
      });
      setPortfolioData(response.data);
      addNotification({ 
        title: 'Portfolio Regenerated',
        message: 'Portfolio regenerated successfully!', 
        type: 'success' 
      });
    } catch (error: any) {
      addNotification({
        title: 'Regeneration Failed',
        message: error.response?.data?.message || 'Failed to regenerate portfolio',
        type: 'error'
      });
    } finally {
      setIsGenerating(false);
    }
  };

  if (step === 'template') {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Palette className="w-5 h-5 mr-2 text-teal-600" />
            Choose Your Portfolio Template
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {PORTFOLIO_TEMPLATES.map((template) => (
              <div
                key={template.id}
                className={`
                  border-2 rounded-lg p-4 cursor-pointer transition-all
                  ${
                    selectedTemplate === template.id
                      ? 'border-teal-500 bg-teal-50'
                      : 'border-gray-200 hover:border-teal-300'
                  }
                `}
                onClick={() => setSelectedTemplate(template.id)}
              >
                <div className="aspect-video bg-gray-100 rounded-lg mb-4 flex items-center justify-center">
                  <Monitor className="w-8 h-8 text-gray-400" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{template.name}</h3>
                <p className="text-sm text-gray-600 mb-3">{template.description}</p>
                <div className="flex flex-wrap gap-1">
                  {template.features.map((feature) => (
                    <span
                      key={feature}
                      className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded"
                    >
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Portfolio URL Preview */}
          <div className="pt-4 border-t">
            <PortfolioUrlPreview
              portfolioName={content.portfolioName}
              onPortfolioNameChange={(name) => updateContent('portfolioName', name)}
            />
          </div>

          <div className="flex justify-between items-center pt-4 border-t">
            <p className="text-sm text-gray-600">
              Select a template to start generating your portfolio
            </p>
            <Button
              onClick={generatePortfolio}
              disabled={!selectedTemplate || isGenerating}
              className="bg-teal-600 hover:bg-teal-700"
            >
              {isGenerating ? (
                <>
                  <LoadingSpinner className="w-4 h-4 mr-2" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Generate Portfolio
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (step === 'customize') {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Customization Panel */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Palette className="w-5 h-5 mr-2 text-teal-600" />
                Customize Your Portfolio
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Content Customization */}
              <div className="space-y-4">
                <h3 className="font-medium text-gray-900">Content</h3>
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="title">Portfolio Title</Label>
                    <Input
                      id="title"
                      value={content.title}
                      onChange={(e) => updateContent('title', e.target.value)}
                      placeholder="Your Name"
                    />
                  </div>
                  <div>
                    <Label htmlFor="subtitle">Subtitle</Label>
                    <Input
                      id="subtitle"
                      value={content.subtitle}
                      onChange={(e) => updateContent('subtitle', e.target.value)}
                      placeholder="Your Professional Title"
                    />
                  </div>
                  <div>
                    <Label htmlFor="bio">Bio</Label>
                    <Textarea
                      id="bio"
                      value={content.bio}
                      onChange={(e) => updateContent('bio', e.target.value)}
                      placeholder="Tell visitors about yourself..."
                      rows={3}
                    />
                  </div>
                </div>
              </div>

              {/* Color Theme */}
              <div className="space-y-4">
                <h3 className="font-medium text-gray-900">Color Theme</h3>
                <div className="grid grid-cols-3 gap-3">
                  {COLOR_THEMES.map((color) => (
                    <button
                      key={color.value}
                      onClick={() => updateCustomizations('primaryColor', color.value)}
                      className={`
                        p-3 rounded-lg border-2 transition-all
                        ${
                          customizations.primaryColor === color.value
                            ? 'border-gray-900'
                            : 'border-gray-200 hover:border-gray-300'
                        }
                      `}
                    >
                      <div className={`w-full h-8 rounded ${color.class} mb-2`}></div>
                      <span className="text-sm font-medium">{color.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Font Selection */}
              <div className="space-y-4">
                <h3 className="font-medium text-gray-900">Typography</h3>
                <div className="space-y-2">
                  {FONT_OPTIONS.map((font) => (
                    <button
                      key={font.value}
                      onClick={() => updateCustomizations('font', font.value)}
                      className={`
                        w-full p-3 text-left rounded-lg border-2 transition-all
                        ${
                          customizations.font === font.value
                            ? 'border-teal-500 bg-teal-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }
                      `}
                    >
                      <div className="font-medium">{font.name}</div>
                      <div className="text-sm text-gray-600">{font.preview}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex space-x-3 pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={() => setStep('template')}
                  className="flex-1"
                >
                  Back to Templates
                </Button>
                <Button
                  onClick={saveCustomizations}
                  className="flex-1 bg-teal-600 hover:bg-teal-700"
                >
                  Save Changes
                </Button>
                <Button
                  onClick={() => setStep('preview')}
                  className="flex-1"
                >
                  <Eye className="w-4 h-4 mr-2" />
                  Preview
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Live Preview */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center">
                  <Eye className="w-5 h-5 mr-2 text-teal-600" />
                  Live Preview
                </span>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setPreviewDevice('desktop')}
                    className={`p-2 rounded ${previewDevice === 'desktop' ? 'bg-teal-100 text-teal-600' : 'text-gray-400'}`}
                  >
                    <Monitor className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setPreviewDevice('tablet')}
                    className={`p-2 rounded ${previewDevice === 'tablet' ? 'bg-teal-100 text-teal-600' : 'text-gray-400'}`}
                  >
                    <Tablet className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setPreviewDevice('mobile')}
                    className={`p-2 rounded ${previewDevice === 'mobile' ? 'bg-teal-100 text-teal-600' : 'text-gray-400'}`}
                  >
                    <Smartphone className="w-4 h-4" />
                  </button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`
                mx-auto bg-white border rounded-lg overflow-hidden
                ${previewDevice === 'desktop' ? 'w-full' : ''}
                ${previewDevice === 'tablet' ? 'w-3/4' : ''}
                ${previewDevice === 'mobile' ? 'w-1/2' : ''}
              `}>
                <div className="aspect-video bg-gray-50 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-2xl font-bold mb-2" style={{ color: customizations.primaryColor }}>
                      {content.title || 'Your Name'}
                    </div>
                    <div className="text-gray-600 mb-4">
                      {content.subtitle || 'Your Professional Title'}
                    </div>
                    <div className="text-sm text-gray-500 max-w-xs">
                      {content.bio || 'Your professional bio will appear here...'}
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (step === 'preview' && portfolioData) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center">
              <Eye className="w-5 h-5 mr-2 text-teal-600" />
              Portfolio Preview
            </span>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                onClick={regeneratePortfolio}
                disabled={isGenerating}
              >
                {isGenerating ? (
                  <LoadingSpinner className="w-4 h-4 mr-2" />
                ) : (
                  <RefreshCw className="w-4 h-4 mr-2" />
                )}
                Regenerate
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Portfolio URL */}
          <div className="bg-gray-50 border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h3 className="font-medium text-gray-900 mb-1">Your Portfolio URL</h3>
                <p className="text-sm text-gray-600 font-mono break-all">{portfolioData.url}</p>
                <div className="mt-2 text-xs text-gray-500">
                  <span className="font-medium">Username:</span> @{(portfolioData as any).username} • 
                  <span className="font-medium ml-2">Portfolio:</span> {(portfolioData as any).portfolioName}
                </div>
              </div>
              <div className="flex space-x-2 ml-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyPortfolioUrl}
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Copy
                </Button>
                <Button
                  size="sm"
                  onClick={() => window.open(portfolioData.url, '_blank')}
                  className="bg-teal-600 hover:bg-teal-700"
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Open
                </Button>
              </div>
            </div>
          </div>

          {/* Portfolio Preview */}
          <div className="border rounded-lg overflow-hidden">
            <iframe
              src={portfolioData.url}
              className="w-full h-96"
              title="Portfolio Preview"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-between items-center pt-4 border-t">
            <Button
              variant="outline"
              onClick={() => setStep('customize')}
            >
              Back to Customize
            </Button>
            <div className="flex space-x-3">
              <Button
                variant="outline"
                onClick={() => window.open(portfolioData.url, '_blank')}
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                View Full Site
              </Button>
              <Button 
                onClick={() => setShowShareModal(true)}
                className="bg-teal-600 hover:bg-teal-700"
              >
                <Share2 className="w-4 h-4 mr-2" />
                Share Portfolio
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      {/* Share Modal */}
      {portfolioData && (
        <PortfolioShare
          isOpen={showShareModal}
          onClose={() => setShowShareModal(false)}
          portfolioUrl={portfolioData.url}
          portfolioTitle={content.title || 'My Professional Portfolio'}
        />
      )}
    </>
  );
}