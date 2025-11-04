#!/usr/bin/env python3
"""
Quick verification script to check if the environment is properly configured.
Run this before starting the application.
"""
import os
import sys
from pathlib import Path


def check_env_file():
    """Check if .env file exists and has required variables."""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found!")
        print("   Run: cp .env.example .env")
        return False

    required_vars = [
        "SECRET_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "OPENAI_API_KEY",
    ]

    with open(env_path) as f:
        content = f.read()

    missing = []
    for var in required_vars:
        if f"{var}=" not in content or f"{var}=your-" in content or f"{var}=sk-your-" in content:
            missing.append(var)

    if missing:
        print(f"❌ Missing or unconfigured environment variables: {', '.join(missing)}")
        return False

    print("✅ .env file configured")
    return True


def check_docker():
    """Check if Docker is available."""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"✅ Docker installed: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker not found!")
        print("   Install from: https://docker.com")
        return False


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python 3.11+ required, found {version.major}.{version.minor}.{version.micro}")
        return False


def check_project_structure():
    """Check if essential files exist."""
    essential_files = [
        "requirements.txt",
        "docker-compose.yml",
        "app/main.py",
        "app/core/config.py",
        "app/models/client.py",
        "app/api/routes/auth.py",
    ]

    missing = [f for f in essential_files if not Path(f).exists()]

    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return False

    print("✅ Project structure intact")
    return True


def main():
    print("🔍 Verifying Social Automation SaaS setup...\n")

    checks = [
        check_python_version(),
        check_project_structure(),
        check_env_file(),
        check_docker(),
    ]

    print("\n" + "="*50)
    if all(checks):
        print("✅ All checks passed! Ready to start.")
        print("\nNext steps:")
        print("  1. Start with Docker: docker-compose up -d")
        print("  2. View logs: docker-compose logs -f")
        print("  3. Visit admin UI: http://localhost:8000/admin/login")
        print("  4. View API docs: http://localhost:8000/docs")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
