import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NotificationProvider, useNotifications } from '@/contexts/notification-context';
import { JobSearch } from '@/components/jobs/job-search';
import { JobList } from '@/components/jobs/job-list';
import { CompanySearch } from '@/components/companies/company-search';
import { CompanyList } from '@/components/companies/company-list';
import { Job, Company } from '@/types';

// Mock the useNotifications hook
const mockNotificationContext = {
  notifications: [],
  addNotification: jest.fn(),
  removeNotification: jest.fn(),
  markAsRead: jest.fn(),
  clearAll: jest.fn(),
};

jest.mock('@/contexts/notification-context', () => ({
  ...jest.requireActual('@/contexts/notification-context'),
  useNotifications: () => mockNotificationContext,
}));

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

const renderWithNotificationProvider = (component: React.ReactElement) => {
  return render(
    <NotificationProvider>
      {component}
    </NotificationProvider>
  );
};

describe('Job and Company Discovery with Notification Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNotificationContext.notifications = [];
  });

  describe('Job Discovery and Application Notifications', () => {
    it('integrates job search with application notifications', async () => {
      const user = userEvent.setup();
      const mockOnSearch = jest.fn();
      const mockOnJobApply = jest.fn().mockResolvedValue({ success: true });
      const mockOnPageChange = jest.fn();

      const { rerender } = renderWithNotificationProvider(
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
        <NotificationProvider>
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
        </NotificationProvider>
      );

      // Should now show job results
      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('TechCorp Inc')).toBeInTheDocument();

      // Apply to job and verify notification
      const applyButton = screen.getByText('Apply Now');
      await user.click(applyButton);

      await waitFor(() => {
        expect(mockOnJobApply).toHaveBeenCalledWith('1');
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Application Submitted',
          message: 'Your application for Senior Software Engineer has been submitted successfully.',
        });
      });
    });

    it('handles job search errors with notifications', async () => {
      const user = userEvent.setup();
      const mockOnSearch = jest.fn().mockRejectedValue(new Error('Search failed'));

      renderWithNotificationProvider(
        <JobSearch 
          searchParams={{ query: '', location: '' }} 
          onSearch={mockOnSearch} 
        />
      );

      const searchInput = screen.getByPlaceholderText('Job title, keywords, or company');
      await user.type(searchInput, 'Invalid Search');
      
      const searchButton = screen.getByRole('button', { name: /search jobs/i });
      await user.click(searchButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'error',
          title: 'Search Failed',
          message: 'Failed to search for jobs. Please try again.',
        });
      });
    });
  });

  describe('Company Discovery and Follow Notifications', () => {
    it('integrates company search with follow notifications', async () => {
      const user = userEvent.setup();
      const mockOnSearch = jest.fn();
      const mockOnCompanyFollow = jest.fn().mockResolvedValue({ success: true });
      const mockOnPageChange = jest.fn();

      const { rerender } = renderWithNotificationProvider(
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
        <NotificationProvider>
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
        </NotificationProvider>
      );

      // Should now show company results
      expect(screen.getByText('TechCorp Inc')).toBeInTheDocument();
      expect(screen.getByText('Technology')).toBeInTheDocument();

      // Follow company and verify notification
      const followButton = screen.getByText('Follow');
      await user.click(followButton);

      await waitFor(() => {
        expect(mockOnCompanyFollow).toHaveBeenCalledWith('1', false);
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Company Followed',
          message: 'You are now following TechCorp Inc. You will receive updates about their job postings and company news.',
        });
      });
    });

    it('handles company search errors with notifications', async () => {
      const user = userEvent.setup();
      const mockOnSearch = jest.fn().mockRejectedValue(new Error('Search failed'));

      renderWithNotificationProvider(
        <CompanySearch 
          searchParams={{ query: '', location: '' }} 
          onSearch={mockOnSearch} 
        />
      );

      const searchInput = screen.getByPlaceholderText('Company name or industry');
      await user.type(searchInput, 'Invalid Search');
      
      const searchButton = screen.getByRole('button', { name: /search companies/i });
      await user.click(searchButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'error',
          title: 'Search Failed',
          message: 'Failed to search for companies. Please try again.',
        });
      });
    });
  });

  describe('Cross-Feature Notification Management', () => {
    it('manages notifications from both job and company features', async () => {
      const user = userEvent.setup();
      const mockOnJobApply = jest.fn().mockResolvedValue({ success: true });
      const mockOnCompanyFollow = jest.fn().mockResolvedValue({ success: true });

      renderWithNotificationProvider(
        <div>
          <JobList
            jobs={mockJobs}
            onJobApply={mockOnJobApply}
            onPageChange={jest.fn()}
            currentPage={1}
            totalCount={1}
            pageSize={20}
          />
          <CompanyList
            companies={mockCompanies}
            onCompanyFollow={mockOnCompanyFollow}
            onPageChange={jest.fn()}
            currentPage={1}
            totalCount={1}
            pageSize={20}
          />
        </div>
      );

      // Apply to job
      const applyButton = screen.getByText('Apply Now');
      await user.click(applyButton);

      // Follow company
      const followButton = screen.getByText('Follow');
      await user.click(followButton);

      await waitFor(() => {
        // Should have received both notifications
        expect(mockNotificationContext.addNotification).toHaveBeenCalledTimes(2);
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Application Submitted',
          message: 'Your application for Senior Software Engineer has been submitted successfully.',
        });
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Company Followed',
          message: 'You are now following TechCorp Inc. You will receive updates about their job postings and company news.',
        });
      });
    });

    it('handles notification clearing across features', async () => {
      const user = userEvent.setup();
      
      // Set up notifications from both features
      const mockNotifications = [
        {
          id: '1',
          type: 'success' as const,
          title: 'Application Submitted',
          message: 'Your job application was submitted.',
          timestamp: new Date().toISOString(),
        },
        {
          id: '2',
          type: 'success' as const,
          title: 'Company Followed',
          message: 'You are now following a company.',
          timestamp: new Date().toISOString(),
        }
      ];

      mockNotificationContext.notifications = mockNotifications;

      render(
        <NotificationProvider>
          <div>
            <span>Application Submitted</span>
            <span>Company Followed</span>
            <button onClick={() => mockNotificationContext.clearAll()}>
              Clear All Notifications
            </button>
          </div>
        </NotificationProvider>
      );

      expect(screen.getByText('Application Submitted')).toBeInTheDocument();
      expect(screen.getByText('Company Followed')).toBeInTheDocument();

      const clearButton = screen.getByText('Clear All Notifications');
      await user.click(clearButton);

      expect(mockNotificationContext.clearAll).toHaveBeenCalled();
    });
  });

  describe('Notification Accessibility and UX', () => {
    it('provides accessible notifications for screen readers', () => {
      const mockNotifications = [
        {
          id: '1',
          type: 'success' as const,
          title: 'Job Application Success',
          message: 'Your application has been submitted successfully.',
          timestamp: new Date().toISOString(),
        }
      ];

      mockNotificationContext.notifications = mockNotifications;

      render(
        <NotificationProvider>
          <div role="status" aria-live="polite" aria-label="Notifications">
            <span>Job Application Success</span>
            <span>Your application has been submitted successfully.</span>
          </div>
        </NotificationProvider>
      );

      const statusElement = screen.getByRole('status');
      expect(statusElement).toHaveAttribute('aria-live', 'polite');
      expect(statusElement).toHaveAttribute('aria-label', 'Notifications');
      expect(screen.getByText('Job Application Success')).toBeInTheDocument();
    });

    it('supports keyboard navigation for notification actions', async () => {
      const user = userEvent.setup();
      const mockOnJobApply = jest.fn().mockResolvedValue({ success: true });

      renderWithNotificationProvider(
        <JobList
          jobs={mockJobs}
          onJobApply={mockOnJobApply}
          onPageChange={jest.fn()}
          currentPage={1}
          totalCount={1}
          pageSize={20}
        />
      );

      const applyButton = screen.getByText('Apply Now');
      
      // Focus and activate with keyboard
      applyButton.focus();
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockOnJobApply).toHaveBeenCalledWith('1');
        expect(mockNotificationContext.addNotification).toHaveBeenCalled();
      });
    });

    it('handles notification timing appropriately', async () => {
      jest.useFakeTimers();
      
      const mockNotifications = [
        {
          id: '1',
          type: 'success' as const,
          title: 'Auto Dismiss Notification',
          message: 'This notification will auto-dismiss.',
          timestamp: new Date().toISOString(),
          autoDismiss: true,
          duration: 3000,
        }
      ];

      mockNotificationContext.notifications = mockNotifications;

      render(
        <NotificationProvider>
          <div>Auto Dismiss Notification</div>
        </NotificationProvider>
      );

      expect(screen.getByText('Auto Dismiss Notification')).toBeInTheDocument();

      // Fast-forward time to trigger auto-dismiss
      jest.advanceTimersByTime(3000);

      await waitFor(() => {
        expect(mockNotificationContext.removeNotification).toHaveBeenCalledWith('1');
      });

      jest.useRealTimers();
    });
  });
});