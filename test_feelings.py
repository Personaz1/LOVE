#!/usr/bin/env python3
"""
Test script for feelings detection and profile updates
"""

import asyncio
import aiohttp
import base64
import json

async def test_feelings():
    """Test feelings detection with different messages"""
    
    # Test credentials
    username = "meranda"
    password = "musser"
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    # Test messages that should trigger feeling updates
    test_messages = [
        "седня все классно",
        "мне грустно",
        "я счастлива",
        "чувствую себя плохо",
        "все отлично"
    ]
    
    print(f"🧪 Testing feelings detection for user: {username}")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        for i, message in enumerate(test_messages, 1):
            print(f"\n📝 Test {i}: '{message}'")
            print("-" * 40)
            
            # Prepare form data
            data = aiohttp.FormData()
            data.add_field('message', message)
            
            # Make streaming request
            async with session.post(
                'http://localhost:8000/api/chat/stream',
                data=data,
                headers={
                    'Authorization': f'Basic {credentials}',
                    'Accept': 'text/event-stream',
                    'Cache-Control': 'no-cache'
                }
            ) as response:
                
                if response.status == 200:
                    print("✅ Request successful")
                    
                    # Just consume the stream to trigger processing
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                if data['type'] == 'complete':
                                    break
                            except json.JSONDecodeError:
                                pass
                    
                    # Now check the profile to see if feeling was updated
                    await asyncio.sleep(1)  # Give time for processing
                    
                    profile_response = await session.get(
                        'http://localhost:8000/api/profile',
                        headers={'Authorization': f'Basic {credentials}'}
                    )
                    
                    if profile_response.status == 200:
                        profile = await profile_response.json()
                        current_feeling = profile.get('current_feeling', 'Not set')
                        print(f"💭 Current feeling after message: {current_feeling}")
                    else:
                        print(f"❌ Failed to get profile: {profile_response.status}")
                        
                else:
                    print(f"❌ Request failed: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_feelings()) 