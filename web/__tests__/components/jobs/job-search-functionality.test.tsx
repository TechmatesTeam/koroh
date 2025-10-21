import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { JobSearch } from '@/components/jobs/job-search';
import { JobList } from '@/components/jobs/job-list';
import { JobRecommendations } from '@/components/jobs/job-recommendations';
import { Job, JobSearchParams } from '@/types';

// Mock data
const mockJobs: Job[] = [
  {
    id: '1',
    title: 'Senior Software Engineer',
    company: {
      id: '1',
      name: 'Tech Corp',
      description: 'Leading tech company',
      industry: 'technology',
      size: 'large',
      location: 'San Francisco, CA',
      website: 'https://techcorp.com',
      logo: '/logos/techcorp.png',
      followers_count: 1500,
      is_following: false,
    },
    description: 'We are looking for a senior software engineer to join our team.',
    requirements: ['React', 'TypeScript', 'Node.js'],
    location: 'San Francisco, CA',
    salary_range: '$120,000 - $180,000',
    job_type: 'full-time',
    posted_date: '2024-01-15T10:00:00Z',
    is_active: true,
  },
  {
    id: '2',
    title: 'Product Manager',
    company: {
      id: '2',
      name: 'Innovation Inc',
      description: 'Innovative product company',
      industry: 'technology',
      size: 'medium',
      location: 'New York, NY',
      website: 'https://innovation.com',
      followers_count: 800,
      is_following: true,
    },
    description: 'Lead product development and strategy.',
    requirements: ['Product Management', 'Analytics', 'Leadership'],
    location: 'New York, NY',
    salary_range: '$100,000 - $150,000',
    job_type: 'full-time',
    posted_date: '2024-01-14T09:00:00Z',
    is_active: true,
  },
];

