"""
Simple test script for waitlist endpoint
Run with: python test_waitlist.py
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_waitlist():
    """Test the waitlist endpoint"""
    print("Testing Waitlist Endpoint...\n")
    
    # Test 1: Join waitlist with standard country
    print("1. Testing join waitlist with standard country...")
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "country": "United States",
        "custom_country": None
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/waitlist/",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        print("   ✅ Successfully joined waitlist\n")
    else:
        print("   ❌ Failed to join waitlist\n")
    
    # Test 2: Join waitlist with "Other" country
    print("2. Testing join waitlist with 'Other' country...")
    data2 = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "country": "Other",
        "custom_country": "Zimbabwe"
    }
    
    response2 = requests.post(
        f"{BASE_URL}/api/v1/waitlist/",
        json=data2,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Status: {response2.status_code}")
    print(f"   Response: {json.dumps(response2.json(), indent=2)}")
    
    if response2.status_code == 201:
        print("   ✅ Successfully joined waitlist with custom country\n")
    else:
        print("   ❌ Failed to join waitlist with custom country\n")
    
    # Test 3: Try to join with duplicate email
    print("3. Testing duplicate email rejection...")
    response3 = requests.post(
        f"{BASE_URL}/api/v1/waitlist/",
        json=data,  # Same email as first test
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Status: {response3.status_code}")
    print(f"   Response: {json.dumps(response3.json(), indent=2)}")
    
    if response3.status_code == 400:
        print("   ✅ Correctly rejected duplicate email\n")
    else:
        print("   ❌ Should have rejected duplicate email\n")
    
    # Test 4: Try to join with "Other" but no custom_country
    print("4. Testing validation - 'Other' country without custom_country...")
    data4 = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test.user@example.com",
        "country": "Other",
        "custom_country": None
    }
    
    response4 = requests.post(
        f"{BASE_URL}/api/v1/waitlist/",
        json=data4,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Status: {response4.status_code}")
    print(f"   Response: {json.dumps(response4.json(), indent=2)}")
    
    if response4.status_code == 400:
        print("   ✅ Correctly rejected missing custom_country\n")
    else:
        print("   ❌ Should have rejected missing custom_country\n")
    
    # Test 5: Get waitlist entries
    print("5. Testing get waitlist entries...")
    response5 = requests.get(f"{BASE_URL}/api/v1/waitlist/")
    
    print(f"   Status: {response5.status_code}")
    print(f"   Response: {json.dumps(response5.json(), indent=2)}")
    
    if response5.status_code == 200:
        print("   ✅ Successfully retrieved waitlist entries\n")
    else:
        print("   ❌ Failed to retrieve waitlist entries\n")
    
    print("Test completed!")

if __name__ == "__main__":
    try:
        test_waitlist()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server. Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

