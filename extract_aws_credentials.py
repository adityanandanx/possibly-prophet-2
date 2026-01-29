#!/usr/bin/env python3
"""
AWS Bearer Token Credential Extractor

This script helps extract AWS credentials from a bearer token URL.
The bearer token you provided appears to be a pre-signed URL with embedded credentials.
"""

import urllib.parse
import base64
import re

def extract_credentials_from_bearer_token(bearer_token):
    """
    Extract AWS credentials from a bearer token URL
    """
    print("🔍 Analyzing bearer token...")
    
    # The token appears to be base64 encoded, let's try to decode it
    try:
        # Remove the prefix if present
        if bearer_token.startswith('ABSKQmVkcm9ja0FQSUtleS1lbXV1LWF0LTQ2ODYyOTc1MzMzNjpx'):
            # This looks like a base64 encoded string
            decoded = base64.b64decode(bearer_token)
            print(f"Decoded token: {decoded}")
            
        # Look for URL patterns in the original token
        if 'bedrock.amazonaws.com' in bearer_token:
            # Parse as URL
            parsed = urllib.parse.urlparse(bearer_token)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            print("Found URL parameters:")
            for key, value in query_params.items():
                print(f"  {key}: {value[0] if value else 'None'}")
                
        # Look for AWS credential patterns
        access_key_match = re.search(r'ASIA[A-Z0-9]{16}', bearer_token)
        if access_key_match:
            access_key = access_key_match.group()
            print(f"✅ Found Access Key: {access_key}")
            
            # The bearer token format suggests these are temporary credentials
            # You'll need to extract the secret key and session token manually
            print("\n📋 To use AWS Bedrock, you need to set these environment variables:")
            print(f"AWS_ACCESS_KEY_ID={access_key}")
            print("AWS_SECRET_ACCESS_KEY=<extract_from_token>")
            print("AWS_SESSION_TOKEN=<extract_from_token>")
            print("AWS_DEFAULT_REGION=eu-north-1")
            
            return access_key
            
    except Exception as e:
        print(f"❌ Error processing token: {e}")
    
    print("\n💡 Alternative Solutions:")
    print("1. Use AWS CLI: aws configure")
    print("2. Contact your AWS administrator for standard credentials")
    print("3. Use a different AI provider (Anthropic, OpenAI, Google)")
    
    return None

def main():
    print("🔑 AWS Credential Extractor for Educational Content Generator")
    print("=" * 60)
    
    # Read the bearer token from environment
    import os
    bearer_token = os.getenv("AWS_BEARER_TOKEN_BEDROCK")
    
    if not bearer_token:
        print("❌ No AWS_BEARER_TOKEN_BEDROCK found in environment")
        print("Make sure you have set the token in your .env file")
        return
    
    print(f"📄 Token length: {len(bearer_token)} characters")
    print(f"📄 Token preview: {bearer_token[:50]}...")
    
    # Try to extract credentials
    access_key = extract_credentials_from_bearer_token(bearer_token)
    
    if access_key:
        print(f"\n✅ Found AWS Access Key: {access_key}")
        print("\n🚀 Next Steps:")
        print("1. Extract the secret key and session token from your bearer token")
        print("2. Add them to your .env file:")
        print(f"   AWS_ACCESS_KEY_ID={access_key}")
        print("   AWS_SECRET_ACCESS_KEY=your_secret_key")
        print("   AWS_SESSION_TOKEN=your_session_token")
        print("   AWS_DEFAULT_REGION=eu-north-1")
        print("3. Remove the AWS_BEARER_TOKEN_BEDROCK line")
        print("4. Test with: uv run python test_mvp_demo.py")
    else:
        print("\n❌ Could not extract credentials from bearer token")
        print("\n🔄 Recommended Alternative:")
        print("Use Anthropic Claude instead (easier setup):")
        print("1. Get free API key: https://console.anthropic.com/")
        print("2. Add to .env: ANTHROPIC_API_KEY=your_key_here")
        print("3. Remove AWS_BEARER_TOKEN_BEDROCK line")
        print("4. Test with: uv run python test_mvp_demo.py")

if __name__ == "__main__":
    main()