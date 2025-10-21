'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Copy, ExternalLink, Globe } from 'lucide-react';
import { useNotifications } from '@/contexts/notification-context';

interface PortfolioUrlPreviewProps {
  portfolioName: string;
  onPortfolioNameChange: (name: string) => void;
}

export function PortfolioUrlPreview({ portfolioName, onPortfolioNameChange }: PortfolioUrlPreviewProps) {
  const [currentHost, setCurrentHost] = useState('localhost:3000');
  const [username, setUsername] = useState('username');
  const { addNotification } = useNotifications();

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setCurrentHost(window.location.host);
      
      // Try to get username from localStorage (mock user data)
      try {
        const currentUser = JSON.parse(localStorage.getItem('koroh_current_user') || '{}');
        if (currentUser.email) {
          const extractedUsername = currentUser.email.split('@')[0] || 
                                  `${currentUser.first_name?.toLowerCase()}.${currentUser.last_name?.toLowerCase()}`;
          setUsername(extractedUsername);
        }
      } catch (error) {
        // Use default username if no user data
      }
    }
  }, []);

  const sanitizePortfolioName = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9-]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
  };

  const handlePortfolioNameChange = (value: string) => {
    const sanitized = sanitizePortfolioName(value);
    onPortfolioNameChange(sanitized);
  };

  const protocol = currentHost.includes('localhost') ? 'http' : 'https';
  const finalPortfolioName = portfolioName || 'your-portfolio-name';
  const fullUrl = `${protocol}://${currentHost}/@${username}/${finalPortfolioName}`;

  const copyUrl = () => {
    navigator.clipboard.writeText(fullUrl);
    addNotification({ 
      title: 'URL Copied',
      message: 'Portfolio URL copied to clipboard!', 
      type: 'success' 
    });
  };

  const openPreview = () => {
    // In a real implementation, this would open the actual portfolio
    window.open(fullUrl, '_blank');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Globe className="w-5 h-5 mr-2 text-teal-600" />
          Portfolio URL Preview
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="portfolioName">Portfolio Name</Label>
          <Input
            id="portfolioName"
            value={portfolioName || ''}
            onChange={(e) => handlePortfolioNameChange(e.target.value)}
            placeholder="my-awesome-portfolio"
            className="mt-1"
          />
          <p className="text-xs text-gray-500 mt-1">
            Only lowercase letters, numbers, and hyphens are allowed.
          </p>
        </div>

        <div className="bg-gray-50 border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h3 className="font-medium text-gray-900 mb-2">Your Portfolio URL</h3>
              <div className="font-mono text-sm break-all bg-white border rounded px-3 py-2">
                <span className="text-gray-500">{protocol}://</span>
                <span className="text-blue-600">{currentHost}</span>
                <span className="text-gray-500">/@</span>
                <span className="text-green-600">{username}</span>
                <span className="text-gray-500">/</span>
                <span className="text-purple-600">{finalPortfolioName}</span>
              </div>
              <div className="mt-2 text-xs text-gray-500 space-y-1">
                <div>
                  <span className="font-medium text-blue-600">Host:</span> {currentHost}
                </div>
                <div>
                  <span className="font-medium text-green-600">Username:</span> @{username}
                </div>
                <div>
                  <span className="font-medium text-purple-600">Portfolio:</span> {finalPortfolioName}
                </div>
              </div>
            </div>
            <div className="flex flex-col space-y-2 ml-4">
              <Button
                variant="outline"
                size="sm"
                onClick={copyUrl}
              >
                <Copy className="w-4 h-4 mr-2" />
                Copy
              </Button>
              <Button
                size="sm"
                onClick={openPreview}
                className="bg-teal-600 hover:bg-teal-700"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Preview
              </Button>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <h4 className="font-medium text-blue-900 mb-1">URL Structure Explained</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• <strong>Host:</strong> Your current domain ({currentHost})</li>
            <li>• <strong>@username:</strong> Your unique username (from email or name)</li>
            <li>• <strong>portfolio-name:</strong> Custom name for this portfolio</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}