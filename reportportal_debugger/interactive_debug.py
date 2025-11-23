#!/usr/bin/env python3
"""
Interactive ReportPortal Debugger
Guides users through setup if credentials are missing
"""

import os
import sys
from pathlib import Path

def create_env_file():
    print("\n" + "="*80)
    print("🔧 ReportPortal Configuration Setup")
    print("="*80 + "\n")
    
    print("Let's set up your ReportPortal connection.\n")
    
    base_url = input("Enter your ReportPortal URL (e.g., https://rp.example.com): ").strip()
    if not base_url:
        print("❌ Base URL is required!")
        return False
    
    base_url = base_url.rstrip('/')
    
    print("\n📝 To get your API Token:")
    print("   1. Login to ReportPortal")
    print("   2. Click your profile (top right)")
    print("   3. Go to Profile → API Keys")
    print("   4. Copy your token\n")
    
    api_token = input("Enter your API Token: ").strip()
    if not api_token:
        print("❌ API Token is required!")
        return False
    
    project_name = input("Enter your Project Name: ").strip()
    if not project_name:
        print("❌ Project Name is required!")
        return False
    
    auto_update = input("\nAuto-update defect types? (y/n) [n]: ").strip().lower()
    auto_update = "true" if auto_update == "y" else "false"
    
    env_content = f"""# ReportPortal Configuration
RP_BASE_URL={base_url}
RP_API_TOKEN={api_token}
RP_PROJECT_NAME={project_name}
RP_LAUNCH_ID=
RP_AUTO_UPDATE={auto_update}
"""
    
    env_path = Path(__file__).parent / ".env"
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print("\n✅ Configuration saved to .env")
        print("🔒 Make sure .env is in .gitignore to keep credentials secure!\n")
        return True
    except Exception as e:
        print(f"\n❌ Error saving configuration: {e}")
        return False


def main():
    env_path = Path(__file__).parent / ".env"
    
    if not env_path.exists():
        print("\n⚠️  No .env file found!")
        response = input("Would you like to create one now? (y/n) [y]: ").strip().lower()
        
        if response != 'n':
            if create_env_file():
                print("✅ Setup complete! Starting debugger...\n")
            else:
                print("\n❌ Setup failed. Please create .env manually.")
                print("See QUICKSTART.md or README.md for instructions.\n")
                sys.exit(1)
        else:
            print("\n❌ Cannot proceed without configuration.")
            print("Please create a .env file. See QUICKSTART.md for help.\n")
            sys.exit(1)
    
    try:
        from rp_debugger import main as debug_main
        debug_main()
    except ImportError as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt\n")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(0)


