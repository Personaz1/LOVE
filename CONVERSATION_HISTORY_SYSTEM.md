# 💬 Conversation History & Archiving System

## 🎯 Overview

**Dynamic conversation management** with intelligent archiving and context preservation.

### **Key Features:**
- ✅ **Dynamic greetings** - No more hardcoded welcome messages
- ✅ **Conversation history** - Persistent chat memory
- ✅ **Intelligent archiving** - Automatic summarization when history gets long
- ✅ **Context preservation** - AI always has access to conversation context
- ✅ **Archive editing** - Model can modify archive summaries
- ✅ **Statistics tracking** - Conversation analytics

## 🏗️ Architecture

### **Core Components:**

#### **1. ConversationHistory Class**
```python
class ConversationHistory:
    - history_file: "memory/conversation_history.json"
    - archive_file: "memory/conversation_archive.json"
    - max_history_entries: 50  # Archive when exceeded
    - max_archive_entries: 1000  # Keep last 1000 archived entries
```

#### **2. Data Flow:**
```
User Message → AI Response → History Storage → Context for Next Message
                                    ↓
                              Archive when >50 entries
                                    ↓
                              Summarize & Store
```

#### **3. Archive Structure:**
```json
{
  "id": "archive_timestamp",
  "timestamp": "2024-01-01T12:00:00",
  "type": "archive",
  "original_count": 30,
  "period_start": "2024-01-01T10:00:00",
  "period_end": "2024-01-01T11:30:00",
  "summary": "Archive: 30 messages from meranda, stepan...",
  "key_topics": ["relationship", "communication", "feelings"],
  "user_activity": {"meranda": 15, "stepan": 15}
}
```

## 🔄 How It Works

### **1. Dynamic Greetings**
**Before:**
```
"Hello Meranda! 💕 I'm so glad you're here. I'm Dr. Harmony..."
```

**After:**
- AI analyzes conversation history
- Creates personalized greeting based on context
- References previous conversations naturally
- Adapts to current user situation

### **2. History Management**
```python
# Add new message
conversation_history.add_message(
    user="meranda",
    message="I'm feeling sad today",
    ai_response="I'm sorry to hear that...",
    context="relationship_context"
)

# Get context for AI
context = conversation_history.get_context_for_ai()
# Returns: Recent history + archive summaries
```

### **3. Automatic Archiving**
- **Trigger**: When history exceeds 50 entries
- **Process**: 
  1. Keep last 20 entries in active history
  2. Archive remaining 30+ entries
  3. Generate summary with key topics
  4. Store in archive with metadata

### **4. Context Integration**
```python
# In web_app.py chat_endpoint
history_context = conversation_history.get_context_for_ai()
relationship_context = shared_context.get_context_summary()
full_context = f"{relationship_context}\n\n{history_context}"

ai_response = await ai_client.generate_response(
    system_prompt=PSYCHOLOGIST_SYSTEM_PROMPT,
    user_message=message,
    context=full_context,  # Includes history + archive
    user_profile=user_profile_dict
)
```

## 📊 API Endpoints

### **Get Conversation History**
```http
GET /api/conversation-history
Authorization: Basic meranda:musser

Response:
{
  "history": [
    {
      "id": "msg_0_1704067200",
      "timestamp": "2024-01-01T12:00:00",
      "user": "meranda",
      "message": "I'm feeling sad today",
      "ai_response": "I'm sorry to hear that...",
      "context": "relationship_context",
      "type": "conversation"
    }
  ],
  "statistics": {
    "current_messages": 25,
    "archived_periods": 3,
    "total_archived_messages": 75,
    "last_activity": "2024-01-01T12:00:00",
    "users": ["meranda", "stepan"]
  }
}
```

### **Get Conversation Archive**
```http
GET /api/conversation-archive
Authorization: Basic meranda:musser

Response:
{
  "archive": [
    {
      "id": "archive_1704067200",
      "timestamp": "2024-01-01T12:00:00",
      "type": "archive",
      "original_count": 30,
      "period_start": "2024-01-01T10:00:00",
      "period_end": "2024-01-01T11:30:00",
      "summary": "Archive: 30 messages from meranda, stepan...",
      "key_topics": ["relationship", "communication"],
      "user_activity": {"meranda": 15, "stepan": 15}
    }
  ],
  "summary": "Archive contains 3 periods with 75 total messages..."
}
```

