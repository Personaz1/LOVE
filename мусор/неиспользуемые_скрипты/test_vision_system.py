#!/usr/bin/env python3
"""
Test script for the new vision system
"""

import os
import sys
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vision_system():
    """Test the new vision system"""
    try:
        from ai_client import AIClient
        
        # Initialize AI client
        ai_client = AIClient()
        
        # Test model status
        status = ai_client.get_model_status()
        print("=== Model Status ===")
        print(f"Current model: {status['current_model']}")
        print(f"Vision client available: {status['vision_client_available']}")
        print(f"Available models:")
        for model in status['available_models']:
            print(f"  - {model['name']} (vision: {model['vision']}, quota: {model['quota']})")
        
        # Test with a sample image if available
        test_image_path = "static/images/logo_small.png"
        if os.path.exists(test_image_path):
            print(f"\n=== Testing Image Analysis ===")
            print(f"Testing with: {test_image_path}")
            
            result = ai_client.analyze_image(test_image_path, "Test context")
            print(f"Analysis result: {result[:200]}...")
        else:
            print(f"\n⚠️ Test image not found: {test_image_path}")
            print("Create a test image to verify vision functionality")
        
        print("\n✅ Vision system test completed")
        
    except Exception as e:
        logger.error(f"❌ Vision system test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_vision_system()
    sys.exit(0 if success else 1) 