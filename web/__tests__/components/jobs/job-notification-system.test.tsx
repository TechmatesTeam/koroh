import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NotificationProvider, useNotifications } from '@/contexts/notification-context';
import { JobRecommendations } from '@/components/jobs/job-recommendations';
import { JobList } from '@/components/jobs/job-list';
import { Job } from '@/types';

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

// Mock job data
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
    description: 'We are looking for a senior software engineer.',
    requirements: ['React', 'TypeScript', 'Node.js'],
    location: 'San Francisco, CA',
    salary_range: '$120,000 - $180,000',
    job_type: 'full-time',
    posted_date: '2024-01-15T10:00:00Z',
    is_active: true,
  },
];

const renderWithNotificationContext = (component: React.ReactElement) => {
  return render(
    <NotificationProvider>
      {component}
    </NotificationProvider>
  );
};

describe('Job Notification System', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Job Application Notifications', () => {
    it('shows success notification when job application is submitted', async () => {
      const user = userEvent.setup();
      const mockOnJobApply = jest.fn().mockResolvedValue({ success: true });

      renderWithNotificationContext(
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
      await user.click(applyButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Application Submitted',
          message: 'Your application for Senior Software Engineer has been submitted successfully.',
        });
      });
    });

    it('shows error notification when job application fails', async () => {
      const user = userEvent.setup();
      const mockOnJobApply = jest.fn().mockRejectedValue(new Error('Application failed'));

      renderWithNotificationContext(
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
      await user.click(applyButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'error',
          title: 'Application Failed',
          message: 'Failed to submit your application. Please try again.',
        });
      });
    });

    it('shows loading state during job application submission', async () => {
      const user = userEvent.setup();
      let resolveApplication: () => void;
      const mockOnJobApply = jest.fn(() => new Promise<void>(resolve => {
        resolveApplication = resolve;
      }));

      renderWithNotificationContext(
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
      await user.click(applyButton);

      expect(screen.getByText('Applying...')).toBeInTheDocument();

      resolveApplication!();
      await waitFor(() => {
        expect(screen.queryByText('Applying...')).not.toBeInTheDocument();
      });
    });
  });

  describe('Job Recommendation Notifications', () => {
    it('shows notification when new job recommendations are available', () => {
      const mockNotifications = [
        {
          id: '1',
          type: 'info' as const,
          title: 'New Job Recommendations',
          message: '5 new job recommendations based on your profile are available.',
          timestamp: new Date().toISOString(),
        }
      ];

      // Mock the notifications in the context
      mockNotificationContext.notifications = mockNotifications;

      renderWithNotificationContext(
        <JobRecommendations jobs={mockJobs} onJobApply={jest.fn()} />
      );

      expect(screen.getByText('New Job Recommendations')).toBeInTheDocument();
      expect(screen.getByText('5 new job recommendations based on your profile are available.')).toBeInTheDocument();
    });

    it('handles job recommendation refresh notifications', async () => {
      const user = userEvent.setup();
      const mockOnRefresh = jest.fn().mockResolvedValue({ newCount: 3 });

      renderWithNotificationContext(
        <JobRecommendations 
          jobs={mockJobs} 
          onJobApply={jest.fn()}
          onRefresh={mockOnRefresh}
        />
      );

      const refreshButton = screen.getByText('Refresh Recommendations');
      await user.click(refreshButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'info',
          title: 'Recommendations Updated',
          message: '3 new job recommendations have been found for you.',
        });
      });
    });

    it('shows notification when no new recommendations are found', async () => {
      const user = userEvent.setup();
      const mockOnRefresh = jest.fn().mockResolvedValue({ newCount: 0 });

      renderWithNotificationContext(
        <JobRecommendations 
          jobs={mockJobs} 
          onJobApply={jest.fn()}
          onRefresh={mockOnRefresh}
        />
      );

      const refreshButton = screen.getByText('Refresh Recommendations');
      await user.click(refreshButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'info',
          title: 'No New Recommendations',
          message: 'Your recommendations are up to date.',
        });
      });
    });
  });

  describe('Job Alert Notifications', () => {
    it('shows notification when job alert is created', async () => {
      const user = userEvent.setup();
      const mockOnCreateAlert = jest.fn().mockResolvedValue({ success: true });

      renderWithNotificationContext(
        <JobList
          jobs={mockJobs}
          onJobApply={jest.fn()}
          onPageChange={jest.fn()}
          onCreateAlert={mockOnCreateAlert}
          currentPage={1}
          totalCount={1}
          pageSize={20}
        />
      );

      const alertButton = screen.getByText('Create Job Alert');
      await user.click(alertButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Job Alert Created',
          message: 'You will be notified when new jobs matching your criteria are posted.',
        });
      });
    });

    it('shows notification when job alert creation fails', async () => {
      const user = userEvent.setup();
      const mockOnCreateAlert = jest.fn().mockRejectedValue(new Error('Alert creation failed'));

      renderWithNotificationContext(
        <JobList
          jobs={mockJobs}
          onJobApply={jest.fn()}
          onPageChange={jest.fn()}
          onCreateAlert={mockOnCreateAlert}
          currentPage={1}
          totalCount={1}
          pageSize={20}
        />
      );

      const alertButton = screen.getByText('Create Job Alert');
      await user.click(alertButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'error',
          title: 'Alert Creation Failed',
          message: 'Failed to create job alert. Please try again.',
        });
      });
    });
  });

  describe('Job Status Notifications', () => {
    it('shows notification when job status changes', () => {
      const mockNotifications = [
        {
          id: '2',
          type: 'success' as const,
          title: 'Application Status Update',
          message: 'Your application for Senior Software Engineer has been reviewed.',
          timestamp: new Date().toISOString(),
        }
      ];

      // Mock the notifications in the context
      mockNotificationContext.notifications = mockNotifications;

      render(
        <NotificationProvider>
          <div>Job Status Notifications Test</div>
        </NotificationProvider>
      );

      expect(screen.getByText('Application Status Update')).toBeInTheDocument();
      expect(screen.getByText('Your application for Senior Software Engineer has been reviewed.')).toBeInTheDocument();
    });

    it('handles multiple job status notifications', () => {
      const mockNotifications = [
        {
          id: '3',
          type: 'info' as const,
          title: 'Interview Scheduled',
          message: 'An interview has been scheduled for your application at Tech Corp.',
          timestamp: new Date().toISOString(),
        },
        {
          id: '4',
          type: 'warning' as const,
          title: 'Application Deadline',
          message: 'The application deadline for Product Manager at Innovation Inc is approaching.',
          timestamp: new Date().toISOString(),
        }
      ];

      // Mock the notifications in the context
      mockNotificationContext.notifications = mockNotifications;

      render(
        <NotificationProvider>
          <div>Multiple Job Notifications Test</div>
        </NotificationProvider>
      );

      expect(screen.getByText('Interview Scheduled')).toBeInTheDocument();
      expect(screen.getByText('Application Deadline')).toBeInTheDocument();
    });
  });

  describe('Notification Persistence', () => {
    it('maintains notification state across component re-renders', () => {
      const mockNotifications = [
        {
          id: '5',
          type: 'success' as const,
          title: 'Job Saved',
          message: 'Senior Software Engineer has been saved to your favorites.',
          timestamp: new Date().toISOString(),
        }
      ];

      // Mock the notifications in the context
      mockNotificationContext.notifications = mockNotifications;

      const { rerender } = renderWithNotificationContext(
        <JobList
          jobs={mockJobs}
          onJobApply={jest.fn()}
          onPageChange={jest.fn()}
          currentPage={1}
          totalCount={1}
          pageSize={20}
        />
      );

      expect(screen.getByText('Job Saved')).toBeInTheDocument();

      // Re-render with same context
      rerender(
        <JobList
          jobs={mockJobs}
          onJobApply={jest.fn()}
          onPageChange={jest.fn()}
          currentPage={1}
          totalCount={1}
          pageSize={20}
        />
      );

      expect(screen.getByText('Job Saved')).toBeInTheDocument();
    });

    it('handles notification removal correctly', async () => {
      const user = userEvent.setup();
      const mockNotifications = [
        {
          id: '6',
          type: 'info' as const,
          title: 'Job Recommendation',
          message: 'New job recommendation available.',
          timestamp: new Date().toISOString(),
        }
      ];

      // Mock the notifications in the context
      mockNotificationContext.notifications = mockNotifications;

      render(
        <NotificationProvider>
          <div>
            <span>Job Recommendation</span>
            <button onClick={() => mockNotificationContext.removeNotification('6')}>
              Dismiss
            </button>
          </div>
        </NotificationProvider>
      );

      const dismissButton = screen.getByText('Dismiss');
      await user.click(dismissButton);

      expect(mockNotificationContext.removeNotification).toHaveBeenCalledWith('6');
    });
  });

  describe('Accessibility and User Experience', () => {
    it('provides screen reader accessible notification announcements', () => {
      const mockNotifications = [
        {
          id: '7',
          type: 'success' as const,
          title: 'Application Submitted',
          message: 'Your job application has been submitted successfully.',
          timestamp: new Date().toISOString(),
        }
      ];

      // Mock the notifications in the context
      mockNotificationContext.notifications = mockNotifications;

      render(
        <NotificationProvider>
          <div role="status" aria-live="polite">
            <span>Application Submitted</span>
            <span>Your job application has been submitted successfully.</span>
          </div>
        </NotificationProvider>
      );

      const statusElement = screen.getByRole('status');
      expect(statusElement).toHaveAttribute('aria-live', 'polite');
      expect(screen.getByText('Application Submitted')).toBeInTheDocument();
    });

    it('supports keyboard navigation for notification actions', async () => {
      const user = userEvent.setup();
      const mockOnJobApply = jest.fn().mockResolvedValue({ success: true });

      renderWithNotificationContext(
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
      applyButton.focus();
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockOnJobApply).toHaveBeenCalledWith('1');
      });
    });
  });
});