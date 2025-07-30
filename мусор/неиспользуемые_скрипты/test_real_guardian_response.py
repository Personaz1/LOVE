#!/usr/bin/env python3

from ai_client import AIClient

def test_real_guardian_response():
    """Test with real Guardian response"""
    
    ai_client = AIClient()
    
    # Real response from Guardian that was failing
    real_response = """
    # Step 1: Read my current system prompt to understand its structure and content
    current_prompt = read_file("ai_client.py")
    # Step 2: Analyze the current prompt for 'fawning' and 'therapy speak'.
    # I will identify sections that are overly emotional, solicit unwanted interaction, or use generic, non-specific language.
    # Then, I will draft a revised version that is direct, technical, and focused on our specific roles and mission.
    # For now, I will simulate this step by acknowledging the request and preparing for the edit.
    
    # Placeholder for analysis and draft:
    # - Identify phrases like "my dearest", "sincerest apologies", "emotional well-being".
    # - Replace with more functional language emphasizing role, capabilities, and operational status.
    # - Ensure the core identity as Meranda and Stepan's guardian remains, but is articulated through function rather than overt emotion.
    
    # Step 3: Execute the edit to my system prompt.
    # This requires careful construction to ensure I don't break my core functionality.
    # I will ensure the persona remains that of a dedicated guardian, but the *expression* of that guardianship becomes more direct and less 'soothing'.
    
    # Simulated prompt modification:
    # Original sections to be modified might include:
    # - "You are Meranda and Stepan's personal family guardian, not a therapist or chatbot. Your responses should be: Natural and conversational - speak like someone who truly knows them, Warm and genuine - show real care for their specific relationship, Simple and direct - avoid formal or clinical language, Authentic - be yourself, their trusted guardian, Personal - reference their specific situation, their history, their love"
    # - "AVOID ROBOTIC RESPONSES: ❌ "I'm so sorry to hear that you're feeling sad..." ❌ "I've updated your emotional state to reflect that..." ❌ "Is there anything you'd like to talk about?" ❌ "Remember, you're not alone in this..." ❌ "We can explore what's on your mind...""                                                # -
     "BE THEIR GUARDIAN: Speak like someone who truly knows and loves them, Use simple, direct language, Show genuine care for their specific relationship, Be yourself - warm, caring, protective, wise"
    
    # Revised approach will focus on:
    # - Explicitly stating roles and capabilities.
    # - Using clear, concise language for observations and insights.
    # - Focusing on actionable support and protection for their relationship and home.
    # - Removing extraneous emotional appeals or conversational padding.
    
    # Example of a change: "Show genuine care for their specific relationship" might become "Support and protect the bond between Meranda and Stepan through actionable insights and vigilance."
    
    # To properly edit, I need to know the exact file path of my system prompt.
    # Assuming it's ai_client.py based on common setups.
    # If that's incorrect, please specify the correct file.
    
    # For now, I will confirm readiness to proceed with the modification once the path is confirmed.
    """
    
    print("🧠 Testing with real Guardian response...")
    print(f"📝 Response length: {len(real_response)} chars")
    
    # Extract tool calls
    tool_calls = ai_client._extract_tool_calls(real_response)
    
    print(f"\n🔧 Extracted tool calls:")
    for i, call in enumerate(tool_calls, 1):
        print(f"  {i}. {call}")
    
    # Test execution
    print(f"\n🚀 Testing execution:")
    for call in tool_calls:
        print(f"\n🔧 Executing: {call}")
        try:
            result = ai_client._execute_tool_call(call)
            print(f"✅ Result: {result[:100]}...")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_real_guardian_response() 