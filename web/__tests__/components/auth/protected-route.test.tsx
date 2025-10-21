import { render, screen } from '@testing-library/react';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { AuthProvider } from '@/contexts/auth-context';
import { NotificationProvider } from '@/contexts/notification-context';

// Mock Next.js router
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock API
jest.mock('@/lib/api', () => ({
  api: {
    auth: {
      logout: jest.fn(),
    },
    profiles: {
      getMe: jest.fn(),
    },
  },
}));

// Mock js-cookie
jest.mock('js-cookie', () => ({
  get: jest.fn(),
  set: jest.fn(),
  remove: jest.fn(),
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <NotificationProvider>
    <AuthProvider>
      {children}
    </AuthProvider>
  </NotificationProvider>
);

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows loading spinner while authentication is being checked', () => {
    const Cookies = require('js-cookie');
    const { api } = require('@/lib/api');
    
    Cookies.get.mockReturnValue('mock-token');
    api.profiles.getMe.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(
      <TestWrapper>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </TestWrapper>
    );

    expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner has role="status"
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('renders children when user is authenticated', async () => {
    const Cookies = require('js-cookie');
    const { api } = require('@/lib/api');
    
    Cookies.get.mockReturnValue('mock-token');
    api.profiles.getMe.mockResolvedValue({
      data: {
        user: { id: 1, email: 'test@example.com', first_name: 'Test', last_name: 'User' }
      }
    });

    render(
      <TestWrapper>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </TestWrapper>
    );

    // Wait for authentication to complete
    await screen.findByText('Protected Content');
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('redirects to login when user is not authenticated', async () => {
    const Cookies = require('js-cookie');
    
    Cookies.get.mockReturnValue(null); // No token

    render(
      <TestWrapper>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </TestWrapper>
    );

    // Wait for the redirect to be triggered
    await new Promise(resolve => setTimeout(resolve, 100));
    
    expect(mockPush).toHaveBeenCalledWith('/auth/login');
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('redirects to custom path when specified', async () => {
    const Cookies = require('js-cookie');
    
    Cookies.get.mockReturnValue(null); // No token

    render(
      <TestWrapper>
        <ProtectedRoute redirectTo="/custom-login">
          <div>Protected Content</div>
        </ProtectedRoute>
      </TestWrapper>
    );

    // Wait for the redirect to be triggered
    await new Promise(resolve => setTimeout(resolve, 100));
    
    expect(mockPush).toHaveBeenCalledWith('/custom-login');
  });

  it('handles invalid token by redirecting to login', async () => {
    const Cookies = require('js-cookie');
    const { api } = require('@/lib/api');
    
    Cookies.get.mockReturnValue('invalid-token');
    api.profiles.getMe.mockRejectedValue(new Error('Unauthorized'));

    render(
      <TestWrapper>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </TestWrapper>
    );

    // Wait for the authentication check and redirect
    await new Promise(resolve => setTimeout(resolve, 100));
    
    expect(mockPush).toHaveBeenCalledWith('/auth/login');
    expect(Cookies.remove).toHaveBeenCalledWith('access_token');
    expect(Cookies.remove).toHaveBeenCalledWith('refresh_token');
  });
});