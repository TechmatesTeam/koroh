# Koroh Authentication System

## Overview

The Koroh platform includes a complete authentication system that works in two modes:
1. **Frontend-Only Mode**: Uses mock API with localStorage for persistence (no backend required)
2. **Full-Stack Mode**: Connects to Django backend API

## Features

### ✅ User Registration
- Create new accounts with email and password
- Form validation with Zod schema
- Password strength requirements
- Terms of service acceptance
- Duplicate email prevention

### ✅ User Login
- Email and password authentication
- Remember me functionality
- Session persistence with cookies/localStorage
- Automatic redirect to dashboard after login

### ✅ Password Reset
- Forgot password functionality
- Email-based reset tokens (simulated in frontend-only mode)
- Secure token validation
- New password confirmation

### ✅ Session Management
- Automatic token refresh
- Logout functionality
- Protected routes
- Authentication state persistence

## Frontend-Only Mode (Port 3000 Only)

When `NEXT_PUBLIC_USE_MOCK_API=true`, the system uses a mock API that:

- Stores user data in localStorage
- Simulates network delays
- Provides demo accounts
- Handles all authentication flows
- Works without any backend services

### Demo Accounts

Visit `/demo` to see available demo accounts:

1. **Demo User**
   - Email: `demo@koroh.com`
   - Password: `demo123`

2. **John Doe**
   - Email: `john@example.com`
   - Password: `password123`

### Password Reset Demo

In frontend-only mode, password reset tokens are displayed directly in the UI for testing purposes.

## Usage

### Starting Frontend-Only Mode

```bash
# Using Docker
make frontend-only

# Or manually
cd web
npm install
NEXT_PUBLIC_USE_MOCK_API=true npm run dev
```

### Starting Full-Stack Mode

```bash
# Using Docker
make up

# This starts all services including backend API
```

## Authentication Flow

### Registration Flow
1. User fills registration form
2. Form validation (client-side)
3. API call to register endpoint
4. User account created
5. Automatic login and redirect to dashboard

### Login Flow
1. User enters email/password
2. Form validation
3. API call to login endpoint
4. Tokens stored (cookies or localStorage)
5. User state updated
6. Redirect to dashboard

### Password Reset Flow
1. User requests password reset
2. Reset token generated
3. Reset link provided (email in production, displayed in demo)
4. User clicks reset link
5. New password form
6. Password updated
7. Redirect to login

## Components

### Authentication Pages
- `/auth/login` - Login page
- `/auth/register` - Registration page
- `/auth/forgot-password` - Password reset request
- `/auth/reset-password` - Password reset form

### Authentication Components
- `LoginForm` - Login form with validation
- `RegisterForm` - Registration form with validation
- `ForgotPasswordForm` - Password reset request form
- `ResetPasswordForm` - Password reset form
- `ProtectedRoute` - Route protection wrapper
- `RedirectIfAuthenticated` - Redirect authenticated users

### Context & Hooks
- `AuthProvider` - Authentication context provider
- `useAuth()` - Authentication hook
- `NotificationProvider` - Notification system
- `useNotifications()` - Notification hook

## API Integration

### Mock API (`/lib/mock-api.ts`)
```typescript
// Authentication methods
mockApi.auth.login(credentials)
mockApi.auth.register(userData)
mockApi.auth.logout()
mockApi.auth.requestPasswordReset(email)
mockApi.auth.resetPassword(token, password)

// Profile methods
mockApi.profiles.getMe()
mockApi.profiles.updateMe(data)
```

### Real API (`/lib/api.ts`)
Automatically switches between mock and real API based on environment variables.

## Environment Variables

```bash
# Frontend-only mode
NEXT_PUBLIC_USE_MOCK_API=true
NEXT_PUBLIC_API_URL=

# Full-stack mode
NEXT_PUBLIC_USE_MOCK_API=false
NEXT_PUBLIC_API_URL=http://api:8000/api/v1
```

## Security Features

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number

### Form Validation
- Email format validation
- Password strength validation
- Confirm password matching
- Required field validation

### Session Security
- Secure token storage
- Automatic token refresh
- Session expiration handling
- CSRF protection ready

## Testing

The authentication system includes comprehensive tests:

```bash
# Run authentication tests
npm test -- --testPathPattern="auth"

# Run all tests
npm test
```

## Accessibility

All authentication forms are fully accessible:
- Proper form labels
- Keyboard navigation
- Screen reader support
- Error message announcements
- Focus management

## Responsive Design

Authentication pages work on all devices:
- Mobile-first design
- Touch-friendly interfaces
- Responsive layouts
- Optimized for all screen sizes

## Notifications

Real-time feedback for all authentication actions:
- Success notifications
- Error messages
- Loading states
- Auto-dismissing alerts

## Getting Started

1. **Start the frontend-only environment:**
   ```bash
   make frontend-only
   ```

2. **Visit the demo page:**
   ```
   http://localhost:3000/demo
   ```

3. **Try the authentication features:**
   - Create a new account
   - Login with demo accounts
   - Test password reset
   - Explore the dashboard

4. **Access the application:**
   ```
   Frontend: http://localhost:3000
   Demo Page: http://localhost:3000/demo
   ```

The authentication system is fully functional and ready to use with just the frontend on port 3000!