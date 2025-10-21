import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CVUpload } from '../../components/cv/cv-upload';
import { PortfolioGenerator } from '../../components/portfolio/portfolio-generator';
import { useNotifications } from '../../contexts/notification-context';
import { api } from '../../lib/api';

// Mock dependencies
jest.mock('../../contexts/notification-context');
jest.mock('../../lib/api');

const mockAddNotification = jest.fn();
const mockUploadCV = jest.fn();
const mockGeneratePortfolio = jest.fn();
const mockGetPortfolios = jest.fn();
const mockUpdatePortfolio = jest.fn();

// Helper function to get file input
const getFileInput = () => {
  return screen.getByRole('presentation').querySelector('input[type="file"]') as HTMLInputElement;
};

beforeEach(() => {
  (useNotifications as jest.Mock).mockReturnValue({
    addNotification: mockAddNotification,
  });
  
  (api.profiles.uploadCV as jest.Mock) = mockUploadCV;
  (api.profiles.generatePortfolio as jest.Mock) = mockGeneratePortfolio;
  (api.profiles.getPortfolios as jest.Mock) = mockGetPortfolios;
  (api.profiles.updatePortfolio as jest.Mock) = mockUpdatePortfolio;
  
  // Clear all mocks
  jest.clearAllMocks();
});

