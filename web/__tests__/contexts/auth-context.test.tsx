import { render, screen, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '@/contexts/auth-context';
import { NotificationProvider } from '@/contexts/notification-context';

// Mock Next.js router
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock API
const mockApi = {
  auth: {
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
  },
  profiles: {
    getMe: jest.fn(),
  },
};

jest.mock('@/lib/api', () => ({
  api: mockApi,
}));

// Mock js-cookie
const mockCookies = {
  get: jest.fn(),
  set: jest.fn(),
  remove: jest.fn(),
};

jest.mock('js-cookie', () => mockCookies);

// Test component to interact with the auth context
function TestComponent() {
  const { user, loading, login, register, logout, isAuthenticated } = useAuth();

  return (
    <div>
      <div data-testid="loading">{loading ? 'loading' : 'not-loading'}</div>
      <div data-testid="authenticated">{isAuthenticated ? 'authenticated' : 'not-authenticated'}</div>
      <div data-testid="user">{user ? `${user.first_name} ${user.last_name}` : 'no-user'}</div>
      <button onClick={() => login({ email: 'test@example.com', password: 'password' })}>
        Login
      </button>
      <button onClick={() => register({ 
        first_name: 'John', 
        last_name: 'Doe', 
        email: 'john@example.com', 
        password: 'password123' 
      })}>
        Register
      </button>
      <button onClick={logout}>
        Logout
      </button>
    </div>
  );
}

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <NotificationProvider>
    <AuthProvider>
      {children}
    </AuthProvider>
  </NotificationProvider>
);

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCookies.get.mockReturnValue(null);
  });

  it('provides auth context to children', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');
    expect(screen.getByTestId('user')).toHaveTextContent('no-user');
  });

  it('checks authentication on mount with valid token', async () => {
    const mockUser = { id: 1, first_name: 'John', last_name: 'Doe', email: 'john@example.com' };
    mockCookies.get.mockReturnValue('valid-token');
    mockApi.profiles.getMe.mockResolvedValue({ data: { user: mockUser } });

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
    expect(screen.getByTestId('user')).toHaveTextContent('John Doe');
  });

  it('handles invalid token on mount', async () => {
    mockCookies.get.mockReturnValue('invalid-token');
    mockApi.profiles.getMe.mockRejectedValue(new Error('Unauthorized'));

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');
    expect(mockCookies.remove).toHaveBeenCalledWith('access_token');
    expect(mockCookies.remove).toHaveBeenCalledWith('refresh_token');
  });

  it('handles successful login', async () => {
    const mockUser = { id: 1, first_name: 'John', last_name: 'Doe', email: 'john@example.com' };
    mockApi.auth.login.mockResolvedValue({
      data: {
        access: 'access-token',
        refresh: 'refresh-token',
        user: mockUser,
      },
    });

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    await act(async () => {
      screen.getByText('Login').click();
    });

    expect(mockApi.auth.login).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password',
    });
    expect(mockCookies.set).toHaveBeenCalledWith('access_token', 'access-token', { expires: 1 });
    expect(mockCookies.set).toHaveBeenCalledWith('refresh_token', 'refresh-token', { expires: 7 });
    expect(mockPush).toHaveBeenCalledWith('/dashboard');
  });

  it('handles successful registration', async () => {
    const mockUser = { id: 1, first_name: 'John', last_name: 'Doe', email: 'john@example.com' };
    mockApi.auth.register.mockResolvedValue({
      data: {
        access: 'access-token',
        refresh: 'refresh-token',
        user: mockUser,
      },
    });

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    await act(async () => {
      screen.getByText('Register').click();
    });

    expect(mockApi.auth.register).toHaveBeenCalledWith({
      first_name: 'John',
      last_name: 'Doe',
      email: 'john@example.com',
      password: 'password123',
    });
    expect(mockPush).toHaveBeenCalledWith('/dashboard');
  });

  it('handles logout', async () => {
    const mockUser = { id: 1, first_name: 'John', last_name: 'Doe', email: 'john@example.com' };
    mockCookies.get.mockReturnValue('valid-token');
    mockApi.profiles.getMe.mockResolvedValue({ data: { user: mockUser } });

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
    });

    act(() => {
      screen.getByText('Logout').click();
    });

    expect(mockApi.auth.logout).toHaveBeenCalled();
    expect(mockCookies.remove).toHaveBeenCalledWith('access_token');
    expect(mockCookies.remove).toHaveBeenCalledWith('refresh_token');
    expect(mockPush).toHaveBeenCalledWith('/');
    expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');
  });

  it('throws error when used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useAuth must be used within an AuthProvider');

    consoleSpy.mockRestore();
  });
});