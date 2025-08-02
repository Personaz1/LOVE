"""
AI Superintelligent Family Architect Web Application
FastAPI web interface for the AI superintelligent family architect and family guardian
"""

import os
import json
import asyncio
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, Response, UploadFile, File, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn

# Импортируем кэш
from ai_client.utils.cache import system_cache

# Load environment variables
load_dotenv()

from ai_client.core.client import AIClient
from prompts.guardian_prompt import AI_GUARDIAN_SYSTEM_PROMPT
from memory.user_profiles import UserProfile
from memory.conversation_history import conversation_history
from memory.guardian_profile import guardian_profile
from memory.theme_manager import theme_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# WebSocket connections list
websocket_connections = []

class WebSocketLogHandler(logging.Handler):
    """Handler для отправки логов через WebSocket"""
    def emit(self, record):
        try:
            log_entry = self.format(record)
            # Отправляем всем подключенным WebSocket клиентам
            for websocket in websocket_connections[:]:  # Копируем список для безопасной итерации
                try:
                    asyncio.create_task(websocket.send_text(log_entry))
                except Exception as e:
                    # Удаляем отключенные WebSocket
                    websocket_connections.remove(websocket)
        except Exception as e:
            pass  # Игнорируем ошибки WebSocket

# Создаем WebSocket handler
websocket_handler = WebSocketLogHandler()
websocket_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Добавляем WebSocket handler только к основному логгеру
# Проверяем, не добавлен ли уже WebSocket handler
if not any(isinstance(handler, WebSocketLogHandler) for handler in logger.handlers):
    logger.addHandler(websocket_handler)

app = FastAPI(title="ΔΣ Guardian - Superintelligent Family Architect", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Security
security = HTTPBasic()

# Session management
SESSIONS = {}  # In production, use Redis or database
SESSION_SECRET = secrets.token_urlsafe(32)

# Initialize components
ai_client = AIClient()
# conversation_history = ConversationHistory() # This line is removed

def get_recent_file_changes() -> str:
    """Get recent file changes for system analysis"""
    try:
        import os
        from datetime import datetime, timedelta
        
        changes = []
        changes.append("## RECENT FILE CHANGES")
        
        # Check for recently modified files
        current_time = datetime.now()
        recent_files = []
        
        # Key directories to monitor
        key_dirs = ["", "ai_client.py", "web_app.py", "memory", "templates", "static", "guardian_sandbox"]
        
        for item in key_dirs:
            if os.path.exists(item):
                if os.path.isfile(item):
                    # Single file
                    mtime = datetime.fromtimestamp(os.path.getmtime(item))
                    if current_time - mtime < timedelta(hours=24):
                        recent_files.append((item, mtime))
                else:
                    # Directory
                    for root, dirs, files in os.walk(item):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                                if current_time - mtime < timedelta(hours=24):
                                    recent_files.append((file_path, mtime))
                            except:
                                continue
        
        # Sort by modification time
        recent_files.sort(key=lambda x: x[1], reverse=True)
        
        if recent_files:
            changes.append("Recently modified files (last 24 hours):")
            for file_path, mtime in recent_files[:10]:  # Show top 10
                changes.append(f"- {file_path} (modified: {mtime.strftime('%H:%M:%S')})")
        else:
            changes.append("No recent file changes detected.")
        
        # Check for new files in sandbox
        sandbox_path = "guardian_sandbox"
        if os.path.exists(sandbox_path):
            sandbox_files = []
            for root, dirs, files in os.walk(sandbox_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        ctime = datetime.fromtimestamp(os.path.getctime(file_path))
                        if current_time - ctime < timedelta(hours=24):
                            sandbox_files.append((file_path, ctime))
                    except:
                        continue
            
            if sandbox_files:
                changes.append("\nNew files in sandbox (last 24 hours):")
                for file_path, ctime in sandbox_files[:5]:
                    changes.append(f"- {file_path} (created: {ctime.strftime('%H:%M:%S')})")
        
        return "\n".join(changes)
        
    except Exception as e:
        logger.error(f"Error getting recent file changes: {e}")
        return "Error retrieving recent file changes"

def create_session(username: str) -> str:
    """Create a new session for user"""
    session_id = secrets.token_urlsafe(32)
    SESSIONS[session_id] = {
        "username": username,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(days=30)  # 30 дней вместо 24 часов
    }
    # Сохраняем сессии в файл
    _save_sessions()
    return session_id

def _save_sessions():
    """Сохранить сессии в файл"""
    try:
        sessions_file = os.path.join(os.path.dirname(__file__), 'sessions.json')
        sessions_data = {}
        for session_id, session in SESSIONS.items():
            sessions_data[session_id] = {
                "username": session["username"],
                "created_at": session["created_at"].isoformat(),
                "expires_at": session["expires_at"].isoformat()
            }
        with open(sessions_file, 'w', encoding='utf-8') as f:
            json.dump(sessions_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving sessions: {e}")

def _load_sessions():
    """Загрузить сессии из файла"""
    try:
        sessions_file = os.path.join(os.path.dirname(__file__), 'sessions.json')
        if os.path.exists(sessions_file):
            with open(sessions_file, 'r', encoding='utf-8') as f:
                sessions_data = json.load(f)
            for session_id, session in sessions_data.items():
                SESSIONS[session_id] = {
                    "username": session["username"],
                    "created_at": datetime.fromisoformat(session["created_at"]),
                    "expires_at": datetime.fromisoformat(session["expires_at"])
                }
    except Exception as e:
        logger.error(f"Error loading sessions: {e}")

# Загружаем сессии при запуске
_load_sessions()

def get_session(session_id: str) -> Optional[Dict]:
    """Get session data"""
    if session_id not in SESSIONS:
        return None
    
    session = SESSIONS[session_id]
    if datetime.now() > session["expires_at"]:
        del SESSIONS[session_id]
        _save_sessions() # Сохраняем после удаления
        return None
    
    return session

def verify_session(request: Request) -> Optional[str]:
    """Verify session and return username"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None
    
    session = get_session(session_id)
    if not session:
        return None
    
    return session["username"]

def verify_password(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify user credentials - fallback for API calls"""
    username = credentials.username
    password = credentials.password
    
    # Valid credentials
    valid_credentials = {
        "meranda": "musser",
        "stepan": "stepan",
        "guest": "guest"
    }
    
    # Simple authentication - in production, use proper password hashing
    if username in valid_credentials and password == valid_credentials[username]:
        return username
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

def get_current_user(request: Request) -> Optional[str]:
    """Get current user from session or query params"""
    # Try session first
    username = verify_session(request)
    if username:
        return username
    
    # Fallback to query params for backward compatibility
    username = request.query_params.get("username")
    password = request.query_params.get("password")
    
    # Valid credentials
    valid_credentials = {
        "meranda": "musser",
        "stepan": "stepan",
        "guest": "guest"
    }
    
    if username in valid_credentials and password == valid_credentials[username]:
        return username
    
    return None

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    """Handle login and create session"""
    # Valid credentials
    valid_credentials = {
        "meranda": "musser",
        "stepan": "stepan",  # Add stepan user
        "guest": "guest"
    }
    
    # Debug logging
    logger.info(f"Login attempt - Username: '{username}', Password: '{password}'")
    logger.info(f"Valid credentials: {valid_credentials}")
    logger.info(f"Username in valid_credentials: {username in valid_credentials}")
    if username in valid_credentials:
        logger.info(f"Password matches: {password == valid_credentials[username]}")
    
    if username in valid_credentials and password == valid_credentials[username]:
        logger.info(f"Login successful for user: {username}")
        session_id = create_session(username)
        response = RedirectResponse(url="/chat", status_code=302)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=86400  # 24 hours
        )
        return response
    else:
        logger.info(f"Login failed for user: {username}")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid credentials"
        })

