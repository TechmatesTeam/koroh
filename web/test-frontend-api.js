// Test frontend API connection with the actual API client
const axios = require('axios');

// Simulate the frontend API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://api:8000/api/v1';
const USE_MOCK_API = process.env.NEXT_PUBLIC_USE_MOCK_API === 'true';

console.log('Environment check:');
console.log('API_BASE_URL:', API_BASE_URL);
console.log('USE_MOCK_API:', USE_MOCK_API);
console.log('NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
console.log('NEXT_PUBLIC_USE_MOCK_API:', process.env.NEXT_PUBLIC_USE_MOCK_API);

// Create axios instance like the frontend does
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

async function testFrontendApiConnection() {
    try {
        console.log('\n🧪 Testing frontend API connection...');

        if (USE_MOCK_API) {
            console.log('⚠️  Mock API is enabled - frontend will use mock data');
            return;
        }

        // Test the auth endpoints that frontend uses
        console.log('Testing auth endpoints...');

        // Test login endpoint (should return 400 for missing credentials)
        try {
            await apiClient.post('/auth/login/', {});
        } catch (error) {
            if (error.response && error.response.status === 400) {
                console.log('✅ Login endpoint accessible (400 for missing credentials)');
            } else {
                throw error;
            }
        }

        // Test register endpoint (should return 400 for missing data)
        try {
            await apiClient.post('/auth/register/', {});
        } catch (error) {
            if (error.response && error.response.status === 400) {
                console.log('✅ Register endpoint accessible (400 for missing data)');
            } else {
                throw error;
            }
        }

        // Test profiles endpoint (should return 401 for no auth)
        try {
            await apiClient.get('/profiles/me/');
        } catch (error) {
            if (error.response && error.response.status === 401) {
                console.log('✅ Profiles endpoint accessible (401 for no auth)');
            } else {
                throw error;
            }
        }

        console.log('🎉 All API endpoints are accessible from frontend!');

    } catch (error) {
        console.error('❌ Frontend API connection failed:', error.message);
        if (error.response) {
            console.error('Response status:', error.response.status);
            console.error('Response data:', error.response.data);
        }
        if (error.code === 'ECONNREFUSED') {
            console.error('💡 Connection refused - check if backend is running');
        }
    }
}

testFrontendApiConnection();