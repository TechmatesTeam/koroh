import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CompanySearch } from '@/components/companies/company-search';
import { CompanyList } from '@/components/companies/company-list';
import { CompanyCard } from '@/components/companies/company-card';
import { Company } from '@/types';

// Mock data
const mockCompanies: Company[] = [
  {
    id: '1',
    name: 'Tech Innovations Inc',
    description: 'Leading technology company focused on AI and machine learning solutions.',
    industry: 'technology',
    size: 'large',
    location: 'San Francisco, CA',
    website: 'https://techinnovations.com',
    logo: '/logos/tech-innovations.png',
    followers_count: 2500,
    is_following: false,
  },
  {
    id: '2',
    name: 'Green Energy Solutions',
    description: 'Sustainable energy company developing renewable energy technologies.',
    industry: 'energy',
    size: 'medium',
    location: 'Austin, TX',
    website: 'https://greenenergy.com',
    logo: '/logos/green-energy.png',
    followers_count: 1200,
    is_following: true,
  },
  {
    id: '3',
    name: 'FinTech Startup',
    description: 'Revolutionary financial technology startup disrupting traditional banking.',
    industry: 'finance',
    size: 'startup',
    location: 'New York, NY',
    website: 'https://fintech-startup.com',
    followers_count: 800,
    is_following: false,
  },
];