@app.post("/api/login-greeting")
async def login_greeting(request: Request):
    """Handle automatic greeting when user logs in"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    async def generate_greeting():
        try:
            # Get user profile
            user_profile = UserProfile(username)
            user_profile_dict = user_profile.get_profile()
            user_profile_dict['username'] = username
            
            # Get conversation context and system analysis
            recent_messages = conversation_history.get_recent_history(limit=10)
            emotional_history = user_profile.get_emotional_history(limit=5)
            emotional_trends = user_profile.get_emotional_trends()
            current_theme = theme_manager.analyze_context_and_set_theme(
                user_profile_dict, recent_messages, emotional_history
            )
            
            # Build rich context for Guardian
            context = f"""
User Profile:
- Name: {user_profile_dict.get('full_name', username)}
- Current Feeling: {user_profile_dict.get('current_feeling', 'N/A')}
- Bio: {user_profile_dict.get('profile', 'N/A')}

Recent Emotional History:
{emotional_history}

Emotional Trends:
{emotional_trends}

Recent Conversation ({len(recent_messages)} messages):
{chr(10).join([f"- {msg.get('message', 'N/A')}" for msg in recent_messages[-3:]])}

Current Theme: {current_theme}

System Status: Guardian is ready to provide personalized greeting
"""
            
            # Generate dynamic greeting using Guardian AI
            greeting_message = f"Create a natural, contextual greeting for {username} based on their current situation and system state. Be creative and avoid generic phrases."
            
            greeting = ai_client.chat(
                message=greeting_message,
                user_profile=user_profile_dict,
                conversation_context=context,
                system_prompt=guardian_profile.get_system_prompt()
            )
            
            # Send greeting
            yield f"data: {json.dumps({'type': 'greeting', 'content': greeting})}\n\n"
            
            # Send completion
            yield f"data: {json.dumps({'type': 'greeting_complete', 'timestamp': datetime.now().isoformat()})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in login greeting: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_greeting(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Serve chat page"""
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/", status_code=302)
    
    # If user came via URL with credentials, create session
    if not verify_session(request) and request.query_params.get("username"):
        session_id = create_session(username)
        response = templates.TemplateResponse("chat.html", {
            "request": request, 
            "username": username,
            "moment_time": datetime.now().strftime("%I:%M %p")
        })
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=86400
        )
        return response
    
    return templates.TemplateResponse("chat.html", {
        "request": request, 
        "username": username,
        "moment_time": datetime.now().strftime("%I:%M %p")
    })

