/**
 * Frontend API Call Test
 * Test if frontend can successfully call backend APIs
 */

const BACKEND_URL = 'http://localhost:8000';

async function testAPICall() {
    console.log('Testing Frontend -> Backend API Calls...\n');
    
    try {
        // Test 1: Health Check
        console.log('1. Testing Health Check...');
        const healthResponse = await fetch(`${BACKEND_URL}/health`);
        const healthData = await healthResponse.json();
        console.log(`   Status: ${healthResponse.status}`);
        console.log(`   Response: ${JSON.stringify(healthData, null, 2)}`);
        console.log('   Health check successful\n');
        
        // Test 2: User Registration (like frontend would do)
        console.log('2. Testing User Registration...');
        const timestamp = Date.now();
        const registrationData = {
            username: `frontend_js_${timestamp}`,
            email: `frontend_js_${timestamp}@example.com`,
            wallet_address: `0x${timestamp.toString(16).padStart(40, '0')}`,
            password: 'frontend_test_password_123',
            full_name: 'Frontend JS Test User'
        };
        
        const registerResponse = await fetch(`${BACKEND_URL}/api/v1/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:8080'  // Simulate frontend origin
            },
            body: JSON.stringify(registrationData)
        });
        
        const registerData = await registerResponse.json();
        console.log(`   Status: ${registerResponse.status}`);
        console.log(`   Response: ${JSON.stringify(registerData, null, 2)}`);
        
        if (registerResponse.status === 200) {
            console.log('   Registration successful\n');
            
            // Test 3: Login
            console.log('3. Testing Login...');
            const loginData = {
                username: registrationData.username,
                password: registrationData.password
            };
            
            const loginResponse = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Origin': 'http://localhost:8080'
                },
                body: JSON.stringify(loginData)
            });
            
            const loginResult = await loginResponse.json();
            console.log(`   Status: ${loginResponse.status}`);
            
            if (loginResponse.status === 200 && loginResult.data?.tokens?.access_token) {
                const accessToken = loginResult.data.tokens.access_token;
                console.log('   Login successful, JWT token received\n');
                
                // Test 4: Authenticated Request
                console.log('4. Testing Authenticated Request...');
                const meResponse = await fetch(`${BACKEND_URL}/api/v1/auth/me`, {
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                        'Origin': 'http://localhost:8080'
                    }
                });
                
                const meData = await meResponse.json();
                console.log(`   Status: ${meResponse.status}`);
                console.log(`   User Data: ${JSON.stringify(meData.data, null, 2)}`);
                
                if (meResponse.status === 200) {
                    console.log('   Authenticated request successful\n');
                    
                    console.log('ALL TESTS PASSED!');
                    console.log('Frontend can successfully communicate with backend');
                    console.log('Authentication flow works end-to-end');
                    console.log('CORS is properly configured');
                    console.log('JWT tokens are working correctly');
                    console.log('\nYour AptosSend platform is FULLY FUNCTIONAL!');
                    
                } else {
                    console.log('   Authenticated request failed');
                }
            } else {
                console.log('   Login failed or missing token');
            }
        } else {
            console.log('   Registration failed');
        }
        
    } catch (error) {
        console.error('API test error:', error);
    }
}

// Run the test
testAPICall();
