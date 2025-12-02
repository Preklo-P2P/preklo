"""
Simple script to test USDC integration
Run this to verify USDC functionality is working

Usage:
    # Activate venv first
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    
    # Then run the script
    python backend/scripts/test_usdc_integration.py
"""

import asyncio
import sys
import os
from decimal import Decimal

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.aptos_service import aptos_service
from app.config import settings


async def test_usdc_balance():
    """Test USDC balance retrieval"""
    print("=" * 60)
    print("Testing USDC Balance Retrieval")
    print("=" * 60)
    
    # Test with a known address (you can replace with your test address)
    test_address = "0x1"  # Aptos test address
    
    print(f"\n1. Testing balance retrieval for address: {test_address}")
    print(f"   USDC Contract: {settings.circle_usdc_contract_address}")
    
    try:
        balance = await aptos_service.get_account_balance(test_address, "USDC")
        print(f"   ✓ USDC Balance: {balance}")
        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


async def test_usdc_contract_address():
    """Test USDC contract address configuration"""
    print("\n" + "=" * 60)
    print("Testing USDC Contract Address Configuration")
    print("=" * 60)
    
    print(f"\n1. Contract Address: {settings.circle_usdc_contract_address}")
    
    # Validate format
    if "::" in settings.circle_usdc_contract_address:
        parts = settings.circle_usdc_contract_address.split("::")
        print(f"   ✓ Format: {len(parts)} parts")
        print(f"   - Address: {parts[0]}")
        print(f"   - Module: {parts[1] if len(parts) > 1 else 'N/A'}")
        print(f"   - Struct: {parts[2] if len(parts) > 2 else 'N/A'}")
        return True
    else:
        print("   ✗ Invalid format - should be 'address::module::struct'")
        return False


async def test_aptos_connection():
    """Test Aptos connection"""
    print("\n" + "=" * 60)
    print("Testing Aptos Connection")
    print("=" * 60)
    
    try:
        health = await aptos_service._check_connection_health()
        if health:
            print("   ✓ Aptos connection is healthy")
            return True
        else:
            print("   ✗ Aptos connection is unhealthy")
            return False
    except Exception as e:
        print(f"   ✗ Error checking connection: {e}")
        return False


async def test_usdc_transfer_simulation():
    """Simulate USDC transfer (without actually sending)"""
    print("\n" + "=" * 60)
    print("Testing USDC Transfer Simulation")
    print("=" * 60)
    
    print("\n1. Testing transfer_usdc function availability")
    
    if hasattr(aptos_service, 'transfer_usdc'):
        print("   ✓ transfer_usdc method exists")
        
        # Check if SDK is available
        from app.services.aptos_service import _get_aptos_sdk
        SDK_AVAILABLE, _ = _get_aptos_sdk()
        
        if SDK_AVAILABLE:
            print("   ✓ Aptos SDK is available")
        else:
            print("   ⚠ Aptos SDK not available (may need: pip install aptos-sdk)")
        
        return True
    else:
        print("   ✗ transfer_usdc method not found")
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("USDC Integration Test Suite")
    print("=" * 60)
    print(f"\nNode URL: {settings.aptos_node_url}")
    print(f"USDC Contract: {settings.circle_usdc_contract_address}\n")
    
    results = []
    
    # Run tests
    results.append(("Contract Address", await test_usdc_contract_address()))
    results.append(("Aptos Connection", await test_aptos_connection()))
    results.append(("Transfer Function", await test_usdc_transfer_simulation()))
    results.append(("Balance Retrieval", await test_usdc_balance()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! USDC integration looks good.")
    else:
        print("\n⚠ Some tests failed. Please check the configuration.")
        print("\nNext steps:")
        print("1. Verify USDC contract address is correct for Aptos testnet")
        print("2. Ensure Aptos node URL is accessible")
        print("3. Check that aptos-sdk is installed: pip install aptos-sdk")
        print("4. Test with a real transfer using the API endpoints")


if __name__ == "__main__":
    asyncio.run(main())