### **Edit Archive Entry**
```http
PUT /api/conversation-archive/{archive_id}
Authorization: Basic meranda:musser
Content-Type: application/json

{
  "summary": "Updated summary by AI"
}
```

### **Clear Conversation History**
```http
POST /api/conversation-clear
Authorization: Basic meranda:musser

Response:
{
  "success": true,
  "message": "Conversation history cleared and archived"
}
```

## 🎨 Frontend Integration

### **JavaScript Functions:**
```javascript
// Load and display conversation history
loadConversationHistory()

// Display history in chat
displayConversationHistory(history)

// Load archive modal
loadConversationArchive()

// Edit archive entry
editArchiveEntry(archiveId)

// Clear history
clearConversationHistory()
```

### **UI Elements:**
- **📚 Archive button** - View conversation archive
- **🗑️ Clear History button** - Archive and clear current history
- **Automatic history loading** - Shows previous conversations on page load

## 🧠 AI Integration

### **Enhanced Prompt:**
```
**DYNAMIC GREETINGS:**
- Create personalized, contextual greetings based on conversation history
- Reference previous conversations naturally when relevant
- Show genuine interest in their ongoing journey
- Adapt your welcome based on their current situation and feelings
- If first message, create warm, personalized welcome

**CONVERSATION HISTORY:**
- You have access to recent conversation history and archived summaries
- Use this context to provide personalized, contextual responses
- Reference previous conversations naturally when relevant
- Build on ongoing discussions and patterns
```

### **Context Building:**
```python
def get_context_for_ai(self, include_archive: bool = True) -> str:
    context_parts = []
    
    # Add recent history (last 5 messages)
    recent = self.get_recent_history(5)
    if recent:
        context_parts.append("RECENT CONVERSATION HISTORY:")
        for msg in recent:
            context_parts.append(f"{msg['user']}: {msg['message']}")
            context_parts.append(f"Dr. Harmony: {msg['ai_response']}")
    
    # Add archive summary
    if include_archive and self.archive:
        context_parts.append("\nARCHIVED CONVERSATIONS:")
        context_parts.append(self.get_archive_summary())
    
    return "\n".join(context_parts)
```

## 📈 Benefits

### **For Users:**
- **Personalized experience** - AI remembers conversations
- **Contextual responses** - References previous discussions
- **No repetitive greetings** - Dynamic, contextual welcomes
- **Archive access** - View conversation history

### **For AI:**
- **Rich context** - Full conversation history available
- **Pattern recognition** - Can identify trends over time
- **Personalized responses** - Based on user history
- **Archive management** - Can edit and improve summaries

### **For System:**
- **Memory efficiency** - Archives old conversations
- **Performance** - Keeps active history manageable
- **Scalability** - Handles unlimited conversation history
- **Data preservation** - No conversation data lost

## 🔧 Configuration

### **Archive Settings:**
```python
self.max_history_entries = 50      # Archive when exceeded
self.max_archive_entries = 1000    # Keep last 1000 archived entries
```

### **File Locations:**
```
memory/conversation_history.json    # Active conversation history
memory/conversation_archive.json    # Archived conversations
```

### **Archive Summary Generation:**
- **Topic extraction** - Identifies key conversation themes
- **User activity analysis** - Tracks participation patterns
- **Period summarization** - Creates contextual summaries
- **Metadata preservation** - Stores timestamps and counts

## 🚀 Usage Examples

### **First Time User:**
```
User: "Hi"
AI: "Hello! I'm Dr. Harmony, your personal relationship consultant. 
     I'm here to help you and your partner understand each other better. 
     What would you like to talk about today?"
```

### **Returning User:**
```
User: "Hi"
AI: "Welcome back! I remember we were talking about communication 
     patterns yesterday. How are things going with that? 
     I'm here to continue supporting your relationship journey."
```

### **Archive Management:**
```
User: "Show me our conversation history"
AI: *Opens archive modal with conversation summaries*
User: "Edit this summary"
AI: *Allows editing of archive entry*
```

---

## 🎉 **System Ready!**

**Dr. Harmony now provides:**
- ✅ **Dynamic, contextual greetings**
- ✅ **Persistent conversation memory**
- ✅ **Intelligent archiving system**
- ✅ **Rich context for AI responses**
- ✅ **Archive management capabilities**

**No more static welcome messages - every interaction is personalized and contextual!** 💕🧠✨ 