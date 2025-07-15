#!/usr/bin/env python3
"""
Setup script for Resume Screening System
Helps configure the system and install dependencies using uv
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_uv_installed():
    """Check if uv is installed"""
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        print("✅ uv is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ uv is not installed")
        print("   Installing uv...")
        return install_uv()

def install_uv():
    """Install uv package manager"""
    try:
        # Install uv using the official installer
        subprocess.run([
            sys.executable, "-m", "pip", "install", "uv"
        ], check=True)
        print("✅ uv installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install uv: {e}")
        print("   Please install uv manually:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False

def install_dependencies():
    """Install required dependencies using uv"""
    print("\n📦 Installing dependencies with uv...")
    
    try:
        # Use uv to install dependencies from pyproject.toml
        subprocess.check_call(["uv", "sync"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file from template"""
    env_file = Path(".env")
    env_example = Path("env_example.txt")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ env_example.txt not found")
        return False
    
    try:
        with open(env_example, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ Created .env file from template")
        print("   Please edit .env with your actual API keys")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def check_credentials():
    """Check if Google credentials file exists"""
    creds_file = Path("credentials.json")
    
    if creds_file.exists():
        print("✅ Google credentials file found")
        return True
    
    print("⚠️  Google credentials file not found")
    print("   Please download credentials.json from Google Cloud Console")
    print("   Instructions:")
    print("   1. Go to https://console.cloud.google.com/")
    print("   2. Create a new project or select existing")
    print("   3. Enable Google Drive API")
    print("   4. Create OAuth 2.0 credentials (Desktop application)")
    print("   5. Download and rename to credentials.json")
    return False

def validate_env_variables():
    """Check if required environment variables are set"""
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   Please set these in your .env file")
        return False
    
    print("✅ Required environment variables are set")
    return True

def run_tests():
    """Run system tests using uv"""
    print("\n🧪 Running system tests...")
    
    try:
        # Use uv to run tests
        result = subprocess.run(["uv", "run", "python", "test_system.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ System tests passed")
            return True
        else:
            print("❌ System tests failed")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    sample_dir = Path("sample_data")
    sample_dir.mkdir(exist_ok=True)
    
    # Create sample resume
    sample_resume = """
John Smith
Software Engineer
john.smith@email.com

EXPERIENCE
Senior Software Engineer | TechCorp | 2020-2023
- Developed AI-powered applications using Python and TensorFlow
- Led team of 5 developers in building scalable microservices
- Implemented MLOps pipelines using Docker and Kubernetes

Software Engineer | StartupXYZ | 2018-2020
- Built REST APIs using Python Flask and PostgreSQL
- Worked with cloud platforms (AWS, GCP)

EDUCATION
Bachelor of Science in Computer Science
University of Technology | 2018

SKILLS
Python, JavaScript, TensorFlow, PyTorch, AWS, GCP, Docker, Kubernetes
"""
    
    with open(sample_dir / "sample_resume.txt", "w") as f:
        f.write(sample_resume)
    
    print("✅ Created sample data in sample_data/ directory")

def create_uv_scripts():
    """Create convenient uv scripts for common tasks"""
    scripts_dir = Path(".uv")
    scripts_dir.mkdir(exist_ok=True)
    
    # Create scripts for common tasks
    scripts = {
        "dev": "uv run python unified_resume_screener.py",
        "test": "uv run python test_system.py",
        "format": "uv run black .",
        "lint": "uv run flake8 .",
        "typecheck": "uv run mypy .",
        "install-dev": "uv sync --group dev",
        "install-test": "uv sync --group test",
    }
    
    for name, command in scripts.items():
        script_file = scripts_dir / f"{name}.sh"
        with open(script_file, "w") as f:
            f.write(f"#!/bin/bash\n{command}\n")
        script_file.chmod(0o755)
    
    print("✅ Created uv convenience scripts in .uv/ directory")

def main():
    """Main setup function"""
    print("🚀 Resume Screening System Setup (uv)")
    print("=" * 45)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check/install uv
    if not check_uv_installed():
        print("\n❌ Setup failed at uv installation")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        print("\n❌ Setup failed at environment file creation")
        sys.exit(1)
    
    # Check credentials
    check_credentials()
    
    # Create sample data
    create_sample_data()
    
    # Create uv scripts
    create_uv_scripts()
    
    print("\n📋 Setup Summary")
    print("-" * 20)
    print("✅ uv package manager configured")
    print("✅ Dependencies installed")
    print("✅ .env file created")
    print("✅ Convenience scripts created")
    print("⚠️  Please configure:")
    print("   - Google API credentials (credentials.json)")
    print("   - Environment variables in .env file")
    
    print("\n🎯 Next Steps:")
    print("1. Edit .env file with your API keys")
    print("2. Download Google credentials.json")
    print("3. Run: uv run python test_system.py")
    print("4. Run: uv run python unified_resume_screener.py")
    
    print("\n🚀 Quick Commands:")
    print("  uv run python unified_resume_screener.py    # Start the web interface")
    print("  uv run python test_system.py   # Run system tests")
    print("  uv run black .                 # Format code")
    print("  uv run flake8 .                # Lint code")
    print("  uv run mypy .                  # Type check")
    
    print("\n📚 Documentation:")
    print("- README.md: Complete setup and usage guide")
    print("- env_example.txt: Environment variable template")
    print("- test_system.py: System validation tests")
    print("- pyproject.toml: Project configuration")
    
    print("\n🎉 Setup completed successfully!")

if __name__ == "__main__":
    main() 