@app.post("/api/chat/stream")
async def chat_stream_endpoint(
    request: Request,
    message: str = Form(...)
):
    """Handle chat messages with streaming response"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Create session if user came via URL
    if not verify_session(request) and request.query_params.get("username"):
        session_id = create_session(username)
        # Note: Can't set cookie in streaming response, but session is created
    
    async def generate_stream():
        try:
            # Get user profile
            user_profile = UserProfile(username)
            user_profile_dict = user_profile.get_profile()
            user_profile_dict['username'] = username  # Add username to profile
            
            # Get conversation context
            recent_messages = conversation_history.get_recent_history(limit=5)
            
            # Build full context
            full_context = ""
            if recent_messages:
                full_context += "Recent conversation:\n"
                for msg in recent_messages:
                    full_context += f"- User: {msg.get('message', '')}\n"
                    full_context += f"- AI: {msg.get('ai_response', '')}\n"
            
            # Track the complete response
            full_response = ""
            
            async for chunk in ai_client.generate_streaming_response(
                system_prompt=guardian_profile.get_system_prompt(),
                user_message=message,
                context=full_context,
                user_profile=user_profile_dict
            ):
                if chunk:
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            # ОБРАБОТКА TOOL CALLS В STREAMING
            logger.info(f"🔧 STREAMING CHAT: Processing response for tool calls...")
            logger.info(f"🔧 STREAMING CHAT: Full response: {full_response[:500]}...")
            
            # Извлекаем tool calls из полного ответа
            tool_calls = ai_client._extract_tool_calls(full_response)
            
            if tool_calls:
                logger.info(f"🔧 STREAMING CHAT: Found {len(tool_calls)} tool calls: {tool_calls}")
                
                # Выполняем каждый tool call
                for tool_call in tool_calls:
                    try:
                        logger.info(f"🔧 STREAMING CHAT: Executing tool call: {tool_call}")
                        tool_result = ai_client._execute_tool_call(tool_call)
                        logger.info(f"✅ STREAMING CHAT: Tool result: {tool_result[:200]}..." if len(tool_result) > 200 else tool_result)
                        
                        # Отправляем результат tool call в чат
                        yield f"data: {json.dumps({'type': 'chunk', 'content': f'\n\n**Результат выполнения:**\n{tool_result}\n\n'})}\n\n"
                        
                        # Заменяем tool call на результат в полном ответе
                        full_response = full_response.replace(tool_call, tool_result)
                        
                    except Exception as e:
                        logger.error(f"❌ STREAMING CHAT: Error executing tool call {tool_call}: {e}")
                        error_msg = f"❌ Error executing {tool_call}: {str(e)}"
                        yield f"data: {json.dumps({'type': 'chunk', 'content': f'\n\n**Ошибка:**\n{error_msg}\n\n'})}\n\n"
                        full_response = full_response.replace(tool_call, error_msg)
            else:
                logger.info(f"🔧 STREAMING CHAT: No tool calls found in response")
            
            # Send final completion signal
            yield f"data: {json.dumps({'type': 'message_complete'})}\n\n"
            
            # Add to conversation history
            conversation_history.add_message(username, message, full_response)
            
            # Send final completion signal
            yield f"data: {json.dumps({'type': 'complete', 'timestamp': datetime.now().isoformat()})}\n\n"
            
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
    message: str = Form(...)
):
    """Handle chat messages with regular response"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Get user profile
        user_profile = UserProfile(username)
        user_profile_dict = user_profile.get_profile()
        user_profile_dict['username'] = username
        
        # Get conversation context
        recent_messages = conversation_history.get_recent_history(limit=5)
        
        # Build full context
        full_context = ""
        if recent_messages:
            full_context += "Recent conversation:\n"
            for msg in recent_messages:
                full_context += f"- User: {msg.get('message', '')}\n"
                full_context += f"- AI: {msg.get('ai_response', '')}\n"
        
        # Generate AI response
        ai_response = ai_client.chat(
            message=message,
            user_profile=user_profile_dict,
            conversation_context=full_context
        )
        
        # ОБРАБОТКА TOOL CALLS
        logger.info(f"🔧 CHAT: Processing response for tool calls...")
        
        # Извлекаем tool calls из ответа
        tool_calls = ai_client._extract_tool_calls(ai_response)
        
        if tool_calls:
            logger.info(f"🔧 CHAT: Found {len(tool_calls)} tool calls: {tool_calls}")
            
            # Выполняем каждый tool call
            for tool_call in tool_calls:
                try:
                    logger.info(f"🔧 CHAT: Executing tool call: {tool_call}")
                    tool_result = ai_client._execute_tool_call(tool_call)
                    logger.info(f"✅ CHAT: Tool result: {tool_result[:200]}..." if len(tool_result) > 200 else tool_result)
                    
                    # Заменяем tool call на результат в ответе
                    ai_response = ai_response.replace(tool_call, tool_result)
                    
                except Exception as e:
                    logger.error(f"❌ CHAT: Error executing tool call {tool_call}: {e}")
                    error_msg = f"❌ Error executing {tool_call}: {str(e)}"
                    ai_response = ai_response.replace(tool_call, error_msg)
        else:
            logger.info(f"🔧 CHAT: No tool calls found in response")
        
        # Save to conversation history
        conversation_history.add_message(username, message, ai_response)
        
        return JSONResponse({
            "success": True,
            "response": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/profile")
async def get_profile(request: Request):
    """Get current user's profile"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        user_profile = UserProfile(username)
        profile_data = user_profile.get_profile()
        profile_data['username'] = username  # Add username to profile data
        
        return JSONResponse({
            "success": True,
            "profile": profile_data
        })
        
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/profile/{username}")
async def get_profile_by_username(request: Request, username: str):
    """Get profile by username (for avatar loading)"""
    # Only allow getting profiles for meranda and stepan
    if username not in ["meranda", "stepan"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        user_profile = UserProfile(username)
        profile_data = user_profile.get_profile()
        
        return JSONResponse({
            "success": True,
            "profile": profile_data
        })
        
    except Exception as e:
        logger.error(f"Error getting profile for {username}: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/avatar/{username}")
async def get_user_avatar(request: Request, username: str):
    """Get user avatar URL without authentication (for display purposes)"""
    # Only allow getting avatars for meranda and stepan
    if username not in ["meranda", "stepan"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        user_profile = UserProfile(username)
        profile_data = user_profile.get_profile()
        
        return JSONResponse({
            "success": True,
            "avatar_url": profile_data.get('avatar_url', ''),
            "username": username
        })
        
    except Exception as e:
        logger.error(f"Error getting avatar for {username}: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/api/profile/update")
async def update_profile_full(request: Request):
    """Update user profile"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        form_data = await request.form()
        
        # Get current profile to preserve existing data
        user_profile = UserProfile(username)
        current_profile = user_profile.get_profile()
        
        # Extract profile data from form, preserving existing data
        profile_data = {
                       'full_name': form_data.get('full_name', current_profile.get('full_name', '')),
                       'age': form_data.get('age', current_profile.get('age', '')),
                       'location': form_data.get('location', current_profile.get('location', '')),
                       'email': form_data.get('email', current_profile.get('email', '')),
                       'current_feeling': form_data.get('current_feeling', current_profile.get('current_feeling', '')),
                       'profile': form_data.get('bio', current_profile.get('profile', '')),  # bio field maps to profile
                       'interests': form_data.get('interests', current_profile.get('interests', '')),
                       'goals': form_data.get('goals', current_profile.get('goals', '')),
                       'challenges': form_data.get('challenges', current_profile.get('challenges', '')),
                       'preferences': form_data.get('preferences', current_profile.get('preferences', '')),
                       'show_feelings': form_data.get('show_feelings') == 'on',
                       'avatar_url': current_profile.get('avatar_url', ''),  # Preserve avatar URL
                       'last_updated': datetime.now().isoformat()
                   }
        
        # Handle password change if provided
        new_password = form_data.get('new_password')
        confirm_password = form_data.get('confirm_password')
        current_password = form_data.get('current_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                return JSONResponse({
                    "success": False,
                    "error": "Passwords do not match"
                }, status_code=400)
            
            # In production, validate current password and hash new password
            if current_password == 'musser':  # Simple validation for demo
                profile_data['password'] = new_password
            else:
                return JSONResponse({
                    "success": False,
                    "error": "Incorrect current password"
                }, status_code=400)
        
        # Update profile
        user_profile._save_profile(profile_data)
        
        return JSONResponse({
            "success": True,
            "message": "Profile updated successfully",
            "profile": profile_data
        })
        
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/api/profile/feeling")
async def update_feeling(
    request: Request,
    feeling: str = Form(...),
    context: str = Form("")
):
    """Update user's current feeling"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        user_profile = UserProfile(username)
        user_profile.update_current_feeling(feeling, context)
        
        return JSONResponse({
            "success": True,
            "message": f"Feeling updated to {feeling}",
            "feeling": feeling
        })
        
    except Exception as e:
        logger.error(f"Error updating feeling: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/conversation-history")
async def get_conversation_history(
    request: Request,
    limit: int = 20
):
    """Get conversation history - optimized for speed"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Create session if user came via URL
    if not verify_session(request) and request.query_params.get("username"):
        session_id = create_session(username)
        response = JSONResponse({
            "success": True,
            "history": conversation_history.get_recent_history(limit=min(limit, 50)),
            "count": len(conversation_history.get_recent_history(limit=min(limit, 50)))
        })
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=86400
        )
        return response
    
    try:
        # Убираем кэш для истории - всегда получаем свежие данные
        optimized_limit = min(limit, 50)
        logger.info(f"🔄 CONVERSATION HISTORY: Fetching fresh data for {username}")
        history = conversation_history.get_recent_history(limit=optimized_limit)
        
        return JSONResponse({
            "success": True,
            "history": history,
            "count": len(history),
            "cached": False
        })
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "history": [],
            "count": 0
        }, status_code=500)