describe('Company Discovery Features', () => {
  describe('CompanySearch Component', () => {
    const mockOnSearch = jest.fn();
    const defaultSearchParams = {
      query: '',
      location: '',
      industry: '',
      size: '',
    };

    beforeEach(() => {
      mockOnSearch.mockClear();
    });

    it('renders company search form with input fields', () => {
      render(
        <CompanySearch searchParams={defaultSearchParams} onSearch={mockOnSearch} />
      );

      expect(screen.getByPlaceholderText('Company name or industry')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Location')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /search companies/i })).toBeInTheDocument();
    });

    it('handles company search form submission', async () => {
      const user = userEvent.setup();
      render(
        <CompanySearch searchParams={defaultSearchParams} onSearch={mockOnSearch} />
      );

      const queryInput = screen.getByPlaceholderText('Company name or industry');
      const locationInput = screen.getByPlaceholderText('Location');
      const submitButton = screen.getByRole('button', { name: /search companies/i });

      await user.type(queryInput, 'Technology');
      await user.type(locationInput, 'San Francisco');
      await user.click(submitButton);

      expect(mockOnSearch).toHaveBeenCalledWith({
        query: 'Technology',
        location: 'San Francisco',
      });
    });

    it('displays company search form structure', () => {
      render(
        <CompanySearch searchParams={defaultSearchParams} onSearch={mockOnSearch} />
      );

      // Test the component structure without relying on form role
      expect(screen.getByPlaceholderText('Company name or industry')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Location')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /search companies/i })).toBeInTheDocument();
    });

    it('updates search parameters correctly', () => {
      const searchParams = {
        query: 'Tech',
        location: 'California',
        industry: 'technology',
        size: 'large',
      };

      render(
        <CompanySearch searchParams={searchParams} onSearch={mockOnSearch} />
      );

      expect(screen.getByDisplayValue('Tech')).toBeInTheDocument();
      expect(screen.getByDisplayValue('California')).toBeInTheDocument();
    });
  });

  describe('CompanyList Component', () => {
    const mockOnCompanyFollow = jest.fn();
    const mockOnPageChange = jest.fn();

    beforeEach(() => {
      mockOnCompanyFollow.mockClear();
      mockOnPageChange.mockClear();
    });

    it('renders company cards in grid layout', () => {
      render(
        <CompanyList
          companies={mockCompanies}
          onCompanyFollow={mockOnCompanyFollow}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={3}
          pageSize={20}
        />
      );

      expect(screen.getByText('Tech Innovations Inc')).toBeInTheDocument();
      expect(screen.getByText('Green Energy Solutions')).toBeInTheDocument();
      expect(screen.getByText('FinTech Startup')).toBeInTheDocument();
    });

    it('displays empty state when no companies found', () => {
      render(
        <CompanyList
          companies={[]}
          onCompanyFollow={mockOnCompanyFollow}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={0}
          pageSize={20}
        />
      );

      expect(screen.getByText('No companies found')).toBeInTheDocument();
      expect(screen.getByText('Try adjusting your search criteria or filters to find more companies.')).toBeInTheDocument();
    });

    it('handles company follow/unfollow actions', async () => {
      const user = userEvent.setup();
      render(
        <CompanyList
          companies={mockCompanies}
          onCompanyFollow={mockOnCompanyFollow}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={3}
          pageSize={20}
        />
      );

      const followButtons = screen.getAllByText('Follow');
      await user.click(followButtons[0]);

      expect(mockOnCompanyFollow).toHaveBeenCalledWith('1', false);
    });

    it('shows pagination when enabled and multiple pages exist', () => {
      render(
        <CompanyList
          companies={mockCompanies}
          onCompanyFollow={mockOnCompanyFollow}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={50}
          pageSize={20}
          showPagination={true}
        />
      );

      // Check for pagination elements
      expect(screen.getAllByText('Next')[0]).toBeInTheDocument();
      expect(screen.getAllByText('Previous')[0]).toBeInTheDocument();
    });

    it('hides pagination when showPagination is false', () => {
      render(
        <CompanyList
          companies={mockCompanies}
          onCompanyFollow={mockOnCompanyFollow}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={50}
          pageSize={20}
          showPagination={false}
        />
      );

      expect(screen.queryByText('Showing 1 to 3 of 50 results')).not.toBeInTheDocument();
    });
  });

  describe('CompanyCard Component', () => {
    const mockOnFollow = jest.fn();

    beforeEach(() => {
      mockOnFollow.mockClear();
    });

    it('displays company information correctly', () => {
      render(
        <CompanyCard company={mockCompanies[0]} onFollow={mockOnFollow} />
      );

      expect(screen.getByText('Tech Innovations Inc')).toBeInTheDocument();
      expect(screen.getByText('Technology')).toBeInTheDocument();
      expect(screen.getByText('San Francisco, CA')).toBeInTheDocument();
      expect(screen.getByText('1001-5000 employees')).toBeInTheDocument();
      expect(screen.getByText('2500 followers')).toBeInTheDocument();
    });

    it('shows company logo when available', () => {
      render(
        <CompanyCard company={mockCompanies[0]} onFollow={mockOnFollow} />
      );

      const logo = screen.getByAltText('Tech Innovations Inc');
      expect(logo).toBeInTheDocument();
      expect(logo).toHaveAttribute('src', '/logos/tech-innovations.png');
    });

    it('shows company initial when logo not available', () => {
      const companyWithoutLogo = { ...mockCompanies[0], logo: undefined };
      render(
        <CompanyCard company={companyWithoutLogo} onFollow={mockOnFollow} />
      );

      expect(screen.getByText('T')).toBeInTheDocument();
    });

    it('displays correct follow/following state', () => {
      render(
        <CompanyCard company={mockCompanies[1]} onFollow={mockOnFollow} />
      );

      expect(screen.getByText('Following')).toBeInTheDocument();
    });

    it('handles follow button clicks', async () => {
      const user = userEvent.setup();
      render(
        <CompanyCard company={mockCompanies[0]} onFollow={mockOnFollow} />
      );

      const followButton = screen.getByText('Follow');
      await user.click(followButton);

      expect(mockOnFollow).toHaveBeenCalled();
    });

    it('displays company website link', () => {
      render(
        <CompanyCard company={mockCompanies[0]} onFollow={mockOnFollow} />
      );

      const websiteLink = screen.getByText('techinnovations.com');
      expect(websiteLink).toBeInTheDocument();
      expect(websiteLink).toHaveAttribute('href', 'https://techinnovations.com');
      expect(websiteLink).toHaveAttribute('target', '_blank');
    });

    it('shows appropriate company size labels', () => {
      render(
        <CompanyCard company={mockCompanies[2]} onFollow={mockOnFollow} />
      );

      expect(screen.getByText('1-50 employees')).toBeInTheDocument();
    });
  });

  describe('Company Tracking Features', () => {
    it('tracks follow state changes correctly', async () => {
      const user = userEvent.setup();
      const mockOnFollow = jest.fn();

      render(
        <CompanyCard company={mockCompanies[0]} onFollow={mockOnFollow} />
      );

      const followButton = screen.getByText('Follow');
      await user.click(followButton);

      expect(mockOnFollow).toHaveBeenCalledTimes(1);
    });

    it('shows loading state during follow action', async () => {
      const user = userEvent.setup();
      let resolveFollow: () => void;
      const mockOnFollow = jest.fn(() => new Promise<void>(resolve => {
        resolveFollow = resolve;
      }));

      render(
        <CompanyCard company={mockCompanies[0]} onFollow={mockOnFollow} />
      );

      const followButton = screen.getByText('Follow');
      await user.click(followButton);

      expect(screen.getByText('Loading...')).toBeInTheDocument();

      // Resolve the promise to complete the action
      resolveFollow!();
      await waitFor(() => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      });
    });

    it('shows loading state during follow action', async () => {
      const user = userEvent.setup();
      let resolveFollow: () => void;
      const mockOnFollow = jest.fn(() => new Promise<void>(resolve => {
        resolveFollow = resolve;
      }));

      render(
        <CompanyCard company={mockCompanies[0]} onFollow={mockOnFollow} />
      );

      const followButton = screen.getByText('Follow');
      await user.click(followButton);

      expect(screen.getByText('Loading...')).toBeInTheDocument();

      // Resolve the promise to complete the action
      resolveFollow!();
      await waitFor(() => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      });
    });
  });

  describe('Search and Filter Integration', () => {
    it('maintains search state across interactions', () => {
      const searchParams = {
        query: 'Technology',
        location: 'California',
        industry: 'tech',
        size: 'large',
      };

      const mockOnSearch = jest.fn();
      render(
        <CompanySearch searchParams={searchParams} onSearch={mockOnSearch} />
      );

      expect(screen.getByDisplayValue('Technology')).toBeInTheDocument();
      expect(screen.getByDisplayValue('California')).toBeInTheDocument();
    });

    it('handles empty search results appropriately', () => {
      const mockOnCompanyFollow = jest.fn();
      const mockOnPageChange = jest.fn();

      render(
        <CompanyList
          companies={[]}
          onCompanyFollow={mockOnCompanyFollow}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={0}
          pageSize={20}
        />
      );

      expect(screen.getByText('No companies found')).toBeInTheDocument();
    });
  });

  describe('Accessibility Features', () => {
    it('provides proper ARIA labels and roles', () => {
      const mockOnSearch = jest.fn();
      render(
        <CompanySearch searchParams={{}} onSearch={mockOnSearch} />
      );

      const searchButton = screen.getByRole('button', { name: /search companies/i });
      expect(searchButton).toHaveAttribute('type', 'submit');
      
      const queryInput = screen.getByPlaceholderText('Company name or industry');
      const locationInput = screen.getByPlaceholderText('Location');
      expect(queryInput).toBeInTheDocument();
      expect(locationInput).toBeInTheDocument();
    });

    it('supports keyboard navigation for company cards', async () => {
      const user = userEvent.setup();
      const mockOnFollow = jest.fn();

      render(
        <CompanyCard company={mockCompanies[0]} onFollow={mockOnFollow} />
      );

      const followButton = screen.getByText('Follow');
      followButton.focus();
      await user.keyboard('{Enter}');

      expect(mockOnFollow).toHaveBeenCalled();
    });

    it('provides descriptive alt text for company logos', () => {
      const mockOnFollow = jest.fn();
      render(
        <CompanyCard company={mockCompanies[0]} onFollow={mockOnFollow} />
      );

      const logo = screen.getByAltText('Tech Innovations Inc');
      expect(logo).toBeInTheDocument();
    });

    it('ensures proper color contrast for industry badges', () => {
      const mockOnFollow = jest.fn();
      render(
        <CompanyCard company={mockCompanies[0]} onFollow={mockOnFollow} />
      );

      const industryBadge = screen.getByText('Technology');
      expect(industryBadge).toHaveClass('bg-blue-100', 'text-blue-800');
    });
  });

  describe('Responsive Design', () => {
    it('adapts company grid layout for different screen sizes', () => {
      const mockOnCompanyFollow = jest.fn();
      const mockOnPageChange = jest.fn();

      render(
        <CompanyList
          companies={mockCompanies}
          onCompanyFollow={mockOnCompanyFollow}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={3}
          pageSize={20}
        />
      );

      const gridContainer = screen.getByText('Tech Innovations Inc').closest('.grid');
      expect(gridContainer).toHaveClass('grid-cols-1', 'md:grid-cols-2');
    });

    it('handles mobile pagination layout', () => {
      const mockOnCompanyFollow = jest.fn();
      const mockOnPageChange = jest.fn();

      render(
        <CompanyList
          companies={mockCompanies}
          onCompanyFollow={mockOnCompanyFollow}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={50}
          pageSize={20}
        />
      );

      // Mobile pagination should be present
      const mobileNext = screen.getAllByText('Next')[0];
      expect(mobileNext).toBeInTheDocument();
    });
  });
});