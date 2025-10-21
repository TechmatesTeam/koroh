# Frontend-Only Development Setup

This guide helps you run only the Koroh frontend on port 3000 with mock data for development purposes.

## Quick Start

### Option 1: Using the startup script
```bash
./start-frontend.sh
```

### Option 2: Using npm directly
```bash
cd web
npm install
npm run dev:mock
```

### Option 3: Manual setup
```bash
cd web
cp .env.local.example .env.local
# Edit .env.local and set NEXT_PUBLIC_USE_MOCK_API=true
npm install
npm run dev
```

## What's Available

The frontend will run on **http://localhost:3000** with the following features:

### ✅ Working Features (Mock Data)
- **Authentication**: Login/Register with demo accounts
- **Dashboard**: Personalized dashboard with mock data
- **Job Search**: Browse mock job listings
- **Company Discovery**: Explore mock company profiles
- **Peer Groups**: Join and interact with mock peer groups
- **AI Chat**: Simulated AI responses
- **Profile Management**: Update profile information
- **Portfolio Generation**: Mock portfolio creation

### 🔐 Demo Accounts
You can use these pre-configured accounts:

**Account 1:**
- Email: `demo@koroh.com`
- Password: `demo123`

**Account 2:**
- Email: `john@example.com`
- Password: `password123`

Or create a new account - it will be stored in localStorage.

### 🎯 Key Features

1. **Full UI/UX**: Complete user interface with all components
2. **Mock Authentication**: Login/logout functionality with localStorage
3. **Responsive Design**: Works on desktop and mobile
4. **Error Handling**: Proper error messages and loading states
5. **Notifications**: Toast notifications for user feedback
6. **Protected Routes**: Route protection and navigation guards

### 📁 Mock Data Includes

- **Jobs**: 50+ mock job listings with realistic data
- **Companies**: Company profiles with growth metrics
- **Peer Groups**: Professional networking groups
- **User Profiles**: Complete user profile management
- **AI Responses**: Simulated AI chat interactions
- **Portfolios**: Mock portfolio generation and management

## Development Features

### Hot Reload
The frontend supports hot reload - changes to code will automatically refresh the browser.

### Error Handling
- Development error overlay for debugging
- User-friendly error messages in production mode
- Comprehensive error logging

### Testing
```bash
cd web
npm test          # Run tests once
npm run test:watch # Run tests in watch mode
```

## Environment Configuration

The `.env.local` file controls the frontend behavior:

```env
# Enable mock API mode
NEXT_PUBLIC_USE_MOCK_API=true

# Frontend URL
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Development features
NEXT_PUBLIC_SHOW_ERROR_DETAILS=true
NODE_ENV=development
```

## Switching to Real Backend

When you're ready to connect to the real backend:

1. Start the backend services:
   ```bash
   make up  # or docker-compose up
   ```

2. Update `.env.local`:
   ```env
   NEXT_PUBLIC_USE_MOCK_API=false
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```

3. Restart the frontend:
   ```bash
   npm run dev
   ```

## Troubleshooting

### Port 3000 Already in Use
```bash
# Kill process using port 3000
lsof -ti:3000 | xargs kill -9

# Or use a different port
npm run dev -- -p 3001
```

### Mock Data Not Loading
1. Check that `NEXT_PUBLIC_USE_MOCK_API=true` in `.env.local`
2. Clear browser localStorage and refresh
3. Check browser console for errors

### Authentication Issues
1. Clear browser cookies and localStorage
2. Try using the demo accounts listed above
3. Check that mock API is enabled

## Next Steps

Once you're satisfied with the frontend:

1. **Backend Integration**: Connect to real Django backend
2. **Production Build**: Create optimized production build
3. **Deployment**: Deploy to production environment
4. **Real Data**: Replace mock data with real API calls

## Support

If you encounter issues:

1. Check the browser console for errors
2. Verify environment variables in `.env.local`
3. Ensure all dependencies are installed (`npm install`)
4. Try clearing browser cache and localStorage

The frontend is now ready for development with full mock data support!