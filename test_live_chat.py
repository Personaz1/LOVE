#!/usr/bin/env python3
"""
Test script for live chat functionality
Tests multiple message support, login greeting, and tool usage
"""

import requests
import json
import time

def test_login_and_greeting():
    """Test login and automatic greeting"""
    print("🧪 Testing login and greeting...")
    
    # Login
    login_data = {
        'username': 'meranda',
        'password': 'musser'
    }
    
    session = requests.Session()
    response = session.post('http://localhost:8000/login', data=login_data, allow_redirects=False)
    
    if response.status_code == 302:
        print("✅ Login successful")
        
        # Get chat page
        chat_response = session.get('http://localhost:8000/chat')
        if chat_response.status_code == 200:
            print("✅ Chat page loaded")
            
            # Test login greeting endpoint
            greeting_response = session.post('http://localhost:8000/api/login-greeting')
            if greeting_response.status_code == 200:
                print("✅ Login greeting endpoint working")
                return True
            else:
                print(f"❌ Login greeting failed: {greeting_response.status_code}")
                return False
        else:
            print(f"❌ Chat page failed: {chat_response.status_code}")
            return False
    else:
        print(f"❌ Login failed: {response.status_code}")
        return False

def test_streaming_chat():
    """Test streaming chat with multiple messages"""
    print("\n🧪 Testing streaming chat...")
    
    session = requests.Session()
    
    # Login first
    login_data = {
        'username': 'meranda',
        'password': 'musser'
    }
    session.post('http://localhost:8000/login', data=login_data, allow_redirects=False)
    
    # Test streaming message
    message_data = {
        'message': 'Hello! Can you analyze the system and tell me what you find?'
    }
    
    try:
        response = session.post(
            'http://localhost:8000/api/chat/stream',
            data=message_data,
            stream=True
        )
        
        if response.status_code == 200:
            print("✅ Streaming response started")
            
            # Read streaming data
            message_count = 0
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if data.get('type') == 'chunk':
                                print(f"📝 Chunk received: {len(data.get('content', ''))} chars")
                            elif data.get('type') == 'message_complete':
                                message_count += 1
                                print(f"✅ Message {message_count} completed")
                            elif data.get('type') == 'complete':
                                print(f"✅ Streaming completed with {data.get('total_messages', 0)} messages")
                                break
                            elif data.get('type') == 'error':
                                print(f"❌ Error: {data.get('message')}")
                                return False
                        except json.JSONDecodeError:
                            continue
            
            print(f"✅ Streaming test completed with {message_count} messages")
            return True
        else:
            print(f"❌ Streaming failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Streaming error: {e}")
        return False

def test_tool_calls():
    """Test tool calls with named arguments"""
    print("\n🧪 Testing tool calls...")
    
    session = requests.Session()
    
    # Login first
    login_data = {
        'username': 'meranda',
        'password': 'musser'
    }
    session.post('http://localhost:8000/login', data=login_data, allow_redirects=False)
    
    # Test message that should trigger tool calls
    message_data = {
        'message': 'Please read my profile and tell me about my emotional history.'
    }
    
    try:
        response = session.post(
            'http://localhost:8000/api/chat/stream',
            data=message_data,
            stream=True
        )
        
        if response.status_code == 200:
            print("✅ Tool call test started")
            
            # Read streaming data
            tool_calls_found = 0
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if data.get('type') == 'chunk':
                                content = data.get('content', '')
                                if 'read_user_profile' in content or 'read_emotional_history' in content:
                                    tool_calls_found += 1
                                    print(f"🔧 Tool call found: {content[:100]}...")
                            elif data.get('type') == 'complete':
                                break
                        except json.JSONDecodeError:
                            continue
            
            print(f"✅ Tool call test completed with {tool_calls_found} tool calls found")
            return tool_calls_found > 0
        else:
            print(f"❌ Tool call test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Tool call test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Live Chat Tests...")
    print("=" * 50)
    
    tests = [
        ("Login and Greeting", test_login_and_greeting),
        ("Streaming Chat", test_streaming_chat),
        ("Tool Calls", test_tool_calls),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅ PASS' if result else '❌ FAIL'}: {test_name}")
        except Exception as e:
            print(f"❌ ERROR: {test_name} - {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Live chat functionality is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main() 