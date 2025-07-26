"""
Dr. Harmony Web Application
FastAPI web interface for the AI relationship psychologist
"""

import os
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn

from ai_client import ai_client
from memory.user_profiles import profile_manager
from memory.conversation_history import conversation_history
from memory.relationship_memory import relationship_memory, MemoryEntry
from prompts.psychologist_prompt import PSYCHOLOGIST_SYSTEM_PROMPT
from shared_context import shared_context
from config import settings

# Initialize FastAPI app
app = FastAPI(title="Dr. Harmony", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Security
security = HTTPBasic()

# User credentials (in production, use proper authentication)
USERS = {
    "meranda": "musser",  # Meranda's password
    "stepan": "stepan"   # Stepan's password
}

def verify_password(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify user credentials"""
    if credentials.username in USERS and USERS[credentials.username] == credentials.password:
        return credentials.username
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/sw.js")
async def service_worker():
    """Serve service worker"""
    from fastapi.responses import FileResponse
    return FileResponse("static/js/sw.js", media_type="application/javascript")

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, username: str = Depends(verify_password)):
    """Show chat interface after authentication"""
    # Get user profile
    profile = profile_manager.get_user_profile(username)
    
    # Get current time for template
    from datetime import datetime
    moment_time = datetime.now().strftime("%H:%M")
    
    # Determine theme based on user
    theme = "dark" if username == "stepan" else "light"
    
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "username": username,
        "user_profile": profile.get_profile() if profile else {},
        "moment_time": moment_time,
        "theme": theme
    })

@app.post("/api/chat")
async def chat_endpoint(
    request: Request,
    message: str = Form(...),
    username: str = Depends(verify_password)
):
    """Handle chat messages"""
    try:
        # Get user profile
        profile = profile_manager.get_user_profile(username)
        
        # Get conversation history context
        history_context = conversation_history.get_context_for_ai()
        
        # Get relationship context
        relationship_context = shared_context.get_context_summary()
        
        # Combine contexts
        full_context = f"{relationship_context}\n\n{history_context}"
        
        # Generate AI response
        user_profile_dict = None
        if profile:
            profile_data = profile.get_profile()
            user_profile_dict = {
                'username': profile_data.get('username', username),
                'profile': profile_data.get('profile', ''),
                'relationship_status': profile_data.get('relationship_status', ''),
                'current_feeling': profile_data.get('current_feeling', '')
            }
        
        ai_response = await ai_client.generate_response(
            system_prompt=PSYCHOLOGIST_SYSTEM_PROMPT,
            user_message=message,
            context=full_context,
            user_profile=user_profile_dict
        )
        
        # Add to conversation history
        conversation_history.add_message(
            user=username,
            message=message,
            ai_response=ai_response,
            context=relationship_context
        )
        
        # Update shared context
        shared_context.add_shared_memory({
            'user': username,
            'message': message,
            'ai_response': ai_response,
            'description': f"{username}: {message[:100]}..."
        })
        
        # Update communication patterns
        shared_context.update_communication_pattern('web_chat', 1)
        
        # Update current topics (simple keyword extraction)
        topics = [word.lower() for word in message.split() if len(word) > 3]
        if topics:
            shared_context.update_current_topics(topics[:3])
        
        return {
            "response": ai_response,
            "timestamp": datetime.now().isoformat(),
            "user": username
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/conversation-history")
async def get_conversation_history(username: str = Depends(verify_password)):
    """Get conversation history"""
    try:
        recent_history = conversation_history.get_recent_history(20)
        return {
            "history": recent_history,
            "statistics": conversation_history.get_statistics()
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/conversation-archive")
async def get_conversation_archive(username: str = Depends(verify_password)):
    """Get conversation archive"""
    try:
        archive_entries = conversation_history.get_archive_entries(10)
        archive_summary = conversation_history.get_archive_summary()
        return {
            "archive": archive_entries,
            "summary": archive_summary
        }
    except Exception as e:
        return {"error": str(e)}

@app.put("/api/conversation-archive/{archive_id}")
async def edit_archive_entry(
    archive_id: str,
    request: Request,
    username: str = Depends(verify_password)
):
    """Edit archive entry (AI can modify summaries)"""
    try:
        data = await request.json()
        new_summary = data.get("summary", "")
        
        if not new_summary.strip():
            return {"success": False, "error": "Summary cannot be empty"}
        
        success = conversation_history.edit_archive_entry(archive_id, new_summary)
        if success:
            return {"success": True, "message": "Archive entry updated successfully"}
        else:
            return {"success": False, "error": "Archive entry not found"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/conversation-clear")
async def clear_conversation_history(username: str = Depends(verify_password)):
    """Clear conversation history (archive first)"""
    try:
        conversation_history.clear_history()
        return {"success": True, "message": "Conversation history cleared and archived"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/profile")
async def get_profile(username: str = Depends(verify_password)):
    """Get user profile"""
    try:
        profile = profile_manager.get_user_profile(username)
        
        if profile:
            profile_data = profile.get_profile()
            return {
                "username": profile_data.get("username", username),
                "profile": profile_data.get("profile", ""),
                "relationship_status": profile_data.get("relationship_status", ""),
                "current_feeling": profile_data.get("current_feeling", ""),
                "last_updated": profile_data.get("last_updated", "")
            }
        else:
            return {"error": "Profile not found"}
    except Exception as e:
        return {"error": str(e)}

@app.put("/api/profile")
async def update_profile(
    request: Request,
    username: str = Depends(verify_password)
):
    """Update user profile"""
    try:
        data = await request.json()
        new_profile = data.get("profile", "")
        
        if not new_profile.strip():
            return {"success": False, "error": "Profile cannot be empty"}
        
        profile = profile_manager.get_user_profile(username)
        if profile:
            success = profile.update_profile(new_profile)
            if success:
                print(f"✅ Profile updated successfully for user {username}")
                return {"success": True, "message": "Profile updated successfully"}
            else:
                return {"success": False, "error": "Failed to update profile"}
        else:
            return {"success": False, "error": "Profile not found"}
        
    except Exception as e:
        print(f"❌ Error updating profile: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/hidden-profile")
async def get_hidden_profile(username: str = Depends(verify_password)):
    """Get hidden profile (model's private notes)"""
    try:
        profile = profile_manager.get_user_profile(username)
        
        if profile:
            hidden_data = profile.get_hidden_profile()
            return {
                "username": hidden_data.get("username", username),
                "hidden_profile": hidden_data.get("hidden_profile", ""),
                "last_updated": hidden_data.get("last_updated", "")
            }
        else:
            return {"error": "Profile not found"}
    except Exception as e:
        return {"error": str(e)}

@app.put("/api/hidden-profile")
async def update_hidden_profile(
    request: Request,
    username: str = Depends(verify_password)
):
    """Update hidden profile (model's private notes)"""
    try:
        data = await request.json()
        new_hidden_profile = data.get("hidden_profile", "")
        
        profile = profile_manager.get_user_profile(username)
        if profile:
            success = profile.update_hidden_profile(new_hidden_profile)
            if success:
                print(f"✅ Hidden profile updated successfully for user {username}")
                return {"success": True, "message": "Hidden profile updated successfully"}
            else:
                return {"success": False, "error": "Failed to update hidden profile"}
        else:
            return {"success": False, "error": "Profile not found"}
        
    except Exception as e:
        print(f"❌ Error updating hidden profile: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/diary")
async def get_diary_entries(username: str = Depends(verify_password)):
    """Get diary entries"""
    try:
        entries = profile_manager.get_diary_entries(username)
        
        # Format entries for display
        formatted_entries = []
        for i, entry in enumerate(entries):
            formatted_entries.append({
                "id": f"entry_{i}",
                "content": entry.get("content", "Hi Diary"),
                "timestamp": entry.get("timestamp", datetime.now().isoformat()),
                "mood": entry.get("mood", "Reflective")
            })
        
        return formatted_entries
        
    except Exception as e:
        return []

@app.put("/api/diary/{entry_id}")
async def update_diary_entry(
    entry_id: str,
    request: Request,
    username: str = Depends(verify_password)
):
    """Update diary entry"""
    try:
        data = await request.json()
        new_content = data.get("content", "")
        
        if not new_content.strip():
            return {"success": False, "error": "Content cannot be empty"}
        
        # Extract index from entry_id (entry_0, entry_1, etc.)
        try:
            index = int(entry_id.replace("entry_", ""))
        except ValueError:
            return {"success": False, "error": "Invalid entry ID"}
        
        # Update the entry in the file
        success = profile_manager.update_diary_entry(username, index, new_content)
        
        if success:
            print(f"✅ Diary entry {entry_id} updated successfully for user {username}")
            return {"success": True, "message": "Diary entry updated successfully"}
        else:
            print(f"❌ Failed to update diary entry {entry_id} for user {username}")
            return {"success": False, "error": "Failed to update diary entry"}
        
    except Exception as e:
        print(f"❌ Error updating diary entry: {e}")
        return {"success": False, "error": str(e)}

@app.delete("/api/diary/{entry_id}")
async def delete_diary_entry(
    entry_id: str,
    username: str = Depends(verify_password)
):
    """Delete diary entry"""
    try:
        # Extract index from entry_id (entry_0, entry_1, etc.)
        try:
            index = int(entry_id.replace("entry_", ""))
        except ValueError:
            return {"success": False, "error": "Invalid entry ID"}
        
        # Delete the entry from the file
        success = profile_manager.delete_diary_entry(username, index)
        
        if success:
            print(f"✅ Diary entry {entry_id} deleted successfully for user {username}")
            return {"success": True, "message": "Diary entry deleted successfully"}
        else:
            print(f"❌ Failed to delete diary entry {entry_id} for user {username}")
            return {"success": False, "error": "Failed to delete diary entry"}
        
    except Exception as e:
        print(f"❌ Error deleting diary entry: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 