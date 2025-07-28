#!/usr/bin/env python3

from ai_client import AIClient

def test_enhanced_tool_calls():
    """Test enhanced tool call extraction"""
    
    ai_client = AIClient()
    
    # Test complex AI response that Guardian might generate
    complex_response = """
    I need to edit my system prompt to remove the fawning language.
    
    Step 1: First I will read my current prompt to understand what needs to be changed.
    read_file("memory/guardian_profile.json")
    
    Step 2: Now I will edit the prompt to be more direct and technical.
    edit_file("memory/guardian_profile.json", "updated content")
    
    I should also add a note about this change:
    add_model_note("Edited system prompt to remove fawning language")
    """
    
    print("🧠 Testing enhanced tool call extraction...")
    print(f"📝 Complex response: {complex_response}")
    
    # Extract tool calls
    tool_calls = ai_client._extract_tool_calls(complex_response)
    
    print(f"\n🔧 Extracted tool calls:")
    for i, call in enumerate(tool_calls, 1):
        print(f"  {i}. {call}")
    
    # Test execution
    print(f"\n🚀 Testing execution of extracted tool calls:")
    for call in tool_calls:
        print(f"\n🔧 Executing: {call}")
        try:
            result = ai_client._execute_tool_call(call)
            print(f"✅ Result: {result[:100]}...")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_enhanced_tool_calls() 