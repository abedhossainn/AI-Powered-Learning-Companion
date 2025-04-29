import firebase_admin
from firebase_admin import credentials, auth
import os
import json
from .config import settings
import traceback

# Initialize Firebase Admin SDK
def initialize_firebase():
    try:
        # Get the correct absolute path to the service account file
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        service_account_path = os.path.join(base_dir, 'firebase-service-account.json')
        
        print(f"Attempting to initialize Firebase Admin SDK with service account at: {service_account_path}")
        
        # Check if the file exists and log the result
        if os.path.exists(service_account_path):
            print(f"Firebase service account file exists: {service_account_path}")
            # Get file permissions and size for debugging
            file_stat = os.stat(service_account_path)
            print(f"File permissions: {oct(file_stat.st_mode)}, Size: {file_stat.st_size} bytes")
            
            # Check file is readable
            with open(service_account_path, 'r') as f:
                first_chars = f.read(20)
                print(f"Successfully read the first 20 chars of the file: {first_chars}...")
        else:
            print(f"ERROR: Firebase service account file NOT FOUND at: {service_account_path}")
            # Try to find it in other locations
            print(f"Current working directory: {os.getcwd()}")
            print(f"Looking for service account file in other directories...")
            
            # Try a few other possible locations
            alt_paths = [
                '/webapps/ai-learning-companion/AI-Powered-Learning-Companion/backend/firebase-service-account.json',
                os.path.join(os.getcwd(), 'firebase-service-account.json'),
                '/etc/firebase-service-account.json'
            ]
            
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    print(f"Found alternative service account file at: {alt_path}")
                    service_account_path = alt_path
                    break
            else:
                print("Could not find Firebase service account file in any expected location")
        
        # First try with environment variable if available
        if settings.FIREBASE_CREDENTIALS_JSON:
            print("Using Firebase credentials from environment variable")
            cred = credentials.Certificate(json.loads(settings.FIREBASE_CREDENTIALS_JSON))
        else:
            # Then try with the service account file
            print(f"Using Firebase credentials from file: {service_account_path}")
            cred = credentials.Certificate(service_account_path)
        
        # Initialize the Firebase Admin SDK
        firebase_app = firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK initialized successfully")
        return firebase_app
    except Exception as e:
        print(f"❌ Error initializing Firebase Admin SDK: {str(e)}")
        print(f"Stack trace: {traceback.format_exc()}")
        return None

# Global Firebase app instance
firebase_app = initialize_firebase()

# Verify Firebase ID token
def verify_firebase_token(id_token):
    try:
        if not firebase_app:
            print("Firebase Admin SDK not initialized, cannot verify token")
            return None
            
        decoded_token = auth.verify_id_token(id_token)
        print(f"✅ Successfully verified Firebase token for user: {decoded_token.get('email')}")
        return decoded_token
    except Exception as e:
        print(f"❌ Error verifying Firebase token: {str(e)}")
        print(f"Stack trace: {traceback.format_exc()}")
        return None