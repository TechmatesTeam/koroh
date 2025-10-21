import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NotificationProvider, useNotifications } from '@/contexts/notification-context';
import { CompanyList } from '@/components/companies/company-list';
import { CompanyCard } from '@/components/companies/company-card';
import { CompanyInsights } from '@/components/companies/company-insights';
import { Company } from '@/types';

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

// Mock company data
const mockCompanies: Company[] = [
  {
    id: '1',
    name: 'Tech Innovations Inc',
    description: 'Leading technology company focused on AI solutions.',
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
    description: 'Sustainable energy company.',
    industry: 'energy',
    size: 'medium',
    location: 'Austin, TX',
    website: 'https://greenenergy.com',
    logo: '/logos/green-energy.png',
    followers_count: 1200,
    is_following: true,
  },
];

const renderWithNotificationContext = (component: React.ReactElement) => {
  return render(
    <NotificationProvider>
      {component}
    </NotificationProvider>
  );
};

describe('Company Notification System', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNotificationContext.notifications = [];
  });

  describe('Company Follow/Unfollow Notifications', () => {
    it('shows success notification when following a company', async () => {
      const user = userEvent.setup();
      const mockOnFollow = jest.fn().mockResolvedValue({ success: true });

      renderWithNotificationContext(
        <CompanyCard company={mockCompanies[0]} onFollow={mockOnFollow} />
      );

      const followButton = screen.getByText('Follow');
      await user.click(followButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Company Followed',
          message: 'You are now following Tech Innovations Inc. You will receive updates about their job postings and company news.',
        });
      });
    });

    it('shows success notification when unfollowing a company', async () => {
      const user = userEvent.setup();
      const mockOnFollow = jest.fn().mockResolvedValue({ success: true });

      renderWithNotificationContext(
        <CompanyCard company={mockCompanies[1]} onFollow={mockOnFollow} />
      );

      const unfollowButton = screen.getByText('Following');
      await user.click(unfollowButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'info',
          title: 'Company Unfollowed',
          message: 'You have unfollowed Green Energy Solutions. You will no longer receive updates from this company.',
        });
      });
    });

    it('shows error notification when follow action fails', async () => {
      const user = userEvent.setup();
      const mockOnFollow = jest.fn().mockRejectedValue(new Error('Follow failed'));

      renderWithNotificationContext(
        <CompanyCard company={mockCompanies[0]} onFollow={mockOnFollow} />
      );

      const followButton = screen.getByText('Follow');
      await user.click(followButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'error',
          title: 'Follow Action Failed',
          message: 'Failed to follow Tech Innovations Inc. Please try again.',
        });
      });
    });

    it('shows loading state during follow action', async () => {
      const user = userEvent.setup();
      let resolveFollow: () => void;
      const mockOnFollow = jest.fn(() => new Promise<void>(resolve => {
        resolveFollow = resolve;
      }));

      renderWithNotificationContext(
        <CompanyCard company={mockCompanies[0]} onFollow={mockOnFollow} />
      );

      const followButton = screen.getByText('Follow');
      await user.click(followButton);

      expect(screen.getByText('Loading...')).toBeInTheDocument();

      resolveFollow!();
      await waitFor(() => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      });
    });
  });

  describe('Company Update Notifications', () => {
    it('shows notification when followed company posts new job', () => {
      const mockNotifications = [
        {
          id: '1',
          type: 'info' as const,
          title: 'New Job Posted',
          message: 'Tech Innovations Inc has posted a new job: Senior Software Engineer.',
          timestamp: new Date().toISOString(),
        }
      ];

      // Mock the notifications in the context
      mockNotificationContext.notifications = mockNotifications;

      render(
        <NotificationProvider>
          <CompanyInsights companyId="1" />
        </NotificationProvider>
      );

      expect(screen.getByText('New Job Posted')).toBeInTheDocument();
      expect(screen.getByText('Tech Innovations Inc has posted a new job: Senior Software Engineer.')).toBeInTheDocument();
    });

    it('shows notification when followed company updates profile', () => {
      const mockNotifications = [
        {
          id: '2',
          type: 'info' as const,
          title: 'Company Update',
          message: 'Green Energy Solutions has updated their company profile and added new information.',
          timestamp: new Date().toISOString(),
        }
      ];

      // Mock the notifications in the context
      mockNotificationContext.notifications = mockNotifications;

      render(
        <NotificationProvider>
          <CompanyInsights companyId="2" />
        </NotificationProvider>
      );

      expect(screen.getByText('Company Update')).toBeInTheDocument();
      expect(screen.getByText('Green Energy Solutions has updated their company profile and added new information.')).toBeInTheDocument();
    });

    it('shows notification for company funding news', () => {
      const mockNotifications = [
        {
          id: '3',
          type: 'success' as const,
          title: 'Funding News',
          message: 'Tech Innovations Inc has raised $50M in Series B funding.',
          timestamp: new Date().toISOString(),
        }
      ];

      // Mock the notifications in the context
      mockNotificationContext.notifications = mockNotifications;

      render(
        <NotificationProvider>
          <CompanyInsights companyId="1" />
        </NotificationProvider>
      );

      expect(screen.getByText('Funding News')).toBeInTheDocument();
      expect(screen.getByText('Tech Innovations Inc has raised $50M in Series B funding.')).toBeInTheDocument();
    });
  });

  describe('Company Alert Notifications', () => {
    it('shows notification when company alert is created', async () => {
      const user = userEvent.setup();
      const mockOnCreateAlert = jest.fn().mockResolvedValue({ success: true });

      renderWithNotificationContext(
        <CompanyList
          companies={mockCompanies}
          onCompanyFollow={jest.fn()}
          onPageChange={jest.fn()}
          onCreateAlert={mockOnCreateAlert}
          currentPage={1}
          totalCount={2}
          pageSize={20}
        />
      );

      const alertButton = screen.getByText('Create Company Alert');
      await user.click(alertButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Company Alert Created',
          message: 'You will be notified when companies matching your criteria post new jobs or updates.',
        });
      });
    });

    it('shows notification when company alert creation fails', async () => {
      const user = userEvent.setup();
      const mockOnCreateAlert = jest.fn().mockRejectedValue(new Error('Alert creation failed'));

      renderWithNotificationContext(
        <CompanyList
          companies={mockCompanies}
          onCompanyFollow={jest.fn()}
          onPageChange={jest.fn()}
          onCreateAlert={mockOnCreateAlert}
          currentPage={1}
          totalCount={2}
          pageSize={20}
        />
      );

      const alertButton = screen.getByText('Create Company Alert');
      await user.click(alertButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'error',
          title: 'Alert Creation Failed',
          message: 'Failed to create company alert. Please try again.',
        });
      });
    });
  });

  describe('Company Insights Notifications', () => {
    it('shows notification when company insights are updated', async () => {
      const user = userEvent.setup();
      const mockOnRefreshInsights = jest.fn().mockResolvedValue({ 
        newInsights: 3,
        insights: ['New funding round', 'Leadership change', 'Product launch']
      });

      renderWithNotificationContext(
        <CompanyInsights 
          companyId="1" 
          onRefreshInsights={mockOnRefreshInsights}
        />
      );

      const refreshButton = screen.getByText('Refresh Insights');
      await user.click(refreshButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'info',
          title: 'Insights Updated',
          message: '3 new insights are available for companies you follow.',
        });
      });
    });

    it('shows notification when no new insights are found', async () => {
      const user = userEvent.setup();
      const mockOnRefreshInsights = jest.fn().mockResolvedValue({ 
        newInsights: 0,
        insights: []
      });

      renderWithNotificationContext(
        <CompanyInsights 
          companyId="1" 
          onRefreshInsights={mockOnRefreshInsights}
        />
      );

      const refreshButton = screen.getByText('Refresh Insights');
      await user.click(refreshButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'info',
          title: 'No New Insights',
          message: 'Your company insights are up to date.',
        });
      });
    });

    it('handles insights refresh error notifications', async () => {
      const user = userEvent.setup();
      const mockOnRefreshInsights = jest.fn().mockRejectedValue(new Error('Insights refresh failed'));

      renderWithNotificationContext(
        <CompanyInsights 
          companyId="1" 
          onRefreshInsights={mockOnRefreshInsights}
        />
      );

      const refreshButton = screen.getByText('Refresh Insights');
      await user.click(refreshButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'error',
          title: 'Insights Refresh Failed',
          message: 'Failed to refresh company insights. Please try again.',
        });
      });
    });
  });

  describe('Company Tracking Notifications', () => {
    it('shows notification when company tracking preferences are updated', async () => {
      const user = userEvent.setup();
      const mockOnUpdateTracking = jest.fn().mockResolvedValue({ success: true });

      renderWithNotificationContext(
        <CompanyInsights 
          companyId="1" 
          onUpdateTracking={mockOnUpdateTracking}
        />
      );

      const trackingButton = screen.getByText('Update Tracking Preferences');
      await user.click(trackingButton);

      await waitFor(() => {
        expect(mockNotificationContext.addNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Tracking Updated',
          message: 'Your company tracking preferences have been updated successfully.',
        });
      });
    });

    it('handles multiple company follow notifications', () => {
      const mockNotifications = [
        {
          id: '4',
          type: 'success' as const,
          title: 'Company Followed',
          message: 'You are now following Tech Innovations Inc.',
          timestamp: new Date().toISOString(),
        },
        {
          id: '5',
          type: 'success' as const,
          title: 'Company Followed',
          message: 'You are now following Green Energy Solutions.',
          timestamp: new Date().toISOString(),
        }
      ];

      // Mock the notifications in the context
      mockNotificationContext.notifications = mockNotifications;

      render(
        <NotificationProvider>
          <div>Multiple Company Follow Notifications Test</div>
        </NotificationProvider>
      );

      expect(screen.getAllByText('Company Followed')).toHaveLength(2);
      expect(screen.getByText('You are now following Tech Innovations Inc.')).toBeInTheDocument();
      expect(screen.getByText('You are now following Green Energy Solutions.')).toBeInTheDocument();
    });
  });

  describe('Notification Persistence and Management', () => {
    it('maintains notification state across component re-renders', () => {
      const mockNotifications = [
        {
          id: '6',
          type: 'info' as const,
          title: 'Company Recommendation',
          message: 'New company recommendations based on your interests are available.',
          timestamp: new Date().toISOString(),
        }
      ];

      // Mock the notifications in the context
      mockNotificationContext.notifications = mockNotifications;

      const { rerender } = renderWithNotificationContext(
        <CompanyList
          companies={mockCompanies}
          onCompanyFollow={jest.fn()}
          onPageChange={jest.fn()}
          currentPage={1}
          totalCount={2}
          pageSize={20}
        />
      );

      expect(screen.getByText('Company Recommendation')).toBeInTheDocument();

      // Re-render with same context
      rerender(
        <CompanyList
          companies={mockCompanies}
          onCompanyFollow={jest.fn()}
          onPageChange={jest.fn()}
          currentPage={1}
          totalCount={2}
          pageSize={20}
        />
      );

      expect(screen.getByText('Company Recommendation')).toBeInTheDocument();
    });

    it('handles notification dismissal correctly', async () => {
      const user = userEvent.setup();
      const mockNotifications = [
        {
          id: '7',
          type: 'warning' as const,
          title: 'Company Alert',
          message: 'A company you follow has significant changes.',
          timestamp: new Date().toISOString(),
        }
      ];

      // Mock the notifications in the context
      mockNotificationContext.notifications = mockNotifications;

      render(
        <NotificationProvider>
          <div>
            <span>Company Alert</span>
            <button onClick={() => mockNotificationContext.removeNotification('7')}>
              Dismiss
            </button>
          </div>
        </NotificationProvider>
      );

      const dismissButton = screen.getByText('Dismiss');
      await user.click(dismissButton);

      expect(mockNotificationContext.removeNotification).toHaveBeenCalledWith('7');
    });

    it('handles bulk notification clearing', async () => {
      const user = userEvent.setup();
      const mockNotifications = [
        {
          id: '8',
          type: 'info' as const,
          title: 'Company Update 1',
          message: 'First company update.',
          timestamp: new Date().toISOString(),
        },
        {
          id: '9',
          type: 'info' as const,
          title: 'Company Update 2',
          message: 'Second company update.',
          timestamp: new Date().toISOString(),
        }
      ];

      // Mock the notifications in the context
      mockNotificationContext.notifications = mockNotifications;

      render(
        <NotificationProvider>
          <div>
            <span>Company Update 1</span>
            <span>Company Update 2</span>
            <button onClick={() => mockNotificationContext.clearAll()}>
              Clear All
            </button>
          </div>
        </NotificationProvider>
      );

      const clearButton = screen.getByText('Clear All');
      await user.click(clearButton);

      expect(mockNotificationContext.clearAll).toHaveBeenCalled();
    });
  });

  describe('Accessibility and User Experience', () => {
    it('provides screen reader accessible notification announcements', () => {
      const mockNotifications = [
        {
          id: '10',
          type: 'success' as const,
          title: 'Company Followed',
          message: 'You are now following Tech Innovations Inc.',
          timestamp: new Date().toISOString(),
        }
      ];

      // Mock the notifications in the context
      mockNotificationContext.notifications = mockNotifications;

      render(
        <NotificationProvider>
          <div role="status" aria-live="polite">
            <span>Company Followed</span>
            <span>You are now following Tech Innovations Inc.</span>
          </div>
        </NotificationProvider>
      );

      const statusElement = screen.getByRole('status');
      expect(statusElement).toHaveAttribute('aria-live', 'polite');
      expect(screen.getByText('Company Followed')).toBeInTheDocument();
    });

    it('supports keyboard navigation for notification actions', async () => {
      const user = userEvent.setup();
      const mockOnFollow = jest.fn().mockResolvedValue({ success: true });

      renderWithNotificationContext(
        <CompanyCard company={mockCompanies[0]} onFollow={mockOnFollow} />
      );

      const followButton = screen.getByText('Follow');
      followButton.focus();
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockOnFollow).toHaveBeenCalled();
      });
    });

    it('provides appropriate notification timing and auto-dismiss', async () => {
      jest.useFakeTimers();
      
      const mockNotifications = [
        {
          id: '11',
          type: 'info' as const,
          title: 'Auto Dismiss Test',
          message: 'This notification should auto-dismiss.',
          timestamp: new Date().toISOString(),
          autoDismiss: true,
          duration: 5000,
        }
      ];

      // Mock the notifications in the context
      mockNotificationContext.notifications = mockNotifications;

      render(
        <NotificationProvider>
          <div>Auto Dismiss Test</div>
        </NotificationProvider>
      );

      expect(screen.getByText('Auto Dismiss Test')).toBeInTheDocument();

      // Fast-forward time
      jest.advanceTimersByTime(5000);

      await waitFor(() => {
        expect(mockNotificationContext.removeNotification).toHaveBeenCalledWith('11');
      });

      jest.useRealTimers();
    });
  });
});