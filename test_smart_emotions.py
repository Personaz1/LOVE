#!/usr/bin/env python3
"""
Test script for smart emotion detection system
"""
import asyncio
import aiohttp
import base64
import json

async def test_smart_emotions():
    """Test smart emotion detection with different messages"""
    username = "meranda"
    password = "musser"
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    test_messages = [
        "сегодня я очень счастлива, все идет отлично",
        "чувствую себя грустно, не знаю что делать",
        "немного тревожно, но в целом нормально",
        "я в восторге от нашего разговора",
        "чувствую себя одиноко"
    ]
    
    print(f"🧪 Testing smart emotion detection for user: {username}")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        for i, message in enumerate(test_messages, 1):
            print(f"\n📝 Test {i}: '{message}'")
            print("-" * 40)
            
            data = aiohttp.FormData()
            data.add_field('message', message)
            
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
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                if data['type'] == 'complete':
                                    break
                            except json.JSONDecodeError:
                                pass
                    
                    await asyncio.sleep(1) # Give time for processing
                    
                    # Check profile for emotion update
                    profile_response = await session.get(
                        'http://localhost:8000/api/profile',
                        headers={'Authorization': f'Basic {credentials}'}
                    )
                    
                    if profile_response.status == 200:
                        profile = await profile_response.json()
                        current_feeling = profile.get('current_feeling', 'Not set')
                        emotional_history = profile.get('emotional_history', [])
                        emotional_trends = profile.get('emotional_trends', {})
                        
                        print(f"💭 Current feeling: {current_feeling}")
                        print(f"📊 Emotional trend: {emotional_trends.get('trend', 'Unknown')}")
                        print(f"📈 Total emotion entries: {emotional_trends.get('total_entries', 0)}")
                        
                        if emotional_history:
                            latest = emotional_history[-1]
                            print(f"🕒 Latest emotion: {latest.get('feeling', 'Unknown')} at {latest.get('time', 'Unknown')}")
                            print(f"📝 Context: {latest.get('context', 'No context')}")
                            
                    else:
                        print(f"❌ Failed to get profile: {profile_response.status}")
                        
                else:
                    print(f"❌ Request failed: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_smart_emotions()) 