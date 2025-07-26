#!/usr/bin/env python3
"""
Complete test of multi-step agency capabilities
"""
import asyncio
import aiohttp
import base64
import json

async def test_complete_agency():
    """Test complete multi-step agency workflow"""
    username = "meranda"
    password = "musser"
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    print(f"🧪 Testing complete multi-step agency for user: {username}")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Complex emotional analysis
        print("\n📝 Test 1: Complex emotional analysis")
        print("-" * 40)
        
        message = "Я чувствую себя очень счастливой сегодня, но хочу понять свои эмоциональные паттерны за последнее время"
        
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
                print("📄 Response:")
                
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if data['type'] == 'chunk':
                                print(f"{data['content']}", end='')
                            elif data['type'] == 'complete':
                                print("\n✅ Response completed")
                                break
                        except json.JSONDecodeError:
                            pass
                
                await asyncio.sleep(1)
                
                # Check results
                profile_response = await session.get(
                    'http://localhost:8000/api/profile',
                    headers={'Authorization': f'Basic {credentials}'}
                )
                
                if profile_response.status == 200:
                    profile = await profile_response.json()
                    current_feeling = profile.get('current_feeling', 'Not set')
                    emotional_history = profile.get('emotional_history', [])
                    emotional_trends = profile.get('emotional_trends', {})
                    
                    print(f"\n📊 Results:")
                    print(f"💭 Current feeling: {current_feeling}")
                    print(f"📈 Total emotion entries: {emotional_trends.get('total_entries', 0)}")
                    print(f"📊 Emotional trend: {emotional_trends.get('trend', 'Unknown')}")
                    
                    if emotional_history:
                        print(f"🕒 Recent emotions:")
                        for entry in emotional_history[-3:]:  # Last 3 entries
                            print(f"   - {entry.get('date', 'Unknown')} {entry.get('time', '')}: {entry.get('feeling', 'Unknown')} (was: {entry.get('previous_feeling', 'Unknown')})")
                            print(f"     Context: {entry.get('context', 'No context')}")
        
        # Test 2: File system operations
        print("\n📝 Test 2: File system operations")
        print("-" * 40)
        
        message = "Проверь мои файлы данных и скажи что ты видишь"
        
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
                print("📄 Response:")
                
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if data['type'] == 'chunk':
                                print(f"{data['content']}", end='')
                            elif data['type'] == 'complete':
                                print("\n✅ Response completed")
                                break
                        except json.JSONDecodeError:
                            pass
        
        # Test 3: Multi-step insight generation
        print("\n📝 Test 3: Multi-step insight generation")
        print("-" * 40)
        
        message = "Проанализируй мои эмоции и создай инсайт о моих паттернах"
        
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
                print("📄 Response:")
                
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if data['type'] == 'chunk':
                                print(f"{data['content']}", end='')
                            elif data['type'] == 'complete':
                                print("\n✅ Response completed")
                                break
                        except json.JSONDecodeError:
                            pass

if __name__ == "__main__":
    asyncio.run(test_complete_agency()) 