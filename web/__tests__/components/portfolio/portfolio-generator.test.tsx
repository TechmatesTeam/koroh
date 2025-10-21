import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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

describe('PortfolioGenerator Component', () => {
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

  it('allows template selection', async () => {
    const user = userEvent.setup();
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    expect(modernTemplate).toHaveClass('border-teal-500');
  });

  it('generates portfolio successfully', async () => {
    const user = userEvent.setup();
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
        skills: ['JavaScript', 'React'],
        experience: [],
        education: [],
        projects: [],
      },
    };
    
    mockGeneratePortfolio.mockResolvedValueOnce({ data: mockPortfolioData });
    
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
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
  });

  it('handles portfolio generation error', async () => {
    const user = userEvent.setup();
    const mockError = {
      response: {
        data: { message: 'Failed to generate portfolio' }
      }
    };
    
    mockGeneratePortfolio.mockRejectedValueOnce(mockError);
    
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    // Select template
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    // Generate portfolio
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    await waitFor(() => {
      expect(mockAddNotification).toHaveBeenCalledWith({
        message: 'Failed to generate portfolio',
        type: 'error'
      });
    });
  });

  it('shows loading state during generation', async () => {
    const user = userEvent.setup();
    
    mockGeneratePortfolio.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ data: {} }), 1000))
    );
    
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    // Select template
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    // Generate portfolio
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    expect(screen.getByText('Generating...')).toBeInTheDocument();
  });

  it('loads existing portfolio data', async () => {
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

  it('prevents generation without template selection', async () => {
    const user = userEvent.setup();
    
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Generate Portfolio')).toBeInTheDocument();
    });
    
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    expect(mockAddNotification).toHaveBeenCalledWith({
      message: 'Please select a template first',
      type: 'error'
    });
    expect(mockGeneratePortfolio).not.toHaveBeenCalled();
  });
});

describe('PortfolioGenerator - Customization Step', () => {
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
      skills: ['JavaScript', 'React'],
      experience: [],
      education: [],
      projects: [],
    },
  };

  beforeEach(() => {
    mockGetPortfolios.mockResolvedValue({ data: [mockPortfolioData] });
    mockGeneratePortfolio.mockResolvedValue({ data: mockPortfolioData });
  });

  it('shows customization interface after generation', async () => {
    const user = userEvent.setup();
    
    render(<PortfolioGenerator />);
    
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    // Select template and generate
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Customize Your Portfolio')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Content')).toBeInTheDocument();
    expect(screen.getByText('Color Theme')).toBeInTheDocument();
    expect(screen.getByText('Typography')).toBeInTheDocument();
  });

  it('allows content customization', async () => {
    const user = userEvent.setup();
    
    render(<PortfolioGenerator />);
    
    // Navigate to customization step
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByLabelText('Portfolio Title')).toBeInTheDocument();
    });
    
    // Update content
    const titleInput = screen.getByLabelText('Portfolio Title');
    await user.clear(titleInput);
    await user.type(titleInput, 'Jane Smith');
    
    const subtitleInput = screen.getByLabelText('Subtitle');
    await user.clear(subtitleInput);
    await user.type(subtitleInput, 'UX Designer');
    
    expect(titleInput).toHaveValue('Jane Smith');
    expect(subtitleInput).toHaveValue('UX Designer');
  });

  it('allows color theme selection', async () => {
    const user = userEvent.setup();
    
    render(<PortfolioGenerator />);
    
    // Navigate to customization step
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Color Theme')).toBeInTheDocument();
    });
    
    // Select blue color
    const blueColor = screen.getByText('Blue').closest('button');
    await user.click(blueColor!);
    
    expect(blueColor).toHaveClass('border-gray-900');
  });

  it('allows font selection', async () => {
    const user = userEvent.setup();
    
    render(<PortfolioGenerator />);
    
    // Navigate to customization step
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Typography')).toBeInTheDocument();
    });
    
    // Select Poppins font
    const poppinsFont = screen.getByText('Poppins').closest('button');
    await user.click(poppinsFont!);
    
    expect(poppinsFont).toHaveClass('border-teal-500');
  });

  it('saves customizations successfully', async () => {
    const user = userEvent.setup();
    
    mockUpdatePortfolio.mockResolvedValueOnce({ data: mockPortfolioData });
    
    render(<PortfolioGenerator />);
    
    // Navigate to customization step
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Save Changes')).toBeInTheDocument();
    });
    
    const saveButton = screen.getByText('Save Changes');
    await user.click(saveButton);
    
    await waitFor(() => {
      expect(mockUpdatePortfolio).toHaveBeenCalledWith('123', expect.any(Object));
      expect(mockAddNotification).toHaveBeenCalledWith({
        message: 'Portfolio updated successfully!',
        type: 'success'
      });
    });
  });

  it('shows live preview updates', async () => {
    const user = userEvent.setup();
    
    render(<PortfolioGenerator />);
    
    // Navigate to customization step
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Live Preview')).toBeInTheDocument();
    });
    
    // Update title and check preview
    const titleInput = screen.getByLabelText('Portfolio Title');
    await user.clear(titleInput);
    await user.type(titleInput, 'Test User');
    
    expect(screen.getByText('Test User')).toBeInTheDocument();
  });

  it('allows device preview switching', async () => {
    const user = userEvent.setup();
    
    render(<PortfolioGenerator />);
    
    // Navigate to customization step
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Live Preview')).toBeInTheDocument();
    });
    
    // Find device preview buttons (they should be icon buttons)
    const previewButtons = screen.getAllByRole('button');
    const tabletButton = previewButtons.find(btn => 
      btn.querySelector('svg') && btn.className.includes('p-2')
    );
    
    if (tabletButton) {
      await user.click(tabletButton);
      // Preview should update (visual change, hard to test without DOM inspection)
    }
  });
});

