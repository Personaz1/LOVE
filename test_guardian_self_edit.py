#!/usr/bin/env python3

import asyncio
from ai_client import AIClient

async def test_guardian_self_edit():
    """Test if Guardian can edit his own prompt through AI request"""
    
    ai_client = AIClient()
    
    # Test message that should trigger Guardian to edit his prompt
    test_message = "Please edit your own system prompt to remove all the fawning and therapy speak. Make it more direct and technical."
    
    print(f"🧠 Testing Guardian with message: {test_message}")
    
    try:
        # Get current guardian profile
        from memory.guardian_profile import guardian_profile
        current_prompt = guardian_profile.get_profile().get("system_prompt", "")
        print(f"📝 Current prompt length: {len(current_prompt)} chars")
        
        # Test the AI response
        print("\n🤖 Testing AI response...")
        
        # This would normally be done through the streaming response
        # For testing, we'll simulate the tool call extraction
        response = ai_client.chat(
            message=test_message,
            user_profile={"username": "stepan"},
            system_prompt=current_prompt
        )
        
        print(f"✅ AI Response: {response[:200]}...")
        
        # Check if Guardian tried to edit his prompt
        print("\n🔍 Checking if Guardian tried to edit his prompt...")
        
        # Read the current prompt to see if it changed
        from memory.guardian_profile import guardian_profile
        new_prompt = guardian_profile.get_profile().get("system_prompt", "")
        
        if len(new_prompt) != len(current_prompt):
            print("✅ Guardian successfully edited his prompt!")
            print(f"📊 Prompt length changed: {len(current_prompt)} -> {len(new_prompt)}")
        else:
            print("❌ Guardian did not edit his prompt")
            
    except Exception as e:
        print(f"❌ Error testing Guardian self-edit: {e}")

if __name__ == "__main__":
    asyncio.run(test_guardian_self_edit()) 