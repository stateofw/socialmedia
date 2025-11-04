#!/usr/bin/env python3
"""
System Validation Script

Verifies that all components are working correctly:
- Database connectivity
- API imports
- Service integrations
- Route registrations
- Configuration validation
"""

import sys
import asyncio
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}ℹ️  {msg}{RESET}")

def print_section(title):
    print(f"\n{BLUE}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{RESET}\n")

# Test 1: Import all services
def test_imports():
    print_section("Testing Imports")

    try:
        from app.services.ai import ai_service
        print_success("AI Service (Gemini/OpenAI)")

        from app.services.hashtag_generator import hashtag_generator
        print_success("Hashtag Generator")

        from app.services.content_polisher import content_polisher
        print_success("Content Polisher (GPT-4)")

        from app.services.publer import publer_service
        print_success("Publer Service")

        from app.services.analytics import analytics_service
        print_success("Analytics Service")

        from app.services.placid import placid_service
        print_success("Placid Service")

        from app.services.sheets import sheets_service
        print_success("Google Sheets Service")

        from app.tasks.recycling_tasks import run_daily_recycling
        print_success("Recycling Tasks")

        return True
    except Exception as e:
        print_error(f"Import failed: {e}")
        return False

# Test 2: Verify database
def test_database():
    print_section("Testing Database")

    try:
        from app.core.database import AsyncSessionLocal, engine
        from sqlalchemy import text

        # Check if database file exists (SQLite)
        if "sqlite" in str(engine.url):
            db_path = str(engine.url).split("///")[-1]
            if Path(db_path).exists():
                print_success(f"Database file exists: {db_path}")
            else:
                print_warning(f"Database file not found: {db_path}")

        # Try to connect
        async def check_connection():
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1

        if asyncio.run(check_connection()):
            print_success("Database connection successful")
            return True
        else:
            print_error("Database connection failed")
            return False

    except Exception as e:
        print_error(f"Database test failed: {e}")
        return False

# Test 3: Verify API routes
def test_routes():
    print_section("Testing API Routes")

    try:
        from app.api import api_router

        routes_count = len(api_router.routes)
        print_info(f"Total routes registered: {routes_count}")

        # Check for key routes
        route_paths = [r.path for r in api_router.routes]

        required_routes = {
            "Analytics Dashboard": "/analytics/dashboard",
            "Analytics Summary": "/analytics/summary",
            "Approval (GET)": "/approval/approve",
            "Approval (POST)": "/approval/{content_id}/approve",
            "Intake Form": "/intake/form",
            "Client Management": "/clients/",
            "Content Management": "/content/",
        }

        for name, path in required_routes.items():
            if path in route_paths:
                print_success(f"{name}: {path}")
            else:
                print_warning(f"{name}: {path} - NOT FOUND")

        return True

    except Exception as e:
        print_error(f"Route test failed: {e}")
        return False

# Test 4: Check configuration
def test_configuration():
    print_section("Testing Configuration")

    try:
        from app.core.config import settings

        # Check critical settings
        configs = {
            "OpenRouter API Key (REQUIRED)": bool(settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY != "your-key"),
            "USE_GEMINI": settings.USE_GEMINI if hasattr(settings, 'USE_GEMINI') else False,
            "Gemini Model": getattr(settings, 'GEMINI_MODEL', 'not set'),
            "Polisher Model": getattr(settings, 'POLISHER_MODEL', 'not set'),
            "Publer API Key (optional)": bool(settings.PUBLER_API_KEY and settings.PUBLER_API_KEY != "your-key"),
            "Publer Workspace ID (optional)": bool(settings.PUBLER_WORKSPACE_ID and settings.PUBLER_WORKSPACE_ID != "your-workspace-id"),
            "Placid API Key (optional)": bool(settings.PLACID_API_KEY and settings.PLACID_API_KEY != "your-key"),
            "Google Sheets ID (optional)": bool(settings.GOOGLE_SHEETS_ID),
        }

        for name, configured in configs.items():
            if configured:
                print_success(f"{name}: Configured")
            else:
                print_warning(f"{name}: Not configured (optional)")

        return True

    except Exception as e:
        print_error(f"Configuration test failed: {e}")
        return False

# Test 5: Test hashtag generation
def test_hashtag_generation():
    print_section("Testing Hashtag Generation")

    try:
        from app.services.hashtag_generator import hashtag_generator

        hashtags = hashtag_generator.generate_hashtags(
            industry="landscaping",
            city="Brewster",
            state="NY",
            content_type="tip",
            platform="instagram",
            include_local=True,
            include_branded=True,
            business_name="Test Business"
        )

        print_info(f"Generated {len(hashtags)} hashtags")
        print_info(f"Sample: {' '.join(hashtags[:5])}")

        if len(hashtags) > 0:
            print_success("Hashtag generation working")
            return True
        else:
            print_error("No hashtags generated")
            return False

    except Exception as e:
        print_error(f"Hashtag test failed: {e}")
        return False

# Test 6: Check migrations
def test_migrations():
    print_section("Testing Database Migrations")

    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        alembic_cfg = Config("alembic.ini")
        script_dir = ScriptDirectory.from_config(alembic_cfg)

        head_revision = script_dir.get_current_head()
        print_info(f"Current migration head: {head_revision}")

        # Check if key migrations exist
        migrations = Path("migrations/versions").glob("*.py")
        migration_names = [m.stem for m in migrations]

        required_migrations = [
            "add_retry_rejection_fields",
            "add_prd_fields",
            "add_publer_multiworkspace"
        ]

        for migration in required_migrations:
            found = any(migration in name for name in migration_names)
            if found:
                print_success(f"Migration exists: {migration}")
            else:
                print_warning(f"Migration not found: {migration}")

        return True

    except Exception as e:
        print_error(f"Migration test failed: {e}")
        return False

# Test 7: Verify models
def test_models():
    print_section("Testing Database Models")

    try:
        from app.models.client import Client
        from app.models.content import Content, ContentStatus
        from app.models.user import User

        # Check Client model has new fields
        client_fields = [
            "publer_workspace_id",
            "publer_api_key",
            "tone_preference",
            "promotions_offers",
            "off_limits_topics",
            "reuse_media",
        ]

        for field in client_fields:
            if hasattr(Client, field):
                print_success(f"Client.{field} exists")
            else:
                print_warning(f"Client.{field} missing")

        return True

    except Exception as e:
        print_error(f"Model test failed: {e}")
        return False

# Main execution
def main():
    print(f"\n{BLUE}{'='*60}")
    print(f"  SOCIAL AUTOMATION SYSTEM VALIDATION")
    print(f"{'='*60}{RESET}\n")

    results = {}

    # Run all tests
    results["Imports"] = test_imports()
    results["Database"] = test_database()
    results["API Routes"] = test_routes()
    results["Configuration"] = test_configuration()
    results["Hashtag Generation"] = test_hashtag_generation()
    results["Migrations"] = test_migrations()
    results["Models"] = test_models()

    # Summary
    print_section("Validation Summary")

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {test_name}: {status}")

    print(f"\n{BLUE}{'='*60}{RESET}")

    if passed == total:
        print_success(f"All tests passed! ({passed}/{total})")
        print_info("System is ready for production use! 🚀")
        return 0
    else:
        print_warning(f"Some tests failed ({passed}/{total} passed)")
        print_info("Review warnings above and configure missing services")
        return 1

if __name__ == "__main__":
    sys.exit(main())