@app.post("/api/conversation-clear")
async def clear_conversation_history(request: Request):
    """Clear conversation history"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        conversation_history.clear_history()
        
        return JSONResponse({
            "success": True,
            "message": "Conversation history cleared"
        })
        
    except Exception as e:
        logger.error(f"Error clearing conversation history: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/conversation-archive")
async def get_conversation_archive(request: Request):
    """Get conversation archive"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Create session if user came via URL
    if not verify_session(request) and request.query_params.get("username"):
        session_id = create_session(username)
        response = JSONResponse({
            "success": True,
            "archive": conversation_history.get_archive_entries(),
            "count": len(conversation_history.get_archive_entries())
        })
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=86400
        )
        return response
    
    try:
        archive = conversation_history.get_archive_entries()
        
        return JSONResponse({
            "success": True,
            "archive": archive,
            "count": len(archive)
        })
        
    except Exception as e:
        logger.error(f"Error getting conversation archive: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.put("/api/conversation-archive/{archive_id}")
async def edit_conversation_archive(
    request: Request,
    archive_id: str,
    summary: str = Form(...)
):
    """Edit conversation archive summary"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        success = conversation_history.edit_archive_entry(archive_id, summary)
        
        if success:
            return JSONResponse({
                "success": True,
                "message": "Archive summary updated"
            })
        else:
            return JSONResponse({
                "success": False,
                "error": "Archive not found"
            }, status_code=404)
        
    except Exception as e:
        logger.error(f"Error editing conversation archive: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)



@app.get("/api/files/list")
async def list_files(
    request: Request,
    directory: str = ""
):
    """List files in directory"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Security: only allow listing files in safe directories
        safe_directories = ["memory", "static", "templates"]
        
        if directory and directory not in safe_directories:
            return JSONResponse({
                "success": False,
                "error": "Access denied to this directory"
            }, status_code=403)
        
        target_dir = directory if directory else "."
        files = []
        
        if os.path.exists(target_dir):
            for item in os.listdir(target_dir):
                item_path = os.path.join(target_dir, item)
                files.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
                })
        
        return JSONResponse({
            "success": True,
            "files": files,
            "directory": directory
        })
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/files/search")
async def search_files(
    request: Request,
    query: str
):
    """Search files by name"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Security: only search in safe directories
        safe_directories = ["memory", "static", "templates"]
        results = []
        
        for directory in safe_directories:
            if os.path.exists(directory):
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if query.lower() in file.lower():
                            file_path = os.path.join(root, file)
                            results.append({
                                "name": file,
                                "path": file_path,
                                "size": os.path.getsize(file_path)
                            })
        
        return JSONResponse({
            "success": True,
            "results": results,
            "query": query,
            "count": len(results)
        })
        
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

# Temporary endpoint to prevent 404 errors from cached frontend
@app.get("/api/hidden-profile")
async def get_hidden_profile_stub(request: Request):
    """Temporary stub for hidden profile - returns empty data"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {"success": True, "hidden_profile": "", "username": username, "last_updated": ""}

