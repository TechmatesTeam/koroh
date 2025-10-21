#!/bin/bash

# Start only the frontend on port 3000
echo "🚀 Starting Koroh Frontend (Mock Mode)"
echo "=================================="
echo "Frontend will be available at: http://localhost:3000"
echo "Using mock API for development"
echo ""
echo "Demo Accounts:"
echo "  📧 demo@koroh.com / demo123"
echo "  📧 john@example.com / password123"
echo ""

cd web

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Ensure .env.local exists with mock API enabled
if [ ! -f ".env.local" ]; then
    echo "📝 Creating .env.local with mock API enabled..."
    cp .env.local.example .env.local
fi

# Verify mock API setting
if ! grep -q "NEXT_PUBLIC_USE_MOCK_API=true" .env.local; then
    echo "⚠️  Warning: Mock API might not be enabled in .env.local"
    echo "   Make sure NEXT_PUBLIC_USE_MOCK_API=true"
fi

# Start the development server
echo "🌐 Starting Next.js development server..."
echo "   Press Ctrl+C to stop"
echo ""
npm run dev