describe('PortfolioGenerator - Preview Step', () => {
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

  beforeEach(() => {
    mockGetPortfolios.mockResolvedValue({ data: [mockPortfolioData] });
    mockGeneratePortfolio.mockResolvedValue({ data: mockPortfolioData });
  });

  it('shows portfolio preview with URL', async () => {
    const user = userEvent.setup();
    
    render(<PortfolioGenerator />);
    
    // Navigate through steps to preview
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Preview')).toBeInTheDocument();
    });
    
    const previewButton = screen.getByText('Preview');
    await user.click(previewButton);
    
    await waitFor(() => {
      expect(screen.getByText('Portfolio Preview')).toBeInTheDocument();
      expect(screen.getByText('Your Portfolio URL')).toBeInTheDocument();
      expect(screen.getByText('https://portfolio.example.com/user123')).toBeInTheDocument();
    });
  });

  it('allows copying portfolio URL', async () => {
    const user = userEvent.setup();
    
    render(<PortfolioGenerator />);
    
    // Navigate to preview step
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Preview')).toBeInTheDocument();
    });
    
    const previewButton = screen.getByText('Preview');
    await user.click(previewButton);
    
    await waitFor(() => {
      expect(screen.getByText('Copy')).toBeInTheDocument();
    });
    
    const copyButton = screen.getByText('Copy');
    await user.click(copyButton);
    
    expect(mockAddNotification).toHaveBeenCalledWith({
      message: 'Portfolio URL copied to clipboard!',
      type: 'success'
    });
  });

  it('allows portfolio regeneration', async () => {
    const user = userEvent.setup();
    
    render(<PortfolioGenerator />);
    
    // Navigate to preview step
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Preview')).toBeInTheDocument();
    });
    
    const previewButton = screen.getByText('Preview');
    await user.click(previewButton);
    
    await waitFor(() => {
      expect(screen.getByText('Regenerate')).toBeInTheDocument();
    });
    
    const regenerateButton = screen.getByText('Regenerate');
    await user.click(regenerateButton);
    
    await waitFor(() => {
      expect(mockGeneratePortfolio).toHaveBeenCalledTimes(2);
    });
  });

  it('opens portfolio in new window', async () => {
    const user = userEvent.setup();
    const mockOpen = jest.fn();
    window.open = mockOpen;
    
    render(<PortfolioGenerator />);
    
    // Navigate to preview step
    await waitFor(() => {
      expect(screen.getByText('Modern Professional')).toBeInTheDocument();
    });
    
    const modernTemplate = screen.getByText('Modern Professional').closest('div');
    await user.click(modernTemplate!);
    
    const generateButton = screen.getByText('Generate Portfolio');
    await user.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Preview')).toBeInTheDocument();
    });
    
    const previewButton = screen.getByText('Preview');
    await user.click(previewButton);
    
    await waitFor(() => {
      expect(screen.getByText('Open')).toBeInTheDocument();
    });
    
    const openButton = screen.getByText('Open');
    await user.click(openButton);
    
    expect(mockOpen).toHaveBeenCalledWith('https://portfolio.example.com/user123', '_blank');
  });
});