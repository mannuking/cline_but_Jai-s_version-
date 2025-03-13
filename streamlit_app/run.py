#!/usr/bin/env python
import os
import subprocess
import sys
import argparse
import platform
from pathlib import Path

def setup_environment():
    """Set up the environment for running the Streamlit app."""
    print("Setting up environment...")
    
    # Check Python version
    python_version = sys.version_info
    if (python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8)):
        print(f"Warning: This application requires Python 3.8+. You're running {python_version.major}.{python_version.minor}")
        response = input("Would you like to continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Install required packages if not already installed
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies. Please try installing them manually:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    # Create necessary directories
    temp_dir = Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp"))
    temp_dir.mkdir(exist_ok=True)
    print("✓ Temp directory created")
    
    # Create a default .env file if it doesn't exist
    env_file = Path.cwd() / '.env'
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write("""# Cline Web IDE Environment Variables
# Uncomment and fill in the values below

# ANTHROPIC_API_KEY=your_api_key_here
# FIREBASE_PRIVATE_KEY_ID=
# FIREBASE_PRIVATE_KEY=
# FIREBASE_CLIENT_EMAIL=
# FIREBASE_CLIENT_ID=
# FIREBASE_CERT_URL=
""")
        print("✓ Default .env file created")
    
    print("✓ Environment set up successfully!")

def run_app(port=8501, enable_auth=True, debug=False):
    """Run the Streamlit app."""
    if not enable_auth:
        os.environ["DISABLE_AUTH"] = "true"
    
    if debug:
        os.environ["STREAMLIT_DEBUG"] = "true"
    
    # Determine if we're running in development mode
    dev_mode = debug or not enable_auth
    if dev_mode:
        print("⚠️  Running in development mode")
    
    print(f"🚀 Starting Cline Web IDE on http://localhost:{port}")
    
    args = ["streamlit", "run", "app.py", "--server.port", str(port)]
    
    if debug:
        # Add debug flags
        args.extend(["--logger.level", "debug"])
    
    try:
        subprocess.call(args)
    except KeyboardInterrupt:
        print("\n👋 Cline Web IDE stopped")
    except Exception as e:
        print(f"❌ Error running Streamlit app: {str(e)}")
        sys.exit(1)

def open_browser(port=8501, delay=1.5):
    """Open the browser after a short delay."""
    import threading
    import time
    import webbrowser
    
    def _open_browser():
        time.sleep(delay)
        url = f"http://localhost:{port}"
        print(f"🌐 Opening {url} in your browser...")
        webbrowser.open(url)
    
    thread = threading.Thread(target=_open_browser)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Cline Web IDE")
    parser.add_argument("--setup", action="store_true", help="Set up the environment")
    parser.add_argument("--port", type=int, default=8501, help="Port to run the app on")
    parser.add_argument("--no-auth", action="store_true", help="Disable authentication")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_environment()
    
    if not args.no_browser:
        open_browser(port=args.port)
    
    run_app(port=args.port, enable_auth=not args.no_auth, debug=args.debug)
