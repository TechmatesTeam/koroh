import { mockApi } from '@/lib/mock-api';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    host: 'localhost:3000',
    origin: 'http://localhost:3000',
  },
  writable: true,
});

describe('Portfolio URL Generation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockImplementation((key) => {
      if (key === 'koroh_current_user') {
        return JSON.stringify({
          id: 'test-user-1',
          email: 'john.doe@example.com',
          first_name: 'John',
          last_name: 'Doe',
        });
      }
      if (key === 'koroh_portfolios') {
        return JSON.stringify([]);
      }
      return null;
    });
  });

  it('generates correct URL structure with localhost', async () => {
    const response = await mockApi.profiles.generatePortfolio({
      portfolioName: 'my-awesome-portfolio',
      template: 'modern-pro'
    });

    const portfolio = response.data;
    
    expect(portfolio.url).toBe('http://localhost:3000/@john.doe/my-awesome-portfolio');
    expect(portfolio.username).toBe('john.doe');
    expect(portfolio.portfolioName).toBe('my-awesome-portfolio');
  });

  it('generates URL with auto-generated portfolio name when not provided', async () => {
    const response = await mockApi.profiles.generatePortfolio({
      template: 'modern-pro'
    });

    const portfolio = response.data;
    
    expect(portfolio.url).toBe('http://localhost:3000/@john.doe/john-doe-portfolio');
    expect(portfolio.username).toBe('john.doe');
    expect(portfolio.portfolioName).toBe('john-doe-portfolio');
  });

  it('generates username from email correctly', async () => {
    localStorageMock.getItem.mockImplementation((key) => {
      if (key === 'koroh_current_user') {
        return JSON.stringify({
          id: 'test-user-2',
          email: 'jane.smith@company.com',
          first_name: 'Jane',
          last_name: 'Smith',
        });
      }
      if (key === 'koroh_portfolios') {
        return JSON.stringify([]);
      }
      return null;
    });

    const response = await mockApi.profiles.generatePortfolio({
      portfolioName: 'professional-portfolio',
      template: 'classic-elegant'
    });

    const portfolio = response.data;
    
    expect(portfolio.url).toBe('http://localhost:3000/@jane.smith/professional-portfolio');
    expect(portfolio.username).toBe('jane.smith');
  });

  it('uses https for production domains', async () => {
    // Mock production domain
    Object.defineProperty(window, 'location', {
      value: {
        host: 'koroh.com',
        origin: 'https://koroh.com',
      },
      writable: true,
    });

    const response = await mockApi.profiles.generatePortfolio({
      portfolioName: 'production-portfolio',
      template: 'creative-bold'
    });

    const portfolio = response.data;
    
    expect(portfolio.url).toBe('https://koroh.com/@john.doe/production-portfolio');
  });

  it('handles special characters in portfolio name', async () => {
    const response = await mockApi.profiles.generatePortfolio({
      portfolioName: 'My Amazing Portfolio!!! 123',
      template: 'minimal-clean'
    });

    const portfolio = response.data;
    
    // The portfolio name should be sanitized in the component, but let's test the API accepts it
    expect(portfolio.portfolioName).toBe('My Amazing Portfolio!!! 123');
    expect(portfolio.url).toContain('@john.doe/My Amazing Portfolio!!! 123');
  });

  it('stores portfolio data correctly', async () => {
    const response = await mockApi.profiles.generatePortfolio({
      portfolioName: 'test-portfolio',
      template: 'modern-pro'
    });

    const portfolio = response.data;
    
    expect(portfolio).toMatchObject({
      userId: 'test-user-1',
      username: 'john.doe',
      portfolioName: 'test-portfolio',
      template: 'modern-pro',
      customizations: {
        theme: 'light',
        primaryColor: '#0d9488',
        font: 'inter',
        layout: 'standard',
      },
      content: {
        title: 'John Doe',
        subtitle: 'Professional Portfolio',
        bio: expect.any(String),
        skills: expect.any(Array),
        experience: expect.any(Array),
        education: expect.any(Array),
        projects: expect.any(Array),
      }
    });

    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'koroh_portfolios',
      expect.stringContaining(portfolio.id)
    );
  });

  it('retrieves existing portfolios correctly', async () => {
    const existingPortfolio = {
      id: 'existing-1',
      userId: 'test-user-1',
      username: 'john.doe',
      portfolioName: 'existing-portfolio',
      url: 'http://localhost:3000/@john.doe/existing-portfolio',
      template: 'modern-pro',
    };

    localStorageMock.getItem.mockImplementation((key) => {
      if (key === 'koroh_current_user') {
        return JSON.stringify({
          id: 'test-user-1',
          email: 'john.doe@example.com',
          first_name: 'John',
          last_name: 'Doe',
        });
      }
      if (key === 'koroh_portfolios') {
        return JSON.stringify([existingPortfolio]);
      }
      return null;
    });

    const response = await mockApi.profiles.getPortfolios();
    
    expect(response.data).toHaveLength(1);
    expect(response.data[0]).toMatchObject(existingPortfolio);
  });
});