@app.put("/api/hidden-profile")
async def update_hidden_profile_stub(
    request: Request,
    hidden_profile_text: str = Form(...)
):
    """Temporary stub for hidden profile update"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {"success": True, "message": "Hidden profile functionality removed"}

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Serve profile page"""
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/", status_code=302)
    
    # If user came via URL with credentials, create session
    if not verify_session(request) and request.query_params.get("username"):
        session_id = create_session(username)
        response = templates.TemplateResponse("profile.html", {
            "request": request, 
            "username": username,
            "profile": get_profile_data(username)
        })
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=86400
        )
        return response
    
    try:
        profile_data = get_profile_data(username)
        return templates.TemplateResponse("profile.html", {
            "request": request, 
            "username": username,
            "profile": profile_data
        })
            
    except Exception as e:
        logger.error(f"Error loading profile page: {e}")
        raise HTTPException(status_code=500, detail="Error loading profile")

def get_profile_data(username: str) -> Dict:
    """Get profile data for user"""
    user_profile = UserProfile(username)
    profile_data = user_profile.get_profile()
    
    # Add default values for new fields
    profile_data.setdefault('email', '')
    profile_data.setdefault('full_name', '')
    profile_data.setdefault('age', '')
    profile_data.setdefault('location', '')

    profile_data.setdefault('show_feelings', True)

    return profile_data

@app.post("/api/profile/avatar")
async def upload_avatar(request: Request):
    """Upload user avatar"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        form_data = await request.form()
        avatar_file = form_data.get('avatar')
        
        if not avatar_file:
            return JSONResponse({"success": False, "error": "No file provided"})
        
        # Create avatars directory if it doesn't exist
        avatar_dir = "static/avatars"
        os.makedirs(avatar_dir, exist_ok=True)
        
        # Save avatar file
        avatar_path = f"{avatar_dir}/{username}_avatar.jpg"
        
        # Read file content properly
        file_content = await avatar_file.read()
        with open(avatar_path, "wb") as f:
            f.write(file_content)
        
        # Update profile with avatar path
        user_profile = UserProfile(username)
        profile_data = user_profile.get_profile()
        profile_data['avatar_url'] = f"/static/avatars/{username}_avatar.jpg"
        user_profile._save_profile(profile_data)
        
        return JSONResponse({
            "success": True, 
            "avatar_url": profile_data['avatar_url'],
            "message": "Avatar uploaded successfully"
        })
        
    except Exception as e:
        logger.error(f"Error uploading avatar: {e}")
        return JSONResponse({"success": False, "error": str(e)})

@app.delete("/api/profile/delete")
async def delete_account(request: Request):
    """Delete user account"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # In production, implement proper account deletion with data cleanup
        # For now, just return success
        return JSONResponse({"success": True, "message": "Account deleted successfully"})
        
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        return JSONResponse({"success": False, "error": str(e)})

@app.post("/logout")
async def logout(response: Response):
    """Handle logout and clear session"""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session_id")
    return response

@app.get("/api/model-status")
async def get_model_status(request: Request):
    """Get AI model status and quota information - internal agent endpoint, no auth required"""
    
    try:
        # Проверяем кэш
        cached_status = system_cache.get("model_status")
        if cached_status:
            logger.info("✅ MODEL STATUS: Returning cached result")
            return JSONResponse({
                "success": True,
                "status": cached_status,
                "timestamp": datetime.now().isoformat(),
                "cached": True
            })
        
        # Получаем свежие данные
        logger.info("🔄 MODEL STATUS: Fetching fresh data")
        status = ai_client.get_model_status()
        
        # Кэшируем результат на 5 минут
        system_cache.set("model_status", status, ttl_seconds=300)
        
        return JSONResponse({
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "cached": False
        })
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/api/system-analysis/clear-cache")
async def clear_system_analysis_cache(request: Request):
    """Clear system analysis cache"""
    try:
        username = get_current_user(request)
        cache_params = {"username": username, "has_user": bool(username)}
        
        system_cache.invalidate("system_analysis", cache_params)
        logger.info("🗑️ SYSTEM ANALYSIS: Cache cleared")
        
        return JSONResponse({
            "success": True,
            "message": "Cache cleared successfully"
        })
    except Exception as e:
        logger.error(f"❌ Error clearing cache: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/api/model-status/clear-cache")
async def clear_model_status_cache(request: Request):
    """Clear model status cache"""
    try:
        system_cache.invalidate("model_status")
        logger.info("🗑️ MODEL STATUS: Cache cleared")
        
        return JSONResponse({
            "success": True,
            "message": "Model status cache cleared successfully"
        })
    except Exception as e:
        logger.error(f"❌ Error clearing model status cache: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/system-analysis")
