#!/usr/bin/env python3
"""
Generate Secure Production Secrets for RWA-Studio

This script generates cryptographically secure secrets for production deployment.
Run this script and copy the output to your .env file.

Usage:
    python generate_secrets.py
    python generate_secrets.py --json  # Output as JSON
"""

import secrets
import argparse
import json
import sys


def generate_hex_secret(length: int = 32) -> str:
    """Generate a cryptographically secure hex string."""
    return secrets.token_hex(length)


def generate_url_safe_secret(length: int = 32) -> str:
    """Generate a URL-safe base64-encoded secret."""
    return secrets.token_urlsafe(length)


def main():
    parser = argparse.ArgumentParser(
        description='Generate secure secrets for RWA-Studio production deployment'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output secrets as JSON'
    )
    parser.add_argument(
        '--env',
        action='store_true',
        help='Output as .env file format (default)'
    )
    
    args = parser.parse_args()
    
    # Generate all required secrets
    secrets_dict = {
        'SECRET_KEY': generate_hex_secret(32),
        'JWT_SECRET_KEY': generate_hex_secret(32),
        'ONFIDO_WEBHOOK_SECRET': generate_url_safe_secret(32),
        'STRIPE_WEBHOOK_SECRET': f'whsec_{generate_url_safe_secret(32)}',
    }
    
    if args.json:
        print(json.dumps(secrets_dict, indent=2))
    else:
        print("=" * 60)
        print("RWA-Studio Production Secrets")
        print("=" * 60)
        print()
        print("# Copy these to your backend .env file:")
        print()
        for key, value in secrets_dict.items():
            print(f"{key}={value}")
        print()
        print("=" * 60)
        print("SECURITY REMINDERS:")
        print("=" * 60)
        print("1. Never commit these secrets to version control")
        print("2. Use different secrets for each environment")
        print("3. Store secrets securely (e.g., AWS Secrets Manager, Vault)")
        print("4. Rotate secrets periodically")
        print()
        print("For database password, generate separately:")
        print(f"  DB_PASSWORD={generate_url_safe_secret(24)}")
        print()
        print("For Redis password (if using authentication):")
        print(f"  REDIS_PASSWORD={generate_url_safe_secret(24)}")


if __name__ == '__main__':
    main()
