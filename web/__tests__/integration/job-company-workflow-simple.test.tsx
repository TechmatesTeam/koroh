import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { JobSearch } from '@/components/jobs/job-search';
import { JobList } from '@/components/jobs/job-list';
import { CompanySearch } from '@/components/companies/company-search';
import { CompanyList } from '@/components/companies/company-list';
import { Job, Company } from '@/types';

// Mock data for integration testing
const mockJobs: Job[] = [
  {
    id: '1',
    title: 'Senior Software Engineer',
    company: {
      id: '1',
      name: 'TechCorp Inc',
      description: 'Leading technology company',
      industry: 'technology',
      size: 'large',
      location: 'San Francisco, CA',
      website: 'https://techcorp.com',
      logo: '/logos/techcorp.png',
      followers_count: 2500,
      is_following: false,
    },
    description: 'We are seeking a senior software engineer to join our innovative team.',
    requirements: ['React', 'TypeScript', 'Node.js'],
    location: 'San Francisco, CA',
    salary_range: '$130,000 - $180,000',
    job_type: 'full-time',
    posted_date: '2024-01-15T10:00:00Z',
    is_active: true,
  },
];

const mockCompanies: Company[] = [
  {
    id: '1',
    name: 'TechCorp Inc',
    description: 'Leading technology company specializing in AI and machine learning.',
    industry: 'technology',
    size: 'large',
    location: 'San Francisco, CA',
    website: 'https://techcorp.com',
    logo: '/logos/techcorp.png',
    followers_count: 2500,
    is_following: false,
  },
];

