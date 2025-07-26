#!/usr/bin/env python3
"""
Test script for multi-step reasoning with tool calling
"""

import asyncio
import json
from ai_client import AIClient
from prompts.psychologist_prompt import AI_GUARDIAN_SYSTEM_PROMPT

async def test_multi_step_reasoning():
    """Test the new multi-step reasoning architecture"""
    
    print("🧪 Testing Multi-Step Reasoning Architecture")
    print("=" * 50)
    
    # Initialize AI client
    client = AIClient()
    
    # Test cases
    test_cases = [
        {
            "message": "привет, как дела?",
            "description": "Basic greeting - should update feeling"
        },
        {
            "message": "расскажи мне про твои инструменты",
            "description": "Tool inquiry - should explain available tools"
        },
        {
            "message": "я чувствую себя счастливой сегодня",
            "description": "Emotional expression - should update feeling"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['description']}")
        print(f"📝 User message: {test_case['message']}")
        print("-" * 40)
        
        try:
            # Generate response
            response_chunks = []
            async for chunk in client.generate_streaming_response(
                AI_GUARDIAN_SYSTEM_PROMPT,
                test_case['message'],
                context="Test conversation",
                user_profile={"username": "meranda", "current_feeling": "Neutral"}
            ):
                response_chunks.append(chunk)
                print(chunk, end="", flush=True)
            
            full_response = "".join(response_chunks)
            print(f"\n\n✅ Test {i} completed successfully")
            
        except Exception as e:
            print(f"\n❌ Test {i} failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Multi-step reasoning test completed!")

if __name__ == "__main__":
    asyncio.run(test_multi_step_reasoning()) 