describe('Job Search Functionality', () => {
  describe('JobSearch Component', () => {
    const mockOnSearch = jest.fn();
    const defaultSearchParams: JobSearchParams = {
      query: '',
      location: '',
      job_type: '',
      page: 1,
      limit: 20,
    };

    beforeEach(() => {
      mockOnSearch.mockClear();
    });

    it('renders search form with input fields', () => {
      render(
        <JobSearch searchParams={defaultSearchParams} onSearch={mockOnSearch} />
      );

      expect(screen.getByPlaceholderText('Job title, keywords, or company')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('City, state, or remote')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /search jobs/i })).toBeInTheDocument();
    });

    it('handles form submission with search parameters', async () => {
      const user = userEvent.setup();
      render(
        <JobSearch searchParams={defaultSearchParams} onSearch={mockOnSearch} />
      );

      const queryInput = screen.getByPlaceholderText('Job title, keywords, or company');
      const locationInput = screen.getByPlaceholderText('City, state, or remote');
      const submitButton = screen.getByRole('button', { name: /search jobs/i });

      await user.type(queryInput, 'Software Engineer');
      await user.type(locationInput, 'San Francisco');
      await user.click(submitButton);

      expect(mockOnSearch).toHaveBeenCalledWith({
        query: 'Software Engineer',
        location: 'San Francisco',
      });
    });

    it('displays popular search suggestions', () => {
      render(
        <JobSearch searchParams={defaultSearchParams} onSearch={mockOnSearch} />
      );

      expect(screen.getByText('Popular searches:')).toBeInTheDocument();
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('Product Manager')).toBeInTheDocument();
      expect(screen.getByText('Data Scientist')).toBeInTheDocument();
    });

    it('handles quick search from popular suggestions', async () => {
      const user = userEvent.setup();
      render(
        <JobSearch searchParams={defaultSearchParams} onSearch={mockOnSearch} />
      );

      const popularSearch = screen.getByText('Software Engineer');
      await user.click(popularSearch);

      expect(mockOnSearch).toHaveBeenCalledWith({
        query: 'Software Engineer',
        location: '',
      });
    });

    it('updates input values when searchParams change', () => {
      const searchParams = {
        query: 'Developer',
        location: 'Remote',
        job_type: 'full-time',
        page: 1,
        limit: 20,
      };

      render(
        <JobSearch searchParams={searchParams} onSearch={mockOnSearch} />
      );

      const queryInput = screen.getByDisplayValue('Developer');
      const locationInput = screen.getByDisplayValue('Remote');

      expect(queryInput).toBeInTheDocument();
      expect(locationInput).toBeInTheDocument();
    });
  });

  describe('JobList Component', () => {
    const mockOnJobApply = jest.fn();
    const mockOnPageChange = jest.fn();

    beforeEach(() => {
      mockOnJobApply.mockClear();
      mockOnPageChange.mockClear();
    });

    it('renders job cards for each job', () => {
      render(
        <JobList
          jobs={mockJobs}
          onJobApply={mockOnJobApply}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={2}
          pageSize={20}
        />
      );

      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('Product Manager')).toBeInTheDocument();
      expect(screen.getByText('Tech Corp')).toBeInTheDocument();
      expect(screen.getByText('Innovation Inc')).toBeInTheDocument();
    });

    it('displays empty state when no jobs found', () => {
      render(
        <JobList
          jobs={[]}
          onJobApply={mockOnJobApply}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={0}
          pageSize={20}
        />
      );

      expect(screen.getByText('No jobs found')).toBeInTheDocument();
      expect(screen.getByText('Try adjusting your search criteria or filters to find more opportunities.')).toBeInTheDocument();
    });

    it('handles job application clicks', async () => {
      const user = userEvent.setup();
      render(
        <JobList
          jobs={mockJobs}
          onJobApply={mockOnJobApply}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={2}
          pageSize={20}
        />
      );

      const applyButtons = screen.getAllByText('Apply Now');
      await user.click(applyButtons[0]);

      expect(mockOnJobApply).toHaveBeenCalledWith('1');
    });

    it('displays pagination when multiple pages exist', () => {
      render(
        <JobList
          jobs={mockJobs}
          onJobApply={mockOnJobApply}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={50}
          pageSize={20}
        />
      );

      // Check for pagination elements
      expect(screen.getAllByText('Next')[0]).toBeInTheDocument();
      expect(screen.getAllByText('Previous')[0]).toBeInTheDocument();
    });

    it('handles pagination navigation', async () => {
      const user = userEvent.setup();
      render(
        <JobList
          jobs={mockJobs}
          onJobApply={mockOnJobApply}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={50}
          pageSize={20}
        />
      );

      const nextButtons = screen.getAllByText('Next');
      await user.click(nextButtons[0]);

      expect(mockOnPageChange).toHaveBeenCalledWith(2);
    });
  });

  describe('JobRecommendations Component', () => {
    const mockOnJobApply = jest.fn();

    beforeEach(() => {
      mockOnJobApply.mockClear();
    });

    it('displays AI recommendations with match scores', () => {
      render(
        <JobRecommendations jobs={mockJobs} onJobApply={mockOnJobApply} />
      );

      expect(screen.getByText('AI Recommendations')).toBeInTheDocument();
      expect(screen.getAllByText('95% Match')).toHaveLength(2);
      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('Product Manager')).toBeInTheDocument();
    });

    it('shows empty state when no recommendations available', () => {
      render(
        <JobRecommendations jobs={[]} onJobApply={mockOnJobApply} />
      );

      expect(screen.getByText('No recommendations yet')).toBeInTheDocument();
      expect(screen.getByText('Complete your profile to get personalized job recommendations.')).toBeInTheDocument();
    });

    it('limits display to 5 recommendations', () => {
      const manyJobs = Array.from({ length: 10 }, (_, i) => ({
        ...mockJobs[0],
        id: `job-${i}`,
        title: `Job ${i}`,
      }));

      render(
        <JobRecommendations jobs={manyJobs} onJobApply={mockOnJobApply} />
      );

      const jobTitles = screen.getAllByText(/Job \d/);
      expect(jobTitles).toHaveLength(5);
    });

    it('shows view all button when more than 5 recommendations', () => {
      const manyJobs = Array.from({ length: 10 }, (_, i) => ({
        ...mockJobs[0],
        id: `job-${i}`,
        title: `Job ${i}`,
      }));

      render(
        <JobRecommendations jobs={manyJobs} onJobApply={mockOnJobApply} />
      );

      expect(screen.getByText('View All Recommendations (10)')).toBeInTheDocument();
    });

    it('handles apply button clicks in recommendations', async () => {
      const user = userEvent.setup();
      render(
        <JobRecommendations jobs={mockJobs} onJobApply={mockOnJobApply} />
      );

      const applyButtons = screen.getAllByText('Apply');
      await user.click(applyButtons[0]);

      expect(mockOnJobApply).toHaveBeenCalledWith('1');
    });
  });

  describe('Search Integration', () => {
    it('maintains search state across components', () => {
      const searchParams: JobSearchParams = {
        query: 'Engineer',
        location: 'California',
        job_type: 'full-time',
        page: 2,
        limit: 10,
      };

      const mockOnSearch = jest.fn();
      render(
        <JobSearch searchParams={searchParams} onSearch={mockOnSearch} />
      );

      expect(screen.getByDisplayValue('Engineer')).toBeInTheDocument();
      expect(screen.getByDisplayValue('California')).toBeInTheDocument();
    });

    it('resets page to 1 on new search', async () => {
      const user = userEvent.setup();
      const mockOnSearch = jest.fn();
      const searchParams: JobSearchParams = {
        query: '',
        location: '',
        page: 5,
        limit: 20,
      };

      render(
        <JobSearch searchParams={searchParams} onSearch={mockOnSearch} />
      );

      const queryInput = screen.getByPlaceholderText('Job title, keywords, or company');
      const submitButton = screen.getByRole('button', { name: /search jobs/i });

      await user.type(queryInput, 'New Search');
      await user.click(submitButton);

      expect(mockOnSearch).toHaveBeenCalledWith({
        query: 'New Search',
        location: '',
      });
    });
  });

  describe('Accessibility', () => {
    it('provides proper form labels and ARIA attributes', () => {
      const mockOnSearch = jest.fn();
      render(
        <JobSearch searchParams={{}} onSearch={mockOnSearch} />
      );

      const searchButton = screen.getByRole('button', { name: /search jobs/i });
      expect(searchButton).toHaveAttribute('type', 'submit');
      
      const queryInput = screen.getByPlaceholderText('Job title, keywords, or company');
      const locationInput = screen.getByPlaceholderText('City, state, or remote');
      expect(queryInput).toBeInTheDocument();
      expect(locationInput).toBeInTheDocument();
    });

    it('supports keyboard navigation for popular searches', async () => {
      const user = userEvent.setup();
      const mockOnSearch = jest.fn();
      render(
        <JobSearch searchParams={{}} onSearch={mockOnSearch} />
      );

      const popularSearch = screen.getByText('Software Engineer');
      popularSearch.focus();
      await user.keyboard('{Enter}');

      expect(mockOnSearch).toHaveBeenCalledWith({
        query: 'Software Engineer',
        location: '',
      });
    });

    it('provides screen reader friendly pagination', () => {
      const mockOnJobApply = jest.fn();
      const mockOnPageChange = jest.fn();

      render(
        <JobList
          jobs={mockJobs}
          onJobApply={mockOnJobApply}
          onPageChange={mockOnPageChange}
          currentPage={1}
          totalCount={50}
          pageSize={20}
        />
      );

      const pagination = screen.getByLabelText('Pagination');
      expect(pagination).toBeInTheDocument();

      // Check for screen reader text within pagination
      const srOnlyElements = screen.getAllByText('Previous');
      expect(srOnlyElements.length).toBeGreaterThan(0);
    });
  });
});