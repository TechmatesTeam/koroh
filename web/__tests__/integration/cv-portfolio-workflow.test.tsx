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

// Helper function to get file input
const getFileInput = () => {
  return screen.getByRole('presentation').querySelector('input[type="file"]') as HTMLInputElement;
};

const mockAddNotification = jest.fn();
const mockUploadCV = jest.fn();
const mockGeneratePortfolio = jest.fn();
const mockGetPortfolios = jest.fn();
const mockUpdatePortfolio = jest.fn();

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

describe('CV Upload to Portfolio Generation Workflow', () => {
  it('completes full workflow from CV upload to portfolio generation', async () => {
    const user = userEvent.setup();
    
    // Mock successful CV upload
    const mockCVResponse = {
      data: {
        id: 'cv-123',
        status: 'processed',
        extracted_data: {
          name: 'John Doe',
          title: 'Software Engineer',
          skills: ['JavaScript', 'React', 'Node.js'],
          experience: [
            {
              company: 'Tech Corp',
              position: 'Senior Developer',
              duration: '2020-2023'
            }
          ]
        }
      }
    };
    
    // Mock successful portfolio generation
    const mockPortfolioResponse = {
      data: {
        id: 'portfolio-123',
        url: 'https://portfolio.example.com/johndoe',
        template: 'modern-pro',
        customizations: {
          theme: 'light',
          primaryColor: '#0d9488',
          font: 'inter',
          layout: 'standard',
        },
        content: {
          title: 'John Doe',
          subtitle: 'Software Engineer',
          bio: 'Experienced software engineer with expertise in modern web technologies.',
          skills: ['JavaScript', 'React', 'Node.js'],
          experience: mockCVResponse.data.extracted_data.experience,
        },
      }
    };
    
    mockUploadCV.mockResolvedValueOnce(mockCVResponse);
    mockGeneratePortfolio.mockResolvedValueOnce(mockPortfolioResponse);
    mockGetPortfolios.mockResolvedValueOnce({ data: [] });
    
    // Step 1: Upload CV
    const { rerender } = render(<CVUpload />);
    
    const mockFile = new File(['test cv content'], 'john-doe-cv.pdf', { 
      type: 'application/pdf' 
    });
    
    const fileInput = screen.getByRole('textbox', { hidden: true });
    await user.upload(fileInput, mockFile);
    
    await waitFor(() => {
      expect(mockUploadCV).toHaveBeenCalledWith(expect.any(FormData));
      expect(mockAddNotification).toHaveBeenCalledWith({
        message: 'CV uploaded successfully!',
        type: 'success'
      });
    });
    
    // Step 2: Generate Portfolio
    rerender(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Choose Your Portfolio Template')).toBeInTheDocument();
    });
    
    // Select template
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    // Generate portfolio
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    await waitFor(() => {
      expect(mockGeneratePortfolio).toHaveBeenCalled();
      expect(mockAddNotification).toHaveBeenCalledWith({
        message: 'Portfolio generated successfully!',
        type: 'success'
      });
    });
    
    // Step 3: Verify customization interface appears
    await waitFor(() => {
      expect(screen.getByText('Customize Your Portfolio')).toBeInTheDocument();
    });
    
    // Verify CV data is populated
    expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Software Engineer')).toBeInTheDocument();
  });

  it('handles CV upload failure gracefully', async () => {
    const user = userEvent.setup();
    
    const mockError = {
      response: {
        data: { message: 'Invalid file format' }
      }
    };
    
    mockUploadCV.mockRejectedValueOnce(mockError);
    
    render(<CVUpload />);
    
    const mockFile = new File(['invalid content'], 'invalid.txt', { 
      type: 'text/plain' 
    });
    
    const fileInput = screen.getByRole('textbox', { hidden: true });
    await user.upload(fileInput, mockFile);
    
    await waitFor(() => {
      expect(mockAddNotification).toHaveBeenCalledWith({
        message: 'Invalid file format',
        type: 'error'
      });
    });
    
    // Verify error state is displayed
    expect(screen.getByText('Invalid file format')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('handles portfolio generation failure after successful CV upload', async () => {
    const user = userEvent.setup();
    
    // Successful CV upload
    mockUploadCV.mockResolvedValueOnce({
      data: { id: 'cv-123', status: 'processed' }
    });
    
    // Failed portfolio generation
    const mockError = {
      response: {
        data: { message: 'Insufficient CV data for portfolio generation' }
      }
    };
    mockGeneratePortfolio.mockRejectedValueOnce(mockError);
    mockGetPortfolios.mockResolvedValueOnce({ data: [] });
    
    // Upload CV first
    const { rerender } = render(<CVUpload />);
    
    const mockFile = new File(['test cv content'], 'test-cv.pdf', { 
      type: 'application/pdf' 
    });
    
    const fileInput = screen.getByRole('textbox', { hidden: true });
    await user.upload(fileInput, mockFile);
    
    await waitFor(() => {
      expect(mockUploadCV).toHaveBeenCalled();
    });
    
    // Try to generate portfolio
    rerender(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    await waitFor(() => {
      expect(mockAddNotification).toHaveBeenCalledWith({
        message: 'Insufficient CV data for portfolio generation',
        type: 'error'
      });
    });
  });

  it('supports portfolio customization after generation', async () => {
    const user = userEvent.setup();
    
    const mockPortfolioData = {
      id: 'portfolio-123',
      url: 'https://portfolio.example.com/user',
      template: 'modern-pro',
      customizations: {
        theme: 'light',
        primaryColor: '#0d9488',
        font: 'inter',
        layout: 'standard',
      },
      content: {
        title: 'Jane Smith',
        subtitle: 'UX Designer',
        bio: 'Creative UX designer...',
      },
    };
    
    mockGeneratePortfolio.mockResolvedValueOnce({ data: mockPortfolioData });
    mockUpdatePortfolio.mockResolvedValueOnce({ data: mockPortfolioData });
    mockGetPortfolios.mockResolvedValueOnce({ data: [] });
    
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    // Generate portfolio
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Customize Your Portfolio')).toBeInTheDocument();
    });
    
    // Customize content
    const titleInput = screen.getByLabelText('Portfolio Title');
    await user.clear(titleInput);
    await user.type(titleInput, 'Jane Smith Updated');
    
    // Change color theme
    const blueColor = screen.getByText('Blue').closest('button');
    await user.click(blueColor!);
    
    // Save changes
    const saveButton = screen.getByText('Save Changes');
    await user.click(saveButton);
    
    await waitFor(() => {
      expect(mockUpdatePortfolio).toHaveBeenCalledWith(
        'portfolio-123',
        expect.objectContaining({
          customizations: expect.objectContaining({
            primaryColor: '#2563eb' // Blue color value
          }),
          content: expect.objectContaining({
            title: 'Jane Smith Updated'
          })
        })
      );
    });
  });

  it('validates file size limits during upload', async () => {
    const user = userEvent.setup();
    
    render(<CVUpload />);
    
    // Create a file larger than 10MB
    const largeContent = 'x'.repeat(11 * 1024 * 1024); // 11MB
    const largeFile = new File([largeContent], 'large-cv.pdf', { 
      type: 'application/pdf' 
    });
    
    const fileInput = screen.getByRole('textbox', { hidden: true });
    
    // This should be rejected by react-dropzone due to size limit
    await user.upload(fileInput, largeFile);
    
    // File should not appear in upload list due to size validation
    expect(screen.queryByText('large-cv.pdf')).not.toBeInTheDocument();
  });

  it('supports multiple file format uploads', async () => {
    const user = userEvent.setup();
    
    const mockResponse = { data: { id: 'cv-123', status: 'processed' } };
    mockUploadCV.mockResolvedValue(mockResponse);
    
    render(<CVUpload />);
    
    const fileFormats = [
      { name: 'test.pdf', type: 'application/pdf' },
      { name: 'test.doc', type: 'application/msword' },
      { name: 'test.docx', type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' },
      { name: 'test.md', type: 'text/markdown' },
    ];
    
    for (const format of fileFormats) {
      const mockFile = new File(['test content'], format.name, { type: format.type });
      const fileInput = screen.getByRole('textbox', { hidden: true });
      
      await user.upload(fileInput, mockFile);
      
      await waitFor(() => {
        expect(screen.getByText(format.name)).toBeInTheDocument();
      });
      
      // Remove file for next iteration
      const removeButton = screen.getByRole('button', { name: /remove/i });
      await user.click(removeButton);
    }
  });

  it('displays progress and completion states correctly', async () => {
    const user = userEvent.setup();
    
    // Mock delayed response to observe progress
    mockUploadCV.mockImplementation(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({ data: { id: 'cv-123' } }), 500)
      )
    );
    
    render(<CVUpload />);
    
    const mockFile = new File(['test content'], 'test-cv.pdf', { 
      type: 'application/pdf' 
    });
    
    const fileInput = screen.getByRole('textbox', { hidden: true });
    await user.upload(fileInput, mockFile);
    
    // Check uploading state
    await waitFor(() => {
      expect(screen.getByText('Uploading...')).toBeInTheDocument();
    });
    
    // Check completion state
    await waitFor(() => {
      expect(screen.getByText('CV uploaded successfully! AI analysis will begin shortly.')).toBeInTheDocument();
    }, { timeout: 1000 });
  });
});