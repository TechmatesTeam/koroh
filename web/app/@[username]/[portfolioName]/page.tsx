'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Button } from '@/components/ui/button';
import { ExternalLink, Share2, Download } from 'lucide-react';

interface PortfolioData {
  id: string;
  username: string;
  portfolioName: string;
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

export default function PortfolioViewerPage() {
  const params = useParams();
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const username = params.username as string;
  const portfolioName = params.portfolioName as string;

  useEffect(() => {
    loadPortfolio();
  }, [username, portfolioName]);

  const loadPortfolio = async () => {
    try {
      setLoading(true);
      
      // For now, we'll simulate loading from localStorage (mock data)
      // In a real app, this would be an API call
      const portfolios = JSON.parse(localStorage.getItem('koroh_portfolios') || '[]');
      const foundPortfolio = portfolios.find((p: PortfolioData) => 
        p.username === username.replace('@', '') && p.portfolioName === portfolioName
      );

      if (foundPortfolio) {
        setPortfolio(foundPortfolio);
      } else {
        setError('Portfolio not found');
      }
    } catch (err) {
      setError('Failed to load portfolio');
    } finally {
      setLoading(false);
    }
  };

  const sharePortfolio = () => {
    if (navigator.share) {
      navigator.share({
        title: portfolio?.content.title || 'Portfolio',
        text: portfolio?.content.subtitle || 'Check out this portfolio',
        url: window.location.href,
      });
    } else {
      navigator.clipboard.writeText(window.location.href);
      alert('Portfolio URL copied to clipboard!');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner className="w-8 h-8 mx-auto mb-4" />
          <p className="text-gray-600">Loading portfolio...</p>
        </div>
      </div>
    );
  }

  if (error || !portfolio) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="p-6 text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Portfolio Not Found</h1>
            <p className="text-gray-600 mb-4">
              The portfolio you're looking for doesn't exist or has been moved.
            </p>
            <Button 
              onClick={() => window.location.href = '/'}
              className="bg-teal-600 hover:bg-teal-700"
            >
              Go Home
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { customizations, content } = portfolio;

  return (
    <div 
      className="min-h-screen"
      style={{ 
        backgroundColor: customizations.theme === 'dark' ? '#1f2937' : '#ffffff',
        color: customizations.theme === 'dark' ? '#ffffff' : '#1f2937',
        fontFamily: customizations.font === 'playfair' ? 'Playfair Display, serif' : 
                   customizations.font === 'roboto' ? 'Roboto, sans-serif' :
                   customizations.font === 'poppins' ? 'Poppins, sans-serif' : 'Inter, sans-serif'
      }}
    >
      {/* Header with sharing options */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-3 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">@{username}</span>
            <span className="text-sm text-gray-400">/</span>
            <span className="text-sm font-medium">{portfolioName}</span>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={sharePortfolio}
            >
              <Share2 className="w-4 h-4 mr-2" />
              Share
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.print()}
            >
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>
      </div>

      {/* Portfolio Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 
            className="text-4xl md:text-6xl font-bold mb-4"
            style={{ color: customizations.primaryColor }}
          >
            {content.title}
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-6">
            {content.subtitle}
          </p>
          <p className="text-lg text-gray-700 max-w-2xl mx-auto leading-relaxed">
            {content.bio}
          </p>
        </div>

        {/* Skills Section */}
        {content.skills && content.skills.length > 0 && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold mb-6" style={{ color: customizations.primaryColor }}>
              Skills
            </h2>
            <div className="flex flex-wrap gap-3">
              {content.skills.map((skill, index) => (
                <span
                  key={index}
                  className="px-4 py-2 rounded-full text-sm font-medium"
                  style={{ 
                    backgroundColor: customizations.primaryColor + '20',
                    color: customizations.primaryColor
                  }}
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Experience Section */}
        {content.experience && content.experience.length > 0 && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold mb-6" style={{ color: customizations.primaryColor }}>
              Experience
            </h2>
            <div className="space-y-6">
              {content.experience.map((exp, index) => (
                <div key={index} className="border-l-4 pl-6" style={{ borderColor: customizations.primaryColor }}>
                  <h3 className="text-xl font-semibold">{exp.title}</h3>
                  <p className="text-gray-600 mb-2">{exp.company} • {exp.duration}</p>
                  <p className="text-gray-700">{exp.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Projects Section */}
        {content.projects && content.projects.length > 0 && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold mb-6" style={{ color: customizations.primaryColor }}>
              Projects
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {content.projects.map((project, index) => (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <CardContent className="p-6">
                    <h3 className="text-xl font-semibold mb-3" style={{ color: customizations.primaryColor }}>
                      {project.name}
                    </h3>
                    <p className="text-gray-700 mb-4">{project.description}</p>
                    {project.technologies && (
                      <div className="flex flex-wrap gap-2">
                        {project.technologies.map((tech: string, techIndex: number) => (
                          <span
                            key={techIndex}
                            className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-700"
                          >
                            {tech}
                          </span>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Education Section */}
        {content.education && content.education.length > 0 && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold mb-6" style={{ color: customizations.primaryColor }}>
              Education
            </h2>
            <div className="space-y-4">
              {content.education.map((edu, index) => (
                <div key={index} className="border-l-4 pl-6" style={{ borderColor: customizations.primaryColor }}>
                  <h3 className="text-xl font-semibold">{edu.degree}</h3>
                  <p className="text-gray-600">{edu.institution} • {edu.year}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center pt-8 border-t">
          <p className="text-gray-500 text-sm">
            Built with Koroh - AI-Powered Professional Networking
          </p>
        </div>
      </div>
    </div>
  );
}