#!/usr/bin/env python3
"""
Test Client Portal
Quick script to verify client can login and access their portal
"""

import requests

BASE_URL = "http://localhost:8000"

# Test data
CLIENT_EMAIL = "client@testbusiness.com"
CLIENT_PASSWORD = "TestPass123"

def test_client_login():
    """Test client login"""
    print("🔐 Testing client login...")

    response = requests.post(
        f"{BASE_URL}/api/v1/client/login",
        data={
            "email": CLIENT_EMAIL,
            "password": CLIENT_PASSWORD
        },
        allow_redirects=False
    )

    if response.status_code == 303:
        print("✅ Login successful! Redirected to:", response.headers.get('location'))
        session_cookie = response.cookies.get('client_session')
        if session_cookie:
            print(f"✅ Session cookie set: {session_cookie[:20]}...")
            return session_cookie
        else:
            print("❌ No session cookie set")
            return None
    else:
        print(f"❌ Login failed with status {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_dashboard(session_cookie):
    """Test accessing dashboard"""
    print("\n📊 Testing dashboard access...")

    response = requests.get(
        f"{BASE_URL}/api/v1/client/dashboard",
        cookies={"client_session": session_cookie}
    )

    if response.status_code == 200:
        print("✅ Dashboard accessible")
        # Check for key content
        if "Test Business" in response.text:
            print("✅ Business name found in dashboard")
        if "Pending Approval" in response.text:
            print("✅ Stats displayed")
        return True
    else:
        print(f"❌ Dashboard failed with status {response.status_code}")
        return False

def test_content_list(session_cookie):
    """Test accessing content list"""
    print("\n📝 Testing content list...")

    response = requests.get(
        f"{BASE_URL}/api/v1/client/content",
        cookies={"client_session": session_cookie}
    )

    if response.status_code == 200:
        print("✅ Content list accessible")
        if "pending_approval" in response.text or "Spring" in response.text:
            print("✅ Content items found")
        return True
    else:
        print(f"❌ Content list failed with status {response.status_code}")
        return False

def test_media_page(session_cookie):
    """Test accessing media library"""
    print("\n📸 Testing media library...")

    response = requests.get(
        f"{BASE_URL}/api/v1/client/media",
        cookies={"client_session": session_cookie}
    )

    if response.status_code == 200:
        print("✅ Media library accessible")
        if "Upload" in response.text:
            print("✅ Upload functionality present")
        return True
    else:
        print(f"❌ Media library failed with status {response.status_code}")
        return False

def main():
    print("=" * 60)
    print("  CLIENT PORTAL TEST")
    print("=" * 60)
    print()
    print(f"Testing with:")
    print(f"  Email: {CLIENT_EMAIL}")
    print(f"  Password: {CLIENT_PASSWORD}")
    print()

    # Test login
    session_cookie = test_client_login()

    if not session_cookie:
        print("\n❌ Login failed - cannot continue tests")
        return False

    # Test dashboard
    dashboard_ok = test_dashboard(session_cookie)

    # Test content list
    content_ok = test_content_list(session_cookie)

    # Test media
    media_ok = test_media_page(session_cookie)

    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    print(f"  Login:        {'✅ PASS' if session_cookie else '❌ FAIL'}")
    print(f"  Dashboard:    {'✅ PASS' if dashboard_ok else '❌ FAIL'}")
    print(f"  Content List: {'✅ PASS' if content_ok else '❌ FAIL'}")
    print(f"  Media Library:{'✅ PASS' if media_ok else '❌ FAIL'}")
    print("=" * 60)

    all_passed = session_cookie and dashboard_ok and content_ok and media_ok

    if all_passed:
        print("\n🎉 All tests passed! Client portal is working!")
        print(f"\n   Visit: {BASE_URL}/api/v1/client/login")
        print(f"   Email: {CLIENT_EMAIL}")
        print(f"   Password: {CLIENT_PASSWORD}")
    else:
        print("\n⚠️  Some tests failed - check output above")

    return all_passed

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
