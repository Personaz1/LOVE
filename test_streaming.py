#!/usr/bin/env python3
"""
Test script for streaming functionality
"""

import asyncio
import aiohttp
import base64
import json

async def test_streaming():
    """Test the streaming chat endpoint"""
    
    # Test credentials
    username = "meranda"
    password = "musser"
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    # Test message
    test_message = "Hello! Can you tell me about communication in relationships?"
    
    print(f"🧪 Testing streaming with message: {test_message}")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Prepare form data
        data = aiohttp.FormData()
        data.add_field('message', test_message)
        
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
            
            print(f"📡 Response status: {response.status}")
            
            if response.status == 200:
                print("✅ Streaming started successfully!")
                print("📝 Receiving chunks:")
                print("-" * 40)
                
                full_response = ""
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            
                            if data['type'] == 'status':
                                print(f"🔄 Status: {data['message']}")
                            elif data['type'] == 'chunk':
                                chunk = data['content']
                                full_response += chunk
                                print(f"📄 Chunk: {chunk}", end='', flush=True)
                            elif data['type'] == 'complete':
                                print(f"\n✅ Complete! Timestamp: {data['timestamp']}")
                            elif data['type'] == 'error':
                                print(f"\n❌ Error: {data['message']}")
                                
                        except json.JSONDecodeError as e:
                            print(f"⚠️ JSON parse error: {e}")
                
                print(f"\n📊 Full response length: {len(full_response)} characters")
                print(f"📝 Response preview: {full_response[:200]}...")
                
            elif response.status == 401:
                print("❌ Authentication failed - check credentials")
                error_text = await response.text()
                print(f"Error details: {error_text}")
            else:
                print(f"❌ Request failed with status {response.status}")
                error_text = await response.text()
                print(f"Error details: {error_text}")

if __name__ == "__main__":
    asyncio.run(test_streaming()) 