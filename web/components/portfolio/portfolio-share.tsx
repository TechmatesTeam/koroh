'use client';

import { useState } from 'react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Share2, 
  Copy, 
  Mail, 
  MessageSquare, 
  Linkedin, 
  Twitter, 
  Facebook,
  QrCode,
  Download,
  ExternalLink
} from 'lucide-react';
import { useNotifications } from '@/contexts/notification-context';

interface PortfolioShareProps {
  isOpen: boolean;
  onClose: () => void;
  portfolioUrl: string;
  portfolioTitle: string;
}

export function PortfolioShare({ 
  isOpen, 
  onClose, 
  portfolioUrl, 
  portfolioTitle 
}: PortfolioShareProps) {
  const [customMessage, setCustomMessage] = useState('');
  const { addNotification } = useNotifications();

  const copyToClipboard = () => {
    navigator.clipboard.writeText(portfolioUrl);
    addNotification({ 
      title: 'URL Copied',
      message: 'Portfolio URL copied to clipboard!', 
      type: 'success' 
    });
  };

  const shareViaEmail = () => {
    const subject = encodeURIComponent(`Check out my professional portfolio: ${portfolioTitle}`);
    const body = encodeURIComponent(
      `Hi,\n\nI'd like to share my professional portfolio with you:\n\n${portfolioUrl}\n\n${customMessage}\n\nBest regards`
    );
    window.open(`mailto:?subject=${subject}&body=${body}`);
  };

  const shareViaLinkedIn = () => {
    const url = encodeURIComponent(portfolioUrl);
    const title = encodeURIComponent(`Check out my professional portfolio: ${portfolioTitle}`);
    window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${url}&title=${title}`, '_blank');
  };

  const shareViaTwitter = () => {
    const text = encodeURIComponent(`Check out my professional portfolio: ${portfolioTitle}`);
    const url = encodeURIComponent(portfolioUrl);
    window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}`, '_blank');
  };

  const shareViaFacebook = () => {
    const url = encodeURIComponent(portfolioUrl);
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank');
  };

  const shareViaSMS = () => {
    const message = encodeURIComponent(
      `Check out my professional portfolio: ${portfolioTitle} - ${portfolioUrl}`
    );
    window.open(`sms:?body=${message}`);
  };

  const generateQRCode = () => {
    // In a real implementation, you would generate a QR code
    // For now, we'll just show a placeholder
    addNotification({ 
      title: 'Coming Soon',
      message: 'QR Code generation coming soon!', 
      type: 'info' 
    });
  };

  const downloadPortfolio = () => {
    // In a real implementation, you would generate a PDF version
    addNotification({ 
      title: 'Coming Soon',
      message: 'PDF download coming soon!', 
      type: 'info' 
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Share Your Portfolio">
      <div className="space-y-6">
        {/* Portfolio URL */}
        <div>
          <Label htmlFor="portfolio-url">Portfolio URL</Label>
          <div className="flex mt-1">
            <Input
              id="portfolio-url"
              value={portfolioUrl}
              readOnly
              className="flex-1 font-mono text-sm"
            />
            <Button
              onClick={copyToClipboard}
              variant="outline"
              className="ml-2"
            >
              <Copy className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Custom Message */}
        <div>
          <Label htmlFor="custom-message">Custom Message (Optional)</Label>
          <textarea
            id="custom-message"
            value={customMessage}
            onChange={(e) => setCustomMessage(e.target.value)}
            placeholder="Add a personal message when sharing..."
            className="w-full mt-1 p-3 border border-gray-300 rounded-md resize-none"
            rows={3}
          />
        </div>

        {/* Share Options */}
        <div>
          <h3 className="font-medium text-gray-900 mb-4">Share Options</h3>
          <div className="grid grid-cols-2 gap-3">
            {/* Email */}
            <Button
              onClick={shareViaEmail}
              variant="outline"
              className="flex items-center justify-center space-x-2 h-12"
            >
              <Mail className="w-5 h-5 text-blue-600" />
              <span>Email</span>
            </Button>

            {/* LinkedIn */}
            <Button
              onClick={shareViaLinkedIn}
              variant="outline"
              className="flex items-center justify-center space-x-2 h-12"
            >
              <Linkedin className="w-5 h-5 text-blue-700" />
              <span>LinkedIn</span>
            </Button>

            {/* Twitter */}
            <Button
              onClick={shareViaTwitter}
              variant="outline"
              className="flex items-center justify-center space-x-2 h-12"
            >
              <Twitter className="w-5 h-5 text-blue-400" />
              <span>Twitter</span>
            </Button>

            {/* Facebook */}
            <Button
              onClick={shareViaFacebook}
              variant="outline"
              className="flex items-center justify-center space-x-2 h-12"
            >
              <Facebook className="w-5 h-5 text-blue-600" />
              <span>Facebook</span>
            </Button>

            {/* SMS */}
            <Button
              onClick={shareViaSMS}
              variant="outline"
              className="flex items-center justify-center space-x-2 h-12"
            >
              <MessageSquare className="w-5 h-5 text-green-600" />
              <span>SMS</span>
            </Button>

            {/* QR Code */}
            <Button
              onClick={generateQRCode}
              variant="outline"
              className="flex items-center justify-center space-x-2 h-12"
            >
              <QrCode className="w-5 h-5 text-gray-600" />
              <span>QR Code</span>
            </Button>
          </div>
        </div>

        {/* Additional Actions */}
        <div className="border-t pt-4">
          <h3 className="font-medium text-gray-900 mb-4">Additional Actions</h3>
          <div className="flex space-x-3">
            <Button
              onClick={() => window.open(portfolioUrl, '_blank')}
              variant="outline"
              className="flex-1"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              Open Portfolio
            </Button>
            <Button
              onClick={downloadPortfolio}
              variant="outline"
              className="flex-1"
            >
              <Download className="w-4 h-4 mr-2" />
              Download PDF
            </Button>
          </div>
        </div>

        {/* Close Button */}
        <div className="flex justify-end pt-4 border-t">
          <Button onClick={onClose} variant="outline">
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}