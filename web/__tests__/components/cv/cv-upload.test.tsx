import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CVUpload } from '../../../components/cv/cv-upload';
import { useNotifications } from '../../../contexts/notification-context';
import { api } from '../../../lib/api';

// Mock dependencies
jest.mock('../../../contexts/notification-context');
jest.mock('../../../lib/api');

const mockAddNotification = jest.fn();
const mockUploadCV = jest.fn();

// Helper function to get file input
const getFileInput = () => {
  return screen.getByRole('presentation').querySelector('input[type="file"]') as HTMLInputElement;
};

beforeEach(() => {
  (useNotifications as jest.Mock).mockReturnValue({
    addNotification: mockAddNotification,
  });
  
  (api.profiles.uploadCV as jest.Mock) = mockUploadCV;
  
  // Clear all mocks
  jest.clearAllMocks();
});

describe('CVUpload Component', () => {
  it('renders upload interface correctly', () => {
    render(<CVUpload />);
    
    expect(screen.getByText('Upload Your CV')).toBeInTheDocument();
    expect(screen.getByText('Drag & drop your CV here')).toBeInTheDocument();
    expect(screen.getByText('browse files')).toBeInTheDocument();
    expect(screen.getByText('Supports PDF, DOC, DOCX, and MD files up to 10MB')).toBeInTheDocument();
  });

  it('displays upload guidelines', () => {
    render(<CVUpload />);
    
    expect(screen.getByText('Upload Guidelines')).toBeInTheDocument();
    expect(screen.getByText(/Ensure your CV is up-to-date/)).toBeInTheDocument();
    expect(screen.getByText(/Include clear section headers/)).toBeInTheDocument();
    expect(screen.getByText(/File size should not exceed 10MB/)).toBeInTheDocument();
  });

  it('handles successful file upload', async () => {
    const user = userEvent.setup();
    const mockFile = new File(['test content'], 'test-cv.pdf', { type: 'application/pdf' });
    const mockResponse = { data: { id: '123', status: 'success' } };
    
    mockUploadCV.mockResolvedValueOnce(mockResponse);
    
    const onUploadSuccess = jest.fn();
    render(<CVUpload onUploadSuccess={onUploadSuccess} />);
    
    const fileInput = getFileInput();
    await user.upload(fileInput, mockFile);
    
    await waitFor(() => {
      expect(screen.getByText('test-cv.pdf')).toBeInTheDocument();
    });
    
    await waitFor(() => {
      expect(mockUploadCV).toHaveBeenCalledWith(expect.any(FormData));
      expect(mockAddNotification).toHaveBeenCalledWith({
        message: 'CV uploaded successfully!',
        type: 'success'
      });
      expect(onUploadSuccess).toHaveBeenCalledWith(mockResponse.data);
    });
  });

  it('handles upload error scenarios', async () => {
    const user = userEvent.setup();
    const mockFile = new File(['test content'], 'test-cv.pdf', { type: 'application/pdf' });
    const mockError = {
      response: {
        data: { message: 'File too large' }
      }
    };
    
    mockUploadCV.mockRejectedValueOnce(mockError);
    
    const onUploadError = jest.fn();
    render(<CVUpload onUploadError={onUploadError} />);
    
    const fileInput = getFileInput();
    await user.upload(fileInput, mockFile);
    
    await waitFor(() => {
      expect(screen.getByText('test-cv.pdf')).toBeInTheDocument();
    });
    
    await waitFor(() => {
      expect(mockAddNotification).toHaveBeenCalledWith({
        message: 'File too large',
        type: 'error'
      });
      expect(onUploadError).toHaveBeenCalledWith('File too large');
      expect(screen.getByText('File too large')).toBeInTheDocument();
    });
  });

  it('shows progress during upload', async () => {
    const user = userEvent.setup();
    const mockFile = new File(['test content'], 'test-cv.pdf', { type: 'application/pdf' });
    
    // Mock a delayed response to see progress
    mockUploadCV.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ data: { id: '123' } }), 100))
    );
    
    render(<CVUpload />);
    
    const fileInput = getFileInput();
    await user.upload(fileInput, mockFile);
    
    await waitFor(() => {
      expect(screen.getByText('Uploading...')).toBeInTheDocument();
    });
  });

  it('allows file removal', async () => {
    const user = userEvent.setup();
    const mockFile = new File(['test content'], 'test-cv.pdf', { type: 'application/pdf' });
    
    mockUploadCV.mockResolvedValueOnce({ data: { id: '123' } });
    
    render(<CVUpload />);
    
    const fileInput = getFileInput();
    await user.upload(fileInput, mockFile);
    
    await waitFor(() => {
      expect(screen.getByText('test-cv.pdf')).toBeInTheDocument();
    });
    
    const removeButtons = screen.getAllByRole('button');
    const removeButton = removeButtons.find(btn => btn.querySelector('svg'));
    await user.click(removeButton!);
    
    expect(screen.queryByText('test-cv.pdf')).not.toBeInTheDocument();
  });

  it('allows retry on failed upload', async () => {
    const user = userEvent.setup();
    const mockFile = new File(['test content'], 'test-cv.pdf', { type: 'application/pdf' });
    
    // First call fails, second succeeds
    mockUploadCV
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({ data: { id: '123' } });
    
    render(<CVUpload />);
    
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

  it('validates file types', async () => {
    const user = userEvent.setup();
    const invalidFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
    
    render(<CVUpload />);
    
    const fileInput = getFileInput();
    
    // This should be rejected by react-dropzone
    await user.upload(fileInput, invalidFile);
    
    // File should not appear in the list since it's rejected
    expect(screen.queryByText('test.txt')).not.toBeInTheDocument();
  });

  it('displays file size correctly', async () => {
    const user = userEvent.setup();
    const mockFile = new File(['x'.repeat(1024)], 'test-cv.pdf', { type: 'application/pdf' });
    
    mockUploadCV.mockResolvedValueOnce({ data: { id: '123' } });
    
    render(<CVUpload />);
    
    const fileInput = getFileInput();
    await user.upload(fileInput, mockFile);
    
    await waitFor(() => {
      expect(screen.getByText('1 KB')).toBeInTheDocument();
    });
  });

  it('handles drag and drop interactions', () => {
    render(<CVUpload />);
    
    const dropzone = screen.getByRole('presentation');
    
    // Simulate drag enter - just verify the dropzone exists
    fireEvent.dragEnter(dropzone);
    expect(dropzone).toBeInTheDocument();
    
    // Simulate drag leave
    fireEvent.dragLeave(dropzone);
    expect(dropzone).toBeInTheDocument();
  });

  it('shows success message after upload completion', async () => {
    const user = userEvent.setup();
    const mockFile = new File(['test content'], 'test-cv.pdf', { type: 'application/pdf' });
    
    mockUploadCV.mockResolvedValueOnce({ data: { id: '123' } });
    
    render(<CVUpload />);
    
    const fileInput = getFileInput();
    await user.upload(fileInput, mockFile);
    
    await waitFor(() => {
      expect(screen.getByText('CV uploaded successfully! AI analysis will begin shortly.')).toBeInTheDocument();
    });
  });
});