describe('CV Upload to Portfolio Generation Workflow - Core Tests', () => {
  it('successfully uploads CV file', async () => {
    const user = userEvent.setup();
    
    const mockCVResponse = {
      data: {
        id: 'cv-123',
        status: 'processed',
        extracted_data: {
          name: 'John Doe',
          title: 'Software Engineer',
          skills: ['JavaScript', 'React', 'Node.js'],
        }
      }
    };
    
    mockUploadCV.mockResolvedValueOnce(mockCVResponse);
    
    render(<CVUpload />);
    
    const mockFile = new File(['test cv content'], 'john-doe-cv.pdf', { 
      type: 'application/pdf' 
    });
    
    const fileInput = getFileInput();
    await user.upload(fileInput, mockFile);
    
    await waitFor(() => {
      expect(mockUploadCV).toHaveBeenCalledWith(expect.any(FormData));
      expect(mockAddNotification).toHaveBeenCalledWith({
        message: 'CV uploaded successfully!',
        type: 'success'
      });
    });
  });

  it('displays portfolio generator interface', async () => {
    mockGetPortfolios.mockResolvedValueOnce({ data: [] });
    
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Choose Your Portfolio Template')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    expect(screen.getByText('Generate Portfolio')).toBeInTheDocument();
  });

  it('handles CV upload errors gracefully', async () => {
    const user = userEvent.setup();
    
    const mockError = {
      response: {
        data: { message: 'File too large' }
      }
    };
    
    mockUploadCV.mockRejectedValueOnce(mockError);
    
    render(<CVUpload />);
    
    // Use a valid file type that will pass dropzone validation
    const mockFile = new File(['test content'], 'test.pdf', { 
      type: 'application/pdf' 
    });
    
    const fileInput = getFileInput();
    await user.upload(fileInput, mockFile);
    
    await waitFor(() => {
      expect(mockAddNotification).toHaveBeenCalledWith({
        message: 'File too large',
        type: 'error'
      });
    });
  });

  it('validates supported file formats', async () => {
    const user = userEvent.setup();
    
    const mockResponse = { data: { id: 'cv-123', status: 'processed' } };
    mockUploadCV.mockResolvedValue(mockResponse);
    
    render(<CVUpload />);
    
    const supportedFormats = [
      { name: 'test.pdf', type: 'application/pdf' },
      { name: 'test.doc', type: 'application/msword' },
      { name: 'test.docx', type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' },
      { name: 'test.md', type: 'text/markdown' },
    ];
    
    for (const format of supportedFormats) {
      const mockFile = new File(['test content'], format.name, { type: format.type });
      const fileInput = getFileInput();
      
      await user.upload(fileInput, mockFile);
      
      await waitFor(() => {
        expect(screen.getByText(format.name)).toBeInTheDocument();
      });
      
      // Remove file for next iteration
      const removeButtons = screen.getAllByRole('button');
      const removeButton = removeButtons.find(btn => btn.querySelector('svg'));
      if (removeButton) {
        await user.click(removeButton);
      }
    }
  });

  it('shows upload progress indicators', async () => {
    const user = userEvent.setup();
    
    // Mock delayed response to observe progress
    mockUploadCV.mockImplementation(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({ data: { id: 'cv-123' } }), 100)
      )
    );
    
    render(<CVUpload />);
    
    const mockFile = new File(['test content'], 'test-cv.pdf', { 
      type: 'application/pdf' 
    });
    
    const fileInput = getFileInput();
    await user.upload(fileInput, mockFile);
    
    // Check uploading state appears
    await waitFor(() => {
      expect(screen.getByText('Uploading...')).toBeInTheDocument();
    });
    
    // Check completion state
    await waitFor(() => {
      expect(screen.getByText('CV uploaded successfully! AI analysis will begin shortly.')).toBeInTheDocument();
    }, { timeout: 1000 });
  });

  it('displays file size information', async () => {
    const user = userEvent.setup();
    
    mockUploadCV.mockResolvedValueOnce({ data: { id: 'cv-123' } });
    
    render(<CVUpload />);
    
    const mockFile = new File(['x'.repeat(1024)], 'test-cv.pdf', { 
      type: 'application/pdf' 
    });
    
    const fileInput = getFileInput();
    await user.upload(fileInput, mockFile);
    
    await waitFor(() => {
      expect(screen.getByText('1 KB')).toBeInTheDocument();
    });
  });

  it('allows file retry on upload failure', async () => {
    const user = userEvent.setup();
    
    // First call fails, second succeeds
    mockUploadCV
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({ data: { id: 'cv-123' } });
    
    render(<CVUpload />);
    
    const mockFile = new File(['test content'], 'test-cv.pdf', { 
      type: 'application/pdf' 
    });
    
    const fileInput = getFileInput();
    await user.upload(fileInput, mockFile);
    
    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
    
    const retryButton = screen.getByText('Retry');
    await user.click(retryButton);
    
    await waitFor(() => {
      expect(mockUploadCV).toHaveBeenCalledTimes(2);
    });
  });

  it('renders portfolio templates correctly', async () => {
    mockGetPortfolios.mockResolvedValueOnce({ data: [] });
    
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Choose Your Portfolio Template')).toBeInTheDocument();
    });
    
    // Check all templates are displayed
    expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    expect(screen.getByText('Classic Elegant')).toBeInTheDocument();
    expect(screen.getByText('Creative Bold')).toBeInTheDocument();
    expect(screen.getByText('Minimal Clean')).toBeInTheDocument();
    
    // Check template descriptions
    expect(screen.getByText('Clean, modern design perfect for tech professionals')).toBeInTheDocument();
    expect(screen.getByText('Timeless design suitable for all industries')).toBeInTheDocument();
  });

  it('handles portfolio API errors gracefully', async () => {
    const mockError = new Error('Portfolio API error');
    mockGetPortfolios.mockRejectedValueOnce(mockError);
    
    render(<PortfolioGenerator />);
    
    // Component should still render despite API error
    await waitFor(() => {
      expect(screen.getByText('Choose Your Portfolio Template')).toBeInTheDocument();
    });
  });

  it('displays upload guidelines', () => {
    render(<CVUpload />);
    
    expect(screen.getByText('Upload Guidelines')).toBeInTheDocument();
    expect(screen.getByText(/Ensure your CV is up-to-date/)).toBeInTheDocument();
    expect(screen.getByText(/Include clear section headers/)).toBeInTheDocument();
    expect(screen.getByText(/File size should not exceed 10MB/)).toBeInTheDocument();
  });

  it('shows template features', async () => {
    mockGetPortfolios.mockResolvedValueOnce({ data: [] });
    
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Responsive Design')).toBeInTheDocument();
      expect(screen.getByText('Dark Mode')).toBeInTheDocument();
      expect(screen.getByText('Professional Layout')).toBeInTheDocument();
      expect(screen.getByText('Portfolio Gallery')).toBeInTheDocument();
    });
  });
});