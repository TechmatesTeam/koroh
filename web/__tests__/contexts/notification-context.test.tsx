import { render, screen, act } from '@testing-library/react';
import { NotificationProvider, useNotifications } from '@/contexts/notification-context';

// Test component to interact with the notification context
function TestComponent() {
  const { notifications, addNotification, removeNotification, markAsRead, clearAll } = useNotifications();

  return (
    <div>
      <div data-testid="notification-count">{notifications.length}</div>
      {notifications.map(notification => (
        <div key={notification.id} data-testid={`notification-${notification.id}`}>
          <span>{notification.title}</span>
          <span>{notification.message}</span>
          <span>{notification.type}</span>
          <span>{notification.read ? 'read' : 'unread'}</span>
        </div>
      ))}
      <button onClick={() => addNotification({ type: 'success', title: 'Success', message: 'Test message' })}>
        Add Success
      </button>
      <button onClick={() => addNotification({ type: 'error', title: 'Error', message: 'Error message' })}>
        Add Error
      </button>
      <button onClick={() => notifications.length > 0 && removeNotification(notifications[0].id)}>
        Remove First
      </button>
      <button onClick={() => notifications.length > 0 && markAsRead(notifications[0].id)}>
        Mark First Read
      </button>
      <button onClick={clearAll}>
        Clear All
      </button>
    </div>
  );
}

describe('NotificationContext', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('provides notification context to children', () => {
    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    expect(screen.getByTestId('notification-count')).toHaveTextContent('0');
  });

  it('adds notifications correctly', () => {
    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    act(() => {
      screen.getByText('Add Success').click();
    });

    expect(screen.getByTestId('notification-count')).toHaveTextContent('1');
    expect(screen.getByText('Success')).toBeInTheDocument();
    expect(screen.getByText('Test message')).toBeInTheDocument();
    expect(screen.getByText('success')).toBeInTheDocument();
    expect(screen.getByText('unread')).toBeInTheDocument();
  });

  it('removes notifications correctly', () => {
    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    act(() => {
      screen.getByText('Add Success').click();
    });

    expect(screen.getByTestId('notification-count')).toHaveTextContent('1');

    act(() => {
      screen.getByText('Remove First').click();
    });

    expect(screen.getByTestId('notification-count')).toHaveTextContent('0');
  });

  it('marks notifications as read', () => {
    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    act(() => {
      screen.getByText('Add Success').click();
    });

    expect(screen.getByText('unread')).toBeInTheDocument();

    act(() => {
      screen.getByText('Mark First Read').click();
    });

    expect(screen.getByText('read')).toBeInTheDocument();
  });

  it('clears all notifications', () => {
    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    act(() => {
      screen.getByText('Add Success').click();
      screen.getByText('Add Error').click();
    });

    expect(screen.getByTestId('notification-count')).toHaveTextContent('2');

    act(() => {
      screen.getByText('Clear All').click();
    });

    expect(screen.getByTestId('notification-count')).toHaveTextContent('0');
  });

  it('auto-removes success notifications after 5 seconds', () => {
    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    act(() => {
      screen.getByText('Add Success').click();
    });

    expect(screen.getByTestId('notification-count')).toHaveTextContent('1');

    act(() => {
      jest.advanceTimersByTime(5000);
    });

    expect(screen.getByTestId('notification-count')).toHaveTextContent('0');
  });

  it('does not auto-remove error notifications', () => {
    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    act(() => {
      screen.getByText('Add Error').click();
    });

    expect(screen.getByTestId('notification-count')).toHaveTextContent('1');

    act(() => {
      jest.advanceTimersByTime(5000);
    });

    expect(screen.getByTestId('notification-count')).toHaveTextContent('1');
  });

  it('throws error when used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useNotifications must be used within a NotificationProvider');

    consoleSpy.mockRestore();
  });
});