#!/usr/bin/env python3
"""
Secret Key Generator for EchoMap

This script generates a secure random secret key for use in Flask applications.
Run this script to generate a new secret key that can be used in your .env file.
"""

import os
import base64
import secrets

def generate_secret_key(length=32):
    """Generate a secure random key of specified length."""
    return secrets.token_hex(length)

def generate_key_as_bytes(length=32):
    """Generate a secure random key as a byte string."""
    random_bytes = os.urandom(length)
    return base64.b64encode(random_bytes).decode('utf-8')

if __name__ == "__main__":
    # Generate hex string secret (most common for Flask)
    hex_secret = generate_secret_key()
    
    # Generate URL-safe base64 encoded secret (alternative option)
    b64_secret = generate_key_as_bytes()
    
    # Print with clear formatting
    print("\n=================================================")
    print("EchoMap Secret Key Generator")
    print("=================================================\n")
    
    print("Option 1: Flask SECRET_KEY (hex format):")
    print(f"SECRET_KEY={hex_secret}\n")
    
    print("Option 2: Alternative SECRET_KEY (base64 format):")
    print(f"SECRET_KEY={b64_secret}\n")
    
    print("Instructions:")
    print("1. Copy one of these keys")
    print("2. Paste it into your .env file")
    print("3. Keep this key secure and never commit it to version control\n")
    
    # Write to a temporary file as backup
    try:
        with open("secret_key_temp.txt", "w") as f:
            f.write(f"Hex format: SECRET_KEY={hex_secret}\n")
            f.write(f"Base64 format: SECRET_KEY={b64_secret}\n")
        print("Secret keys have also been saved to secret_key_temp.txt as backup")
        print("Please delete this file after copying your key!\n")
    except:
        # If we can't write to file, it's not critical
        pass