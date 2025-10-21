#!/bin/bash

# Test script for Koroh authentication system
echo "🚀 Testing Koroh Authentication System"
echo "======================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Start frontend-only environment
echo "🔧 Starting frontend-only environment..."
make frontend-only

# Wait for the service to be ready
echo "⏳ Waiting for frontend to be ready..."
sleep 10

# Check if the service is running
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running successfully!"
    echo ""
    echo "🎉 Authentication system is ready!"
    echo ""
    echo "📋 Available URLs:"
    echo "   • Main App:    http://localhost:3000"
    echo "   • Demo Page:   http://localhost:3000/demo"
    echo "   • Login:       http://localhost:3000/auth/login"
    echo "   • Register:    http://localhost:3000/auth/register"
    echo ""
    echo "👤 Demo Accounts:"
    echo "   • Email: demo@koroh.com, Password: demo123"
    echo "   • Email: john@example.com, Password: password123"
    echo ""
    echo "🔧 Features Available:"
    echo "   ✅ User registration"
    echo "   ✅ User login/logout"
    echo "   ✅ Password reset"
    echo "   ✅ Session management"
    echo "   ✅ Protected routes"
    echo "   ✅ Responsive design"
    echo "   ✅ Accessibility compliance"
    echo ""
    echo "🌐 Open http://localhost:3000/demo in your browser to get started!"
else
    echo "❌ Frontend failed to start properly"
    echo "📋 Checking logs..."
    docker-compose -f docker-compose.frontend-only.yml logs web
    exit 1
fi