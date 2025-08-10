#!/usr/bin/env python3
"""
Test script for JiMeng configuration
"""
import os
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from open_webui.config import (
    JIMENG_ENABLED,
    JIMENG_API_URL,
    JIMENG_API_KEY,
    JIMENG_CREDITS_5S,
    JIMENG_CREDITS_10S,
)


def test_jimeng_config():
    """Test if JiMeng configuration can be loaded"""
    print("Testing JiMeng Configuration Loading...")
    print(f"JIMENG_ENABLED: {JIMENG_ENABLED.value}")
    print(f"JIMENG_API_URL: {JIMENG_API_URL.value}")
    api_key_value = JIMENG_API_KEY.value
    print(f"JIMENG_API_KEY: {'*' * len(api_key_value) if api_key_value else 'Not set'}")
    print(f"JIMENG_CREDITS_5S: {JIMENG_CREDITS_5S.value}")
    print(f"JIMENG_CREDITS_10S: {JIMENG_CREDITS_10S.value}")

    # Test if the router can be imported
    try:
        from open_webui.routers import jimeng

        print("\n✓ JiMeng router imported successfully")

        # Check router configuration
        print("\nRouter endpoints:")
        for route in jimeng.router.routes:
            if hasattr(route, "path"):
                print(f"  {route.methods} {route.path}")
    except Exception as e:
        print(f"\n✗ Error importing JiMeng router: {e}")
        return False

    print("\n✓ JiMeng configuration test passed!")
    return True


if __name__ == "__main__":
    test_jimeng_config()
