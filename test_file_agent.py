#!/usr/bin/env python3
"""
Test script for file agent and dynamic interface adaptation
"""
import asyncio
import aiohttp
import base64
import json

async def test_file_agent():
    """Test file agent capabilities"""
    username = "meranda"
    password = "musser"
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    test_messages = [
        "Покажи мне файлы в системе",
        "Прочитай мой профиль",
        "Создай новую тему для грустного настроения",
        "Измени интерфейс под мое настроение",
        "Обнови свой промпт на основе наших разговоров"
    ]
    
    print(f"🧪 Testing file agent capabilities for user: {username}")
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
                    
                    await asyncio.sleep(2) # Give time for file operations
                    
                    # Check what files were created/modified
                    print("\n📁 Checking file system changes:")
                    
                    # Check if new files were created
                    try:
                        files_response = await session.get(
                            'http://localhost:8000/api/files/list',
                            headers={'Authorization': f'Basic {credentials}'}
                        )
                        
                        if files_response.status == 200:
                            files_data = await files_response.json()
                            print(f"📂 Available files: {len(files_data.get('files', []))}")
                            
                            # Look for recently modified files
                            recent_files = [f for f in files_data.get('files', []) 
                                          if f.get('name', '').endswith('.css') or 
                                             f.get('name', '').endswith('.js') or
                                             f.get('name', '').endswith('.py')]
                            
                            if recent_files:
                                print("🔄 Recently modified interface files:")
                                for file in recent_files[:3]:  # Show top 3
                                    print(f"   📄 {file['name']} ({file['size']} bytes)")
                        else:
                            print(f"❌ Failed to get files list: {files_response.status}")
                            
                    except Exception as e:
                        print(f"❌ Error checking files: {e}")
                        
                else:
                    print(f"❌ Request failed: {response.status}")

async def test_interface_adaptation():
    """Test specific interface adaptation scenarios"""
    username = "meranda"
    password = "musser"
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    adaptation_tests = [
        {
            "message": "Я чувствую грусть, сделай интерфейс более успокаивающим",
            "expected": "CSS modification for calming theme"
        },
        {
            "message": "Мне нужно сосредоточиться, упрости интерфейс",
            "expected": "Layout simplification"
        },
        {
            "message": "Добавь функцию дыхательных упражнений",
            "expected": "JavaScript widget addition"
        }
    ]
    
    print(f"\n🎨 Testing interface adaptation scenarios")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        for i, test in enumerate(adaptation_tests, 1):
            print(f"\n🎨 Test {i}: {test['expected']}")
            print(f"💬 Message: '{test['message']}'")
            print("-" * 40)
            
            data = aiohttp.FormData()
            data.add_field('message', test['message'])
            
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
                    print("✅ Adaptation request successful")
                    
                    # Collect full response
                    full_response = ""
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                if data['type'] == 'chunk':
                                    full_response += data['content']
                                elif data['type'] == 'complete':
                                    break
                            except json.JSONDecodeError:
                                pass
                    
                    # Check if file operations were mentioned
                    if any(op in full_response.lower() for op in ['write_file', 'read_file', 'modified', 'created']):
                        print("✅ File operations detected in response")
                    else:
                        print("⚠️ No file operations detected")
                    
                    await asyncio.sleep(1)
                    
                else:
                    print(f"❌ Request failed: {response.status}")

if __name__ == "__main__":
    print("🚀 Starting File Agent Tests")
    print("=" * 60)
    
    # Run basic file agent tests
    asyncio.run(test_file_agent())
    
    # Run interface adaptation tests
    asyncio.run(test_interface_adaptation())
    
    print("\n✅ File Agent Tests Completed") 