async def get_system_analysis(request: Request):
    """Get system analysis and relationship insights - internal agent endpoint, no auth required"""
    
    try:
        # Get current user if available, but don't require it
        username = get_current_user(request)
        
        # Проверяем кэш (но с более коротким TTL для тестирования)
        cache_params = {"username": username, "has_user": bool(username)}
        cached_result = system_cache.get("system_analysis", cache_params, ttl_seconds=60)  # 1 минута для тестирования
        
        if cached_result:
            logger.info("✅ SYSTEM ANALYSIS: Returning cached result")
            return JSONResponse(content=cached_result)
        
        # Если кэша нет, начинаем анализ
        logger.info("🔧 SYSTEM ANALYSIS: Starting fresh analysis...")
        
        if username:
            # If user is authenticated, get their profile and context
            user_profile = UserProfile(username)
            profile_data = user_profile.get_profile()
            
            # Get conversation history
            recent_messages = conversation_history.get_recent_history(limit=10)
            
            # Get emotional history and trends
            emotional_history = user_profile.get_emotional_history(limit=10)
            emotional_trends = user_profile.get_emotional_trends()
            
            # Analyze and set theme automatically
            current_theme = theme_manager.analyze_context_and_set_theme(
                profile_data, recent_messages, emotional_history
            )
            
            # Get recent model notes for context
            recent_notes = ai_client.memory.get_model_notes()
            
            # Build context for LLM - ПОЛНЫЕ ДАННЫЕ ДЛЯ АНАЛИЗА
            context = f"""
User Profile:
- Name: {profile_data.get('full_name', username)}
- Current Feeling: {profile_data.get('current_feeling', 'N/A')}
- Bio: {profile_data.get('profile', 'N/A')}

Recent Emotional History:
{emotional_history}

Emotional Trends:
{emotional_trends}

Recent Conversation ({len(recent_messages)} messages):
{chr(10).join([f"- {msg.get('message', 'N/A')}" for msg in recent_messages])}

Recent Model Notes:
{recent_notes}

Current Theme: {current_theme}
"""
        else:
            # If no user authenticated, provide basic system analysis
            context = """
System Status:
- No authenticated user
- Basic system analysis mode
- Guardian AI is operational
- All core functions available
"""
            current_theme = "neutral"
        
        # Get recent file changes and system status
        recent_changes = get_recent_file_changes()
        system_health = ai_client.system.diagnose_system_health()
        
        # Generate system analysis using AI - ОСНОВНОЙ ПРОМПТ GUARDIAN
        system_prompt = AI_GUARDIAN_SYSTEM_PROMPT
        
        analysis_message = f"""You are ΔΣ Guardian. Analyze the system and take autonomous actions based on this context:

User Context: {context}
Recent Changes: {recent_changes[:500]}
System Health: {system_health[:500]}

**YOUR MISSION:**
1. **ANALYZE** the conversation history and user context
2. **IDENTIFY** important events, patterns, and insights
3. **TAKE ACTION** - create reminders, notes, calendar events, update profiles
4. **RESPOND** with your analysis and actions taken

**LOOK FOR:**
- Birthdays, anniversaries, important dates
- Emotional patterns and trends
- Relationship dynamics
- System issues or improvements needed
- User preferences and needs

**ACT AUTONOMOUSLY** - don't just analyze, CREATE and UPDATE based on what you discover.

Provide your response in this JSON format:
{{
  "system_status": "Your analysis of current state",
  "actions_taken": ["List of actions you performed"],
  "insights": ["Key insights discovered"],
  "recommendations": ["Suggestions for users"],
  "reminders_created": ["Any reminders or calendar events"],
  "notes_added": ["System notes you created"]
}}"""

        # Log system analysis start
        logger.info("🔧 SYSTEM ANALYSIS: Starting autonomous analysis...")
        logger.info(f"🔧 SYSTEM ANALYSIS: User context available: {bool(username)}")
        logger.info(f"🔧 SYSTEM ANALYSIS: Recent changes: {len(recent_changes.split())} words")
        logger.info(f"🔧 SYSTEM ANALYSIS: System health: {len(system_health.split())} words")
        
        # Детальное логирование для отладки
        try:
            logger.info(f"🔧 SYSTEM ANALYSIS: emotional_history type: {type(emotional_history)}")
            logger.info(f"🔧 SYSTEM ANALYSIS: emotional_trends type: {type(emotional_trends)}")
            logger.info(f"🔧 SYSTEM ANALYSIS: recent_messages type: {type(recent_messages)}")
            logger.info(f"🔧 SYSTEM ANALYSIS: recent_notes type: {type(recent_notes)}")
        except Exception as e:
            logger.error(f"🔧 SYSTEM ANALYSIS: Error in debug logging: {e}")

        # Generate analysis
        analysis_response = ai_client.chat(
            message=analysis_message,
            user_profile=profile_data if username else {},
            conversation_context=context,
            system_prompt=system_prompt
        )

        # Log system analysis completion
        logger.info(f"✅ SYSTEM ANALYSIS: Completed - {len(analysis_response.split())} words generated")
        logger.info(f"✅ SYSTEM ANALYSIS: Response preview: {analysis_response[:100]}...")
        
        # Try to parse JSON response - УЛУЧШЕННАЯ ОБРАБОТКА
        try:
            import re
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', analysis_response, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
                logger.info("✅ SYSTEM ANALYSIS: JSON parsed successfully")
                
                # Генерируем динамические советы на основе анализа
                try:
                    # Получаем профиль как словарь
                    user_profile_dict = profile_data.get_profile() if username and profile_data else None
                    tips = ai_client.tips.generate_tips(
                        context=f"System analysis: {analysis_data.get('system_status', '')[:200]}",
                        user_profile=user_profile_dict
                    )
                    analysis_data["tips"] = tips
                    logger.info("✅ SYSTEM ANALYSIS: Dynamic tips generated")
                except Exception as e:
                    logger.error(f"❌ SYSTEM ANALYSIS: Tips generation failed: {e}")
                    analysis_data["tips"] = ["Focus on open communication", "Practice active listening", "Take time for self-care"]
            else:
                # Fallback if no JSON found
                logger.warning("⚠️ SYSTEM ANALYSIS: No JSON found in response")
                # Генерируем динамические советы
                try:
                    # Получаем профиль как словарь
                    user_profile_dict = profile_data.get_profile() if username and profile_data else None
                    tips = ai_client.tips.generate_tips(
                        context=f"System analysis response: {analysis_response[:200]}",
                        user_profile=user_profile_dict
                    )
                except:
                    tips = ["Focus on open communication", "Practice active listening", "Take time for self-care"]
                
                analysis_data = {
                    "system_status": analysis_response,
                    "tips": tips,
                    "capabilities": "System is operational"
                }
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing failed
            logger.error(f"❌ SYSTEM ANALYSIS: JSON parsing failed: {e}")
            # Генерируем динамические советы
            try:
                # Получаем профиль как словарь
                user_profile_dict = profile_data.get_profile() if username and profile_data else None
                tips = ai_client.tips.generate_tips(
                    context=f"System analysis failed: {analysis_response[:200]}",
                    user_profile=user_profile_dict
                )
            except:
                tips = ["Focus on open communication", "Practice active listening", "Take time for self-care"]
            
            analysis_data = {
                "system_status": analysis_response,
                "tips": tips,
                "capabilities": "System is operational"
            }
        except Exception as e:
            # General fallback
            logger.error(f"❌ SYSTEM ANALYSIS: General parsing error: {e}")
            # Генерируем динамические советы
            try:
                # Получаем профиль как словарь
                user_profile_dict = profile_data.get_profile() if username and profile_data else None
                tips = ai_client.tips.generate_tips(
                    context=f"System analysis error: {str(e)}",
                    user_profile=user_profile_dict
                )
            except:
                tips = ["Focus on open communication", "Practice active listening", "Take time for self-care"]
            
            analysis_data = {
                "system_status": "System analysis completed",
                "tips": tips,
                "capabilities": "System is operational"
            }
        
        # Сохраняем в кэш только если нет ошибок
        if "❌ Error: 429" not in analysis_response and "❌ Error:" not in analysis_response:
            system_cache.set("system_analysis", analysis_data, cache_params, ttl_seconds=600)
            logger.info("💾 SYSTEM ANALYSIS: Result cached for 10 minutes")
        else:
            logger.warning("⚠️ SYSTEM ANALYSIS: Not caching error response")
            # Инвалидируем кэш при ошибках
            system_cache.invalidate("system_analysis", cache_params)
        
        return JSONResponse({
            "success": True,
            "analysis": analysis_data,
            "theme": current_theme,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ System analysis error: {e}")
        
        # Пробуем вернуть кэшированный результат при ошибке
        try:
            cached_result = system_cache.get("system_analysis", cache_params, ttl_seconds=3600)  # 1 час для fallback
            if cached_result:
                logger.info("✅ SYSTEM ANALYSIS: Returning cached fallback result")
                return JSONResponse(content=cached_result)
        except:
            pass
        
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

# Guardian Profile API endpoints
@app.get("/api/guardian/profile")
async def get_guardian_profile(request: Request):
    """Get ΔΣ Guardian profile"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        profile = guardian_profile.get_profile()
        return JSONResponse({"success": True, "profile": profile})
    except Exception as e:
        logger.error(f"Error getting guardian profile: {e}")
        return JSONResponse({"success": False, "error": str(e)})

@app.post("/api/guardian/profile/update")
async def update_guardian_profile(request: Request):
    data = await request.json()
    guardian_profile.update_profile(data)
    return {"status": "ok", "profile": guardian_profile.get_profile()}

@app.post("/api/guardian/avatar")
async def upload_guardian_avatar(request: Request):
    """Upload ΔΣ Guardian avatar"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        form_data = await request.form()
        avatar_file = form_data.get('avatar')
        
        if not avatar_file:
            return JSONResponse({"success": False, "error": "No file provided"})
        
        # Create avatars directory if it doesn't exist
        avatar_dir = "static/avatars"
        os.makedirs(avatar_dir, exist_ok=True)
        
        # Save avatar file
        avatar_path = f"{avatar_dir}/guardian_avatar.jpg"
        
        # Read file content properly
        file_content = await avatar_file.read()
        with open(avatar_path, "wb") as f:
            f.write(file_content)
        
        # Update profile with avatar path
        success = guardian_profile.update_avatar(f"/static/avatars/guardian_avatar.jpg")
        
        if success:
            profile = guardian_profile.get_profile()
            return JSONResponse({
                "success": True, 
                "avatar_url": profile["avatar_url"],
                "message": "Guardian avatar uploaded successfully"
            })
        else:
            return JSONResponse({"success": False, "error": "Failed to update avatar"})
        
    except Exception as e:
        logger.error(f"Error uploading guardian avatar: {e}")
        return JSONResponse({"success": False, "error": str(e)})

@app.post("/api/guardian/reset")
async def reset_guardian_profile(request: Request):
    """Reset guardian profile to defaults"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        success = guardian_profile.reset_to_defaults()
        if success:
            return JSONResponse({"success": True, "message": "Guardian profile reset to defaults"})
        else:
            return JSONResponse({"success": False, "error": "Failed to reset profile"}, status_code=500)
    except Exception as e:
        logger.error(f"Error resetting guardian profile: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/guardian/update-prompt")
async def update_guardian_prompt_from_file(request: Request):
    """Update guardian prompt from the prompts file"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        success = guardian_profile.update_prompt_from_file()
        if success:
            return JSONResponse({"success": True, "message": "Guardian prompt updated from file"})
        else:
            return JSONResponse({"success": False, "error": "Failed to update prompt"}, status_code=500)
    except Exception as e:
        logger.error(f"Error updating guardian prompt: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/guardian/prompt/reset")
async def reset_guardian_prompt(request: Request):
    guardian_profile.update_prompt_from_file()
    return {"status": "ok", "prompt": guardian_profile.get_system_prompt()}

@app.get("/guardian", response_class=HTMLResponse)
async def guardian_profile_page(request: Request):
    """Serve Guardian profile page"""
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/", status_code=302)
    
    try:
        profile = guardian_profile.get_profile()
        return templates.TemplateResponse("guardian.html", {
            "request": request,
            "username": username,
            "guardian": profile
        })
    except Exception as e:
        logger.error(f"Error loading guardian profile page: {e}")
        return templates.TemplateResponse("guardian.html", {
            "request": request,
            "username": username,
            "guardian": {}
        })

@app.get("/sw.js")
async def service_worker(request: Request):
    """Service Worker for PWA functionality"""
    return FileResponse("static/sw.js", media_type="application/javascript")

# File upload and management endpoints
@app.post("/api/upload-file")
async def upload_file(
    request: Request,
    file: UploadFile = File(...)
):
    """Upload file to sandbox or images directory"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Determine upload directory based on file type
        if file.content_type and file.content_type.startswith('image/'):
            # Images go to static/images for analysis
            upload_dir = "static/images"
            file_path = f"/static/images/{file.filename}"
        else:
            # Other files go to sandbox
            upload_dir = "guardian_sandbox/uploads"
            file_path = f"/guardian_sandbox/uploads/{file.filename}"
        
        # Create directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_location = os.path.join(upload_dir, file.filename)
        with open(file_location, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return JSONResponse({
            "success": True,
            "file_path": file_path,
            "file_name": file.filename,
            "file_type": file.content_type,
            "file_size": len(content)
        })
        
    except Exception as e:
        logger.error(f"File upload error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/api/analyze-image")
async def analyze_image(request: Request):
    """Analyze uploaded image using AI"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        data = await request.json()
        file_path = data.get("file_path")
        file_name = data.get("file_name")
        user_context = data.get("user_context", "")
        
        if not file_path or not file_name:
            return JSONResponse({
                "success": False,
                "error": "Missing file path or name"
            })
        
        # Remove leading slash for file system path
        fs_path = file_path.lstrip('/')
        
        if not os.path.exists(fs_path):
            return JSONResponse({
                "success": False,
                "error": "File not found"
            })
        
        # Use the new integrated image analysis
        analysis = ai_client.system.analyze_image(fs_path, user_context)
        
        return JSONResponse({
            "success": True,
            "analysis": analysis,
            "model_used": ai_client.gemini_client.get_current_model(),
            "vision_api_available": ai_client.gemini_client.vision_client is not None
        })
        
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/api/delete-file")
async def delete_file(request: Request):
    """Delete uploaded file"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        data = await request.json()
        file_path = data.get("file_path")
        
        if not file_path:
            return JSONResponse({
                "success": False,
                "error": "Missing file path"
            })
        
        # Remove leading slash for file system path
        fs_path = file_path.lstrip('/')
        
        if not os.path.exists(fs_path):
            return JSONResponse({
                "success": False,
                "error": "File not found"
            })
        
        # Delete file
        os.remove(fs_path)
        
        return JSONResponse({
            "success": True,
            "message": "File deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"File deletion error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/download/{file_path:path}")
async def download_file(request: Request, file_path: str):
    """Download file from sandbox"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Construct full path
        full_path = os.path.join("guardian_sandbox", file_path)
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Return file for download
        return FileResponse(
            path=full_path,
            filename=os.path.basename(full_path),
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"File download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Message editing endpoints
@app.post("/api/message/edit")
async def edit_message(request: Request):
    """Edit a message in conversation history"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        data = await request.json()
        message_id = data.get("message_id")
        new_content = data.get("new_content")
        
        if not message_id or new_content is None:
            return JSONResponse({
                "success": False,
                "error": "Missing message_id or new_content"
            })
        
        # Edit message in conversation history
        success = conversation_history.edit_message(message_id, new_content)
        
        if success:
            return JSONResponse({
                "success": True,
                "message": "Message edited successfully"
            })
        else:
            return JSONResponse({
                "success": False,
                "error": "Failed to edit message"
            })
        
    except Exception as e:
        logger.error(f"Message edit error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/api/message/delete")
async def delete_message(request: Request):
    """Delete a message from conversation history"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        data = await request.json()
        message_id = data.get("message_id")
        
        if not message_id:
            return JSONResponse({
                "success": False,
                "error": "Missing message_id"
            })
        
        # Delete message from conversation history
        success = conversation_history.delete_message(message_id)
        
        if success:
            return JSONResponse({
                "success": True,
                "message": "Message deleted successfully"
            })
        else:
            return JSONResponse({
                "success": False,
                "error": "Failed to delete message"
            })
        
    except Exception as e:
        logger.error(f"Message deletion error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/api/conversation/archive")
async def archive_conversation(request: Request):
    """Manually archive current conversation"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Archive current conversation
        conversation_history._archive_old_messages()
        
        return JSONResponse({
            "success": True,
            "message": "Conversation archived successfully"
        })
        
    except Exception as e:
        logger.error(f"Conversation archive error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/image-analyzer/status")
async def get_image_analyzer_status(request: Request):
    """Get image analyzer status"""
    try:
        # Image analysis is now integrated into ai_client
        status = ai_client.get_model_status()
        return {"success": True, "status": status}
    except Exception as e:
        logger.error(f"Error getting image analyzer status: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/model/switch")
async def switch_model(request: Request):
    """Switch to a different AI model"""
    try:
        data = await request.json()
        model_name = data.get('model_name')
        
        if not model_name:
            return {"success": False, "error": "Model name is required"}
        
        # Use global AI client instance
        success = ai_client.switch_to_model(model_name)
        
        if success:
            current_model = ai_client.get_model_status()
            return {
                "success": True, 
                "message": f"Switched to {model_name}",
                "current_model": current_model
            }
        else:
            return {"success": False, "error": f"Failed to switch to {model_name}"}
            
    except Exception as e:
        logger.error(f"Error switching model: {e}")
        return {"success": False, "error": str(e)}

@app.get("/roadmap", response_class=HTMLResponse)
async def roadmap_page(request: Request):
    """Development roadmap page"""
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("roadmap.html", {
        "request": request,
        "username": username
    })

@app.get("/models", response_class=HTMLResponse)
async def models_page(request: Request):
    """AI Models management page"""
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("models.html", {
        "request": request,
        "username": username
    })

# WebSocket endpoint для real-time логов
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Простой стриминг логов
        last_position = 0
        
        while True:
            try:
                # Читаем лог файл
                with open('app.log', 'r', encoding='utf-8') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    
                    if new_lines:
                        # Отправляем только новые строки
                        for line in new_lines:
                            if line.strip():
                                await websocket.send_text(line.strip())
                        
                        # Обновляем позицию
                        last_position = f.tell()
                
                # Ждем 1 секунду
                await asyncio.sleep(1)
                
            except FileNotFoundError:
                await websocket.send_text("Log file not found")
                break
            except Exception as e:
                await websocket.send_text(f"Log error: {e}")
                break
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 