#!/usr/bin/env python3
"""
Test script for multi-step agency capabilities
"""
import asyncio
import aiohttp
import base64
import json

async def test_multi_step_agency():
    """Test multi-step agency with complex operations"""
    username = "meranda"
    password = "musser"
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    test_messages = [
        "Я чувствую себя очень счастливой сегодня, но хочу понять свои эмоциональные паттерны",
        "Мне грустно, и я хочу посмотреть свою историю эмоций",
        "Проверь мои данные и скажи что ты видишь"
    ]
    
    print(f"🧪 Testing multi-step agency for user: {username}")
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
                    print("📄 Response chunks:")
                    
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                if data['type'] == 'chunk':
                                    print(f"   {data['content']}", end='')
                                elif data['type'] == 'complete':
                                    print("\n✅ Response completed")
                                    break
                            except json.JSONDecodeError:
                                pass
                    
                    await asyncio.sleep(1) # Give time for processing
                    
                    # Check what files were created/modified
                    print("\n📁 Checking file system changes:")
                    
                    # Check profile
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
    asyncio.run(test_multi_step_agency()) 