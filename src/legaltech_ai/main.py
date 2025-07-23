#!/usr/bin/env python3

import os
import subprocess
import sys
from dotenv import load_dotenv

def main():
    """Simple entry point to run the Streamlit app."""
    
    # Load environment variables
    load_dotenv()
    
    # Check if required environment variables are set
    required_vars = ['WATSONX_API_KEY', 'WATSONX_URL', 'WATSONX_PROJECT_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        sys.exit(1)
    
    print("Starting LegalTech AI application...")
    
    # Get port from environment or use default
    port = os.getenv('PORT', '8080')
    
    # Run Streamlit app
    try:
        subprocess.run([
            'streamlit', 'run', 
            'src/legaltech_ai/ui/streamlit_app.py',
            '--server.port', port,
            '--server.address', '0.0.0.0'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()