describe('Job and Company Discovery Workflow Integration', () => {
  describe('Job Search and Display Workflow', () => {
    it('integrates job search with job list display', async () => {
      const user = userEvent.setup();
      const mockOnSearch = jest.fn();
      const mockOnJobApply = jest.fn();
      const mockOnPageChange = jest.fn();

      const { rerender } = render(
        <div>
          <JobSearch 
            searchParams={{ query: '', location: '' }} 
            onSearch={mockOnSearch} 
          />
          <JobList
            jobs={[]}
            onJobApply={mockOnJobApply}
            onPageChange={mockOnPageChange}
            currentPage={1}
            totalCount={0}
            pageSize={20}
          />
        </div>
      );

      // Initially shows empty state
      expect(screen.getByText('No jobs found')).toBeInTheDocument();

      // Perform search
      const searchInput = screen.getByPlaceholderText('Job title, keywords, or company');
      await user.type(searchInput, 'Software Engineer');
      
      const searchButton = screen.getByRole('button', { name: /search jobs/i });
      await user.click(searchButton);

      expect(mockOnSearch).toHaveBeenCalledWith({
        query: 'Software Engineer',
        location: '',
      });

      // Simulate search results by re-rendering with jobs
      rerender(
        <div>
          <JobSearch 
            searchParams={{ query: 'Software Engineer', location: '' }} 
            onSearch={mockOnSearch} 
          />
          <JobList
            jobs={mockJobs}
            onJobApply={mockOnJobApply}
            onPageChange={mockOnPageChange}
            currentPage={1}
            totalCount={1}
            pageSize={20}
          />
        </div>
      );

      // Should now show job results
      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('TechCorp Inc')).toBeInTheDocument();
    });

    it('handles job application from search results', async () => {
      const user = userEvent.setup();
      const mockOnJobApply = jest.fn();
      const mockOnPageChange = jest.fn();

      render(
        <JobList
          jobs={mockJobs}
          onJobApply={mockOnJobApply}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={1}
          pageSize={20}
        />
      );

      const applyButton = screen.getByText('Apply Now');
      await user.click(applyButton);

      expect(mockOnJobApply).toHaveBeenCalledWith('1');
    });
  });

  describe('Company Search and Discovery Workflow', () => {
    it('integrates company search with company list display', async () => {
      const user = userEvent.setup();
      const mockOnSearch = jest.fn();
      const mockOnCompanyFollow = jest.fn();
      const mockOnPageChange = jest.fn();

      const { rerender } = render(
        <div>
          <CompanySearch 
            searchParams={{ query: '', location: '' }} 
            onSearch={mockOnSearch} 
          />
          <CompanyList
            companies={[]}
            onCompanyFollow={mockOnCompanyFollow}
            onPageChange={mockOnPageChange}
            currentPage={1}
            totalCount={0}
            pageSize={20}
          />
        </div>
      );

      // Initially shows empty state
      expect(screen.getByText('No companies found')).toBeInTheDocument();

      // Perform search
      const searchInput = screen.getByPlaceholderText('Company name or industry');
      await user.type(searchInput, 'Technology');
      
      const searchButton = screen.getByRole('button', { name: /search companies/i });
      await user.click(searchButton);

      expect(mockOnSearch).toHaveBeenCalledWith({
        query: 'Technology',
        location: '',
      });

      // Simulate search results by re-rendering with companies
      rerender(
        <div>
          <CompanySearch 
            searchParams={{ query: 'Technology', location: '' }} 
            onSearch={mockOnSearch} 
          />
          <CompanyList
            companies={mockCompanies}
            onCompanyFollow={mockOnCompanyFollow}
            onPageChange={mockOnPageChange}
            currentPage={1}
            totalCount={1}
            pageSize={20}
          />
        </div>
      );

      // Should now show company results
      expect(screen.getByText('TechCorp Inc')).toBeInTheDocument();
      expect(screen.getByText('Technology')).toBeInTheDocument();
    });

    it('handles company follow action from search results', async () => {
      const user = userEvent.setup();
      const mockOnCompanyFollow = jest.fn();
      const mockOnPageChange = jest.fn();

      render(
        <CompanyList
          companies={mockCompanies}
          onCompanyFollow={mockOnCompanyFollow}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={1}
          pageSize={20}
        />
      );

      const followButton = screen.getByText('Follow');
      await user.click(followButton);

      expect(mockOnCompanyFollow).toHaveBeenCalledWith('1', false);
    });
  });

  describe('Cross-Feature Data Consistency', () => {
    it('maintains consistent company information between job and company views', () => {
      const mockOnJobApply = jest.fn();
      const mockOnPageChange = jest.fn();
      const mockOnCompanyFollow = jest.fn();

      const { rerender } = render(
        <JobList
          jobs={mockJobs}
          onJobApply={mockOnJobApply}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={1}
          pageSize={20}
        />
      );

      // Company info in job listing
      expect(screen.getByText('TechCorp Inc')).toBeInTheDocument();

      // Switch to company view
      rerender(
        <CompanyList
          companies={mockCompanies}
          onCompanyFollow={mockOnCompanyFollow}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={1}
          pageSize={20}
        />
      );

      // Same company info should be consistent
      expect(screen.getByText('TechCorp Inc')).toBeInTheDocument();
      expect(screen.getByText('2500 followers')).toBeInTheDocument();
    });

    it('handles search state management across components', async () => {
      const user = userEvent.setup();
      const mockOnSearch = jest.fn();

      render(
        <JobSearch 
          searchParams={{ query: 'Engineer', location: 'California' }} 
          onSearch={mockOnSearch} 
        />
      );

      // Should maintain search state
      expect(screen.getByDisplayValue('Engineer')).toBeInTheDocument();
      expect(screen.getByDisplayValue('California')).toBeInTheDocument();

      // Modify search
      const locationInput = screen.getByDisplayValue('California');
      await user.clear(locationInput);
      await user.type(locationInput, 'New York');

      const searchButton = screen.getByRole('button', { name: /search jobs/i });
      await user.click(searchButton);

      expect(mockOnSearch).toHaveBeenCalledWith({
        query: 'Engineer',
        location: 'New York',
      });
    });
  });

  describe('User Experience Flow', () => {
    it('provides smooth transition from search to results to actions', async () => {
      const user = userEvent.setup();
      const mockOnSearch = jest.fn();
      const mockOnJobApply = jest.fn();
      const mockOnPageChange = jest.fn();

      const { rerender } = render(
        <div>
          <JobSearch 
            searchParams={{ query: '', location: '' }} 
            onSearch={mockOnSearch} 
          />
          <JobList
            jobs={[]}
            onJobApply={mockOnJobApply}
            onPageChange={mockOnPageChange}
            currentPage={1}
            totalCount={0}
            pageSize={20}
          />
        </div>
      );

      // Step 1: Search
      const searchInput = screen.getByPlaceholderText('Job title, keywords, or company');
      await user.type(searchInput, 'Developer');
      
      const searchButton = screen.getByRole('button', { name: /search jobs/i });
      await user.click(searchButton);

      // Step 2: Results appear
      rerender(
        <div>
          <JobSearch 
            searchParams={{ query: 'Developer', location: '' }} 
            onSearch={mockOnSearch} 
          />
          <JobList
            jobs={mockJobs}
            onJobApply={mockOnJobApply}
            onPageChange={mockOnPageChange}
            currentPage={1}
            totalCount={1}
            pageSize={20}
          />
        </div>
      );

      // Step 3: User can interact with results
      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
      
      const applyButton = screen.getByText('Apply Now');
      await user.click(applyButton);

      expect(mockOnJobApply).toHaveBeenCalledWith('1');
    });

    it('maintains component state during interactions', async () => {
      const user = userEvent.setup();
      const mockOnCompanyFollow = jest.fn();
      const mockOnPageChange = jest.fn();

      render(
        <CompanyList
          companies={mockCompanies}
          onCompanyFollow={mockOnCompanyFollow}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={1}
          pageSize={20}
        />
      );

      const followButton = screen.getByText('Follow');
      
      // Should handle interaction successfully
      await user.click(followButton);
      
      // Component should still be functional
      expect(screen.getByText('TechCorp Inc')).toBeInTheDocument();
      expect(mockOnCompanyFollow).toHaveBeenCalledWith('1', false);
    });
  });

  describe('Accessibility and Usability', () => {
    it('supports keyboard navigation across search and results', async () => {
      const user = userEvent.setup();
      const mockOnSearch = jest.fn();

      render(
        <JobSearch 
          searchParams={{ query: '', location: '' }} 
          onSearch={mockOnSearch} 
        />
      );

      const searchInput = screen.getByPlaceholderText('Job title, keywords, or company');
      
      // Tab navigation
      await user.tab();
      expect(searchInput).toHaveFocus();

      // Type and submit with Enter
      await user.type(searchInput, 'Engineer');
      await user.keyboard('{Tab}'); // Move to location input
      await user.keyboard('{Tab}'); // Move to submit button
      await user.keyboard('{Enter}');

      expect(mockOnSearch).toHaveBeenCalledWith({
        query: 'Engineer',
        location: '',
      });
    });

    it('provides clear visual feedback for user actions', async () => {
      const user = userEvent.setup();
      const mockOnJobApply = jest.fn();
      const mockOnPageChange = jest.fn();

      render(
        <JobList
          jobs={mockJobs}
          onJobApply={mockOnJobApply}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={1}
          pageSize={20}
        />
      );

      // Job card should be visible and interactive
      const jobCard = screen.getByText('Senior Software Engineer').closest('.rounded-lg');
      expect(jobCard).toHaveClass('hover:shadow-md');

      // Apply button should be clearly labeled
      const applyButton = screen.getByText('Apply Now');
      expect(applyButton).toBeInTheDocument();
      
      await user.click(applyButton);
      expect(mockOnJobApply).toHaveBeenCalled();
    });
  });
});