// Simple test to verify mock API is working
const { mockApi } = require('./lib/mock-api');

async function testMockApi() {
  console.log('🧪 Testing Mock API...');
  
  try {
    // Test registration
    console.log('Testing registration...');
    const registerResult = await mockApi.auth.register({
      email: 'test@example.com',
      password: 'test123',
      first_name: 'Test',
      last_name: 'User'
    });
    console.log('✅ Registration successful:', registerResult.data.user.email);
    
    // Test login
    console.log('Testing login...');
    const loginResult = await mockApi.auth.login({
      email: 'test@example.com',
      password: 'test123'
    });
    console.log('✅ Login successful:', loginResult.data.user.email);
    
    // Test profile
    console.log('Testing profile...');
    const profileResult = await mockApi.profiles.getMe();
    console.log('✅ Profile retrieved:', profileResult.data.user.email);
    
    console.log('🎉 All mock API tests passed!');
    
  } catch (error) {
    console.error('❌ Mock API test failed:', error.message);
  }
}

// Run if called directly
if (require.main === module) {
  testMockApi();
}

module.exports = { testMockApi };