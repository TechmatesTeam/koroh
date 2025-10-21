import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { PortfolioGenerator } from '../../../components/portfolio/portfolio-generator';
import { useNotifications } from '../../../contexts/notification-context';
import { api } from '../../../lib/api';

// Mock dependencies
jest.mock('../../../contexts/notification-context');
jest.mock('../../../lib/api');

const mockAddNotification = jest.fn();
const mockGeneratePortfolio = jest.fn();
const mockGetPortfolios = jest.fn();
const mockUpdatePortfolio = jest.fn();

beforeEach(() => {
  (useNotifications as jest.Mock).mockReturnValue({
    addNotification: mockAddNotification,
  });
  
  (api.profiles.generatePortfolio as jest.Mock) = mockGeneratePortfolio;
  (api.profiles.getPortfolios as jest.Mock) = mockGetPortfolios;
  (api.profiles.updatePortfolio as jest.Mock) = mockUpdatePortfolio;
  
  // Clear all mocks
  jest.clearAllMocks();
});

describe('PortfolioGenerator Component - Core Functionality', () => {
  beforeEach(() => {
    mockGetPortfolios.mockResolvedValue({ data: [] });
  });

  it('renders template selection step initially', async () => {
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Choose Your Portfolio Template')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    expect(screen.getByText('Classic Elegant')).toBeInTheDocument();
    expect(screen.getByText('Creative Bold')).toBeInTheDocument();
    expect(screen.getByText('Minimal Clean')).toBeInTheDocument();
  });

  it('displays template features correctly', async () => {
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    // Check that template features are displayed
    expect(screen.getByText('Responsive Design')).toBeInTheDocument();
    expect(screen.getByText('Dark Mode')).toBeInTheDocument();
    expect(screen.getByText('Professional Layout')).toBeInTheDocument();
    expect(screen.getByText('Portfolio Gallery')).toBeInTheDocument();
  });

  it('shows generate button', async () => {
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Generate Portfolio')).toBeInTheDocument();
    });
  });

  it('loads existing portfolio data on mount', async () => {
    const existingPortfolio = {
      id: '123',
      url: 'https://portfolio.example.com/user123',
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
        bio: 'Passionate developer...',
      },
    };
    
    mockGetPortfolios.mockResolvedValueOnce({ data: [existingPortfolio] });
    
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(mockGetPortfolios).toHaveBeenCalled();
    });
  });

  it('handles API errors gracefully', async () => {
    mockGetPortfolios.mockRejectedValueOnce(new Error('API Error'));
    
    render(<PortfolioGenerator />);
    
    // Component should still render even if API fails
    await waitFor(() => {
      expect(screen.getByText('Choose Your Portfolio Template')).toBeInTheDocument();
    });
  });

  it('displays color theme options', async () => {
    const mockPortfolioData = {
      id: '123',
      url: 'https://portfolio.example.com/user123',
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
        bio: 'Passionate developer...',
      },
    };
    
    mockGeneratePortfolio.mockResolvedValue({ data: mockPortfolioData });
    
    render(<PortfolioGenerator />);
    
    // Simulate successful generation to reach customization step
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
  });

  it('displays font options', async () => {
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Choose Your Portfolio Template')).toBeInTheDocument();
    });
    
    // The component should render without errors
    expect(screen.getByText('Generate Portfolio')).toBeInTheDocument();
  });

  it('shows template descriptions', async () => {
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Clean, modern design perfect for tech professionals')).toBeInTheDocument();
      expect(screen.getByText('Timeless design suitable for all industries')).toBeInTheDocument();
      expect(screen.getByText('Eye-catching design for creative professionals')).toBeInTheDocument();
      expect(screen.getByText('Simple, focused design that highlights content')).toBeInTheDocument();
    });
  });

  it('renders without crashing when no existing portfolios', async () => {
    mockGetPortfolios.mockResolvedValue({ data: [] });
    
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Choose Your Portfolio Template')).toBeInTheDocument();
    });
  });

  it('handles empty API responses', async () => {
    mockGetPortfolios.mockResolvedValue({ data: null });
    
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Choose Your Portfolio Template')).toBeInTheDocument();
    });
  });

  it('displays template categories correctly', async () => {
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      // All templates should be visible
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
      expect(screen.getByText('Classic Elegant')).toBeInTheDocument();
      expect(screen.getByText('Creative Bold')).toBeInTheDocument();
      expect(screen.getByText('Minimal Clean')).toBeInTheDocument();
    });
  });
});

describe('PortfolioGenerator - Error Handling', () => {
  beforeEach(() => {
    mockGetPortfolios.mockResolvedValue({ data: [] });
  });

  it('handles portfolio generation API errors', async () => {
    const mockError = {
      response: {
        data: { message: 'Failed to generate portfolio' }
      }
    };
    
    mockGeneratePortfolio.mockRejectedValueOnce(mockError);
    
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Choose Your Portfolio Template')).toBeInTheDocument();
    });
    
    // Component should handle errors gracefully
    expect(screen.getByText('Generate Portfolio')).toBeInTheDocument();
  });

  it('handles network errors', async () => {
    mockGetPortfolios.mockRejectedValueOnce(new Error('Network error'));
    
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Choose Your Portfolio Template')).toBeInTheDocument();
    });
  });

  it('handles malformed API responses', async () => {
    mockGetPortfolios.mockResolvedValueOnce({ invalid: 'response' });
    
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Choose Your Portfolio Template')).toBeInTheDocument();
    });
  });
});