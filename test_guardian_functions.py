#!/usr/bin/env python3
"""
Test script for ΔΣ Guardian functions
Tests all new capabilities: ReAct, Web Access, Vector Memory, Task Planning
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_client import AIClient

def test_react_architecture():
    """Test ReAct architecture functions"""
    print("🧠 Testing ReAct Architecture...")
    
    ai = AIClient()
    
    # Test planning
    plan = ai.plan_step("diagnose system issues")
    print(f"📋 Plan: {plan[:100]}...")
    
    # Test action
    action = ai.act_step("diagnose_system_health", "")
    print(f"🔧 Action: {action[:100]}...")
    
    # Test reflection
    reflection = ai.reflect(["Step 1: Diagnosed system health", "Step 2: Found no issues"])
    print(f"🤔 Reflection: {reflection[:100]}...")
    
    print("✅ ReAct Architecture tests completed\n")

def test_web_access():
    """Test web access functions"""
    print("🌐 Testing Web Access...")
    
    ai = AIClient()
    
    # Test web search
    search_result = ai.web_search("latest AI developments")
    print(f"🔍 Web search: {search_result[:100]}...")
    
    # Test URL fetch
    fetch_result = ai.fetch_url("https://httpbin.org/json")
    print(f"📄 URL fetch: {fetch_result[:100]}...")
    
    # Test translation
    translation = ai.translate_text("Hello world", "ru")
    print(f"🌍 Translation: {translation[:100]}...")
    
    print("✅ Web Access tests completed\n")

def test_vector_memory():
    """Test vector memory functions"""
    print("🧠 Testing Vector Memory...")
    
    ai = AIClient()
    
    # Test storing embeddings
    store_result = ai.store_embedding_memory("User prefers technical discussions", "user_preference")
    print(f"💾 Store embedding: {store_result}")
    
    store_result2 = ai.store_embedding_memory("System diagnostics show good health", "system_status")
    print(f"💾 Store embedding 2: {store_result2}")
    
    # Test searching
    search_result = ai.search_embedding_memory("technical issues", 3)
    print(f"🔍 Vector search: {search_result[:200]}...")
    
    # Test statistics
    stats = ai.get_memory_stats()
    print(f"📊 Memory stats: {stats}")
    
    print("✅ Vector Memory tests completed\n")

def test_task_planning():
    """Test task planning functions"""
    print("📅 Testing Task Planning...")
    
    ai = AIClient()
    
    # Test creating events
    event_result = ai.create_event("Test Meeting", "Testing Guardian functions", "2025-08-02", "15:00", "high")
    print(f"📅 Create event: {event_result}")
    
    event_result2 = ai.create_event("Weekend Plans", "Family activities", "2025-08-03", "10:00", "medium")
    print(f"📅 Create event 2: {event_result2}")
    
    # Test getting upcoming events
    upcoming = ai.get_upcoming_events(7)
    print(f"📋 Upcoming events: {upcoming[:200]}...")
    
    # Test statistics
    stats = ai.get_event_statistics()
    print(f"📊 Event stats: {stats}")
    
    # Test task list creation
    tasks = "Buy groceries\nClean house\nCall parents\nTest Guardian"
    task_list = ai.create_task_list("Test Tasks", tasks)
    print(f"📝 Task list: {task_list}")
    
    print("✅ Task Planning tests completed\n")

def test_system_health():
    """Test system health and diagnostics"""
    print("🏥 Testing System Health...")
    
    ai = AIClient()
    
    # Test system health
    health = ai.diagnose_system_health()
    print(f"🏥 System health: {health[:200]}...")
    
    # Test system logs
    logs = ai.get_system_logs(10)
    print(f"📋 System logs: {logs[:200]}...")
    
    print("✅ System Health tests completed\n")

def main():
    """Run all tests"""
    print("🚀 Starting ΔΣ Guardian Function Tests\n")
    
    try:
        test_react_architecture()
        test_web_access()
        test_vector_memory()
        test_task_planning()
        test_system_health()
        
        print("🎉 All tests completed successfully!")
        print("✅ Guardian is ready with all modern AI capabilities!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 