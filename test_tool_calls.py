#!/usr/bin/env python3

from ai_client import AIClient

def test_tool_calls():
    """Test tool call execution"""
    
    ai_client = AIClient()
    
    # Test various tool calls
    test_calls = [
        "read_file(\"memory/guardian_profile.json\")",
        "add_model_note(\"Test note from tool call\")",
        "edit_file(\"test_file.txt\", \"Test content\")",
        "delete_file(\"test_file.txt\")"
    ]
    
    for tool_call in test_calls:
        print(f"\n🔧 Testing: {tool_call}")
        try:
            result = ai_client._execute_tool_call(tool_call)
            print(f"✅ Result: {result[:100]}...")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_tool_calls() 