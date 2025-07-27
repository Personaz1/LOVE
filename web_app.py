"""
AI Guardian Angel Web Application
FastAPI web interface for the AI family guardian angel
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn

# Load environment variables
load_dotenv()

from ai_client import AIClient
from prompts.psychologist_prompt import AI_GUARDIAN_SYSTEM_PROMPT
from memory.user_profiles import UserProfile
from memory.conversation_history import ConversationHistory
from file_agent import file_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Family Psychologist Bot", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Security
security = HTTPBasic()

# Initialize components
ai_client = AIClient()
conversation_history = ConversationHistory()

def verify_password(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify user credentials"""
    username = credentials.username
    password = credentials.password
    
    # Simple authentication - in production, use proper password hashing
    if username == "meranda" and password == "musser":
        return username
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, username: str = Depends(verify_password)):
    """Serve chat page"""
    return templates.TemplateResponse("chat.html", {"request": request, "username": username})

@app.post("/api/chat/stream")
async def chat_stream_endpoint(
    request: Request,
    message: str = Form(...),
    username: str = Depends(verify_password)
):
    """Handle chat messages with streaming response"""
    
    async def generate_stream():
        try:
            # Get user profile
            user_profile = UserProfile(username)
            user_profile_dict = user_profile.get_profile()
            
            # Get conversation context
            recent_messages = conversation_history.get_recent_history(limit=5)
            
            # Build full context
            full_context = ""
            if recent_messages:
                full_context += "Recent conversation:\n"
                for msg in recent_messages:
                    full_context += f"- User: {msg.get('message', '')}\n"
                    full_context += f"- AI: {msg.get('ai_response', '')}\n"
            
            # Send initial status (optional - can be removed)
            # yield f"data: {json.dumps({'type': 'status', 'message': 'Starting response generation...'})}\n\n"
            
            full_response = ""
            async for chunk in ai_client.generate_streaming_response(
                system_prompt=AI_GUARDIAN_SYSTEM_PROMPT,
                user_message=message,
                context=full_context,
                user_profile=user_profile_dict
            ):
                if chunk:
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            # Add to conversation history
            conversation_history.add_message(username, message, full_response)
            
            # Send completion signal (optional - can be removed)
            # yield f"data: {json.dumps({'type': 'complete', 'timestamp': datetime.now().isoformat()})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@app.post("/api/chat")
async def chat_endpoint(
    request: Request,
    message: str = Form(...),
    username: str = Depends(verify_password)
):
    """Handle chat messages with regular response (fallback)"""
    try:
        # Get user profile
        user_profile = UserProfile(username)
        user_profile_dict = user_profile.get_profile()
        
        # Get conversation context
        recent_messages = conversation_history.get_recent_history(limit=5)
        
        # Build full context
        full_context = ""
        if recent_messages:
            full_context += "Recent conversation:\n"
            for msg in recent_messages:
                full_context += f"- User: {msg.get('message', '')}\n"
                full_context += f"- AI: {msg.get('ai_response', '')}\n"
        
        # Generate response
        response = await ai_client._generate_gemini_response(
            system_prompt=AI_GUARDIAN_SYSTEM_PROMPT,
            user_message=message,
            context=full_context,
            user_profile=user_profile_dict
        )
        
        # Add to conversation history
        conversation_history.add_message(username, message, response)
        
        return {"response": response}
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profile")
async def get_profile(username: str = Depends(verify_password)):
    """Get user profile"""
    try:
        user_profile = UserProfile(username)
        profile_data = user_profile.get_profile()
        
        # Add emotional history
        emotional_history = user_profile.get_emotional_history(limit=10)
        emotional_trends = user_profile.get_emotional_trends()
        
        profile_data["emotional_history"] = emotional_history
        profile_data["emotional_trends"] = emotional_trends
        
        return profile_data
        
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profile/feeling")
async def update_feeling(
    feeling: str = Form(...),
    context: str = Form(""),
    username: str = Depends(verify_password)
):
    """Update user's current feeling"""
    try:
        user_profile = UserProfile(username)
        result = user_profile.update_current_feeling(feeling, context)
        return {"success": result, "feeling": feeling}
        
    except Exception as e:
        logger.error(f"Error updating feeling: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversation-history")
async def get_conversation_history(
    limit: int = 10,
    username: str = Depends(verify_password)
):
    """Get conversation history for the user"""
    try:
        # Get conversation history
        history = conversation_history.get_recent_history(limit=limit)
        
        # Get statistics
        stats = conversation_history.get_statistics()
        
        return {
            "history": history,
            "statistics": stats,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return {
            "history": [],
            "statistics": {},
            "success": False,
            "error": str(e)
        }

@app.post("/api/conversation-clear")
async def clear_conversation_history(
    username: str = Depends(verify_password)
):
    """Clear and archive conversation history"""
    try:
        conversation_history.clear_history()
        return {"success": True, "message": "Conversation history cleared and archived"}
    except Exception as e:
        logger.error(f"Error clearing conversation history: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/conversation-archive")
async def get_conversation_archive(
    username: str = Depends(verify_password)
):
    """Get conversation archive"""
    try:
        archive = conversation_history.get_archive_entries()
        summary = conversation_history.get_archive_summary()
        
        return {
            "archive": archive,
            "summary": summary,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error getting conversation archive: {e}")
        return {
            "archive": [],
            "summary": "Error loading archive",
            "success": False,
            "error": str(e)
        }

@app.put("/api/conversation-archive/{archive_id}")
async def edit_conversation_archive(
    archive_id: str,
    summary: str = Form(...),
    username: str = Depends(verify_password)
):
    """Edit conversation archive entry"""
    try:
        success = conversation_history.edit_archive_entry(archive_id, summary)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error editing archive entry: {e}")
        return {"success": False, "error": str(e)}



@app.get("/api/files/list")
async def list_files(
    directory: str = "",
    username: str = Depends(verify_password)
):
    """List files in directory"""
    try:
        result = file_agent.list_files(directory)
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/search")
async def search_files(
    query: str,
    username: str = Depends(verify_password)
):
    """Search files"""
    try:
        result = file_agent.search_files(query)
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/theme")
async def get_current_theme(username: str = Depends(verify_password)):
    """Get current theme"""
    try:
        theme_file = "memory/current_theme.json"
        if os.path.exists(theme_file):
            with open(theme_file, 'r') as f:
                theme_data = json.load(f)
                return {"success": True, "theme": theme_data}
        else:
            return {"success": True, "theme": {"theme": "default"}}
    except Exception as e:
        logger.error(f"Error getting theme: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/theme")
async def update_theme(
    theme: str = Form(...),
    username: str = Depends(verify_password)
):
    """Update current theme"""
    try:
        theme_file = "memory/current_theme.json"
        theme_data = {
            "theme": theme,
            "updated_at": datetime.now().isoformat()
        }
        
        with open(theme_file, 'w') as f:
            json.dump(theme_data, f, indent=2)
        
        return {"success": True, "theme": theme_data}
    except Exception as e:
        logger.error(f"Error updating theme: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/hidden-profile")
async def get_hidden_profile(username: str = Depends(verify_password)):
    """Get user's hidden profile (model's private notes)"""
    try:
        user_profile = UserProfile(username)
        hidden_profile = user_profile.get_hidden_profile()
        return {"success": True, "hidden_profile": hidden_profile}
        
    except Exception as e:
        logger.error(f"Error getting hidden profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/hidden-profile")
async def update_hidden_profile(
    hidden_profile_data: dict,
    username: str = Depends(verify_password)
):
    """Update user's hidden profile"""
    try:
        user_profile = UserProfile(username)
        result = user_profile.update_hidden_profile(hidden_profile_data)
        return {"success": result, "message": "Hidden profile updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating hidden profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 