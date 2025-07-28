#!/usr/bin/env python3

import json
import os
from ai_client import AIClient

def test_guardian_edit():
    """Test if Guardian can edit his own prompt"""
    
    # Initialize AI client
    ai_client = AIClient()
    
    # Test reading current prompt
    print("🔍 Testing read_file for guardian profile...")
    try:
        content = ai_client.read_file("memory/guardian_profile.json")
        print(f"✅ Successfully read guardian profile ({len(content)} chars)")
        
        # Parse JSON
        profile = json.loads(content)
        current_prompt = profile.get("system_prompt", "")
        print(f"📝 Current prompt length: {len(current_prompt)} chars")
        
        # Test editing the prompt
        print("\n🔧 Testing edit_file for guardian profile...")
        
        # Create a modified version
        modified_profile = profile.copy()
        modified_profile["system_prompt"] = current_prompt + "\n\n# TEST: Guardian can edit himself!"
        modified_content = json.dumps(modified_profile, indent=2, ensure_ascii=False)
        
        # Try to edit
        result = ai_client.edit_file("memory/guardian_profile.json", modified_content)
        print(f"✅ Edit result: {result}")
        
        # Verify the change
        print("\n🔍 Verifying the change...")
        new_content = ai_client.read_file("memory/guardian_profile.json")
        new_profile = json.loads(new_content)
        if "TEST: Guardian can edit himself!" in new_profile.get("system_prompt", ""):
            print("✅ Guardian successfully edited his own prompt!")
        else:
            print("❌ Guardian could not edit his own prompt")
            
    except Exception as e:
        print(f"❌ Error testing guardian edit: {e}")

if __name__ == "__main__":
    test_guardian_edit() 