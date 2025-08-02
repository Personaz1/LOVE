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
import time

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
import logging.handlers

file_handler = logging.handlers.RotatingFileHandler(
    'app.log', 
    maxBytes=1024*1024,  # 1MB
    backupCount=3  # 3 файла максимум
)
console_handler = logging.StreamHandler()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[file_handler, console_handler]
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

# Отключаем дублирование логов в других модулях
for module_logger in ['ai_client', 'memory', 'ai_client.utils.cache', 'ai_client.tools.tips_generator']:
    module_logger_obj = logging.getLogger(module_logger)
    module_logger_obj.handlers = []
    module_logger_obj.propagate = False

app = FastAPI(title="ΔΣ Guardian - Superintelligent Family Architect", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Security
security = HTTPBasic()

# Session management
import redis

session_redis = redis.Redis(host='localhost', port=6379, db=1)
SESSION_SECRET = secrets.token_urlsafe(32)

# Initialize components
ai_client = AIClient()
gemini_client = ai_client.gemini_client  # Прямой доступ к Gemini клиенту
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

async def create_session(username: str) -> str:
    """Create a new session for user"""
    session_id = secrets.token_urlsafe(32)
    session_data = {
        "username": username,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
    }
    
    # Сохраняем в Redis
    await asyncio.get_event_loop().run_in_executor(
        None, 
        session_redis.setex,
        f"session:{session_id}",
        86400 * 30,  # 30 дней
        json.dumps(session_data)
    )
    return session_id

# Сессии теперь в Redis - старые функции удалены

async def get_session(session_id: str) -> Optional[Dict]:
    """Get session data"""
    try:
        data = await asyncio.get_event_loop().run_in_executor(
            None, session_redis.get, f"session:{session_id}"
        )
        if data:
            session = json.loads(data)
            expires_at = datetime.fromisoformat(session["expires_at"])
            if datetime.now() > expires_at:
                # Удаляем истекшую сессию
                await asyncio.get_event_loop().run_in_executor(
                    None, session_redis.delete, f"session:{session_id}"
                )
                return None
            return session
        return None
    except Exception as e:
        logger.error(f"Session get error: {e}")
        return None

async def verify_session(request: Request) -> Optional[str]:
    """Verify session and return username"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None
    
    session = await get_session(session_id)
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

async def get_current_user(request: Request) -> Optional[str]:
    """Get current user from session or query params"""
    # Try session first
    username = await verify_session(request)
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
        session_id = await create_session(username)
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
    username = await get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    async def generate_greeting():
        try:
            # Get user profile
            user_profile = UserProfile(username)
            user_profile_dict = user_profile.get_profile()
            user_profile_dict['username'] = username
            
            # ПАРАЛЛЕЛЬНАЯ ЗАГРУЗКА - не блокируем
            recent_messages = await asyncio.get_event_loop().run_in_executor(
                None, conversation_history.get_recent_history, 10
            )
            emotional_history = await asyncio.get_event_loop().run_in_executor(
                None, user_profile.get_emotional_history, 5
            )
            emotional_trends = await asyncio.get_event_loop().run_in_executor(
                None, user_profile.get_emotional_trends
            )
            current_theme = await asyncio.get_event_loop().run_in_executor(
                None, theme_manager.analyze_context_and_set_theme,
                user_profile_dict, recent_messages, emotional_history
            )
            
            # Get recent model notes for scheduled actions
            recent_notes = await asyncio.get_event_loop().run_in_executor(
                None, ai_client.memory.get_model_notes
            )
            
            # Check for scheduled actions (birthday greetings, etc.)
            scheduled_actions = []
            if recent_notes and isinstance(recent_notes, dict) and 'notes' in recent_notes:
                for note in recent_notes['notes']:
                    if isinstance(note, dict) and 'scheduled_attunement' in str(note.get('category', '')):
                        scheduled_actions.append(note.get('text', ''))
            
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

Recent Model Notes:
{recent_notes}

Scheduled Actions:
{chr(10).join([f"- {action}" for action in scheduled_actions])}

System Status: Guardian is ready to provide personalized greeting
"""
            
            # Generate dynamic greeting using Guardian AI
            greeting_message = f"""Create a natural, contextual greeting for {username} based on their current situation and system state.

IMPORTANT: Check the scheduled actions and execute them if applicable:
- If there are scheduled birthday greetings or special actions, execute them naturally
- If this is Meranda's first login and there are birthday greetings scheduled, deliver them warmly
- If there are any pending actions for this user, incorporate them into the greeting

Be creative and avoid generic phrases. If there are scheduled actions, make them feel natural and contextual."""
            
            greeting = gemini_client.chat(
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
    username = await get_current_user(request)
    if not username:
        return RedirectResponse(url="/", status_code=302)
    
    # If user came via URL with credentials, create session
    if not await verify_session(request) and request.query_params.get("username"):
        session_id = await create_session(username)
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
    username = await get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Create session if user came via URL
    if not await verify_session(request) and request.query_params.get("username"):
        session_id = await create_session(username)
        # Note: Can't set cookie in streaming response, but session is created
    
    async def generate_stream():
        try:
            # Get user profile
            user_profile = UserProfile(username)
            user_profile_dict = user_profile.get_profile()
            user_profile_dict['username'] = username  # Add username to profile
            
            # ПАРАЛЛЕЛЬНАЯ ЗАГРУЗКА КОНТЕКСТА
            recent_messages = await asyncio.get_event_loop().run_in_executor(
                None, conversation_history.get_recent_history, 5
            )
            
            # Build full context
            full_context = ""
            if recent_messages:
                full_context += "Recent conversation:\n"
                for msg in recent_messages:
                    full_context += f"- User: {msg.get('message', '')}\n"
                    full_context += f"- AI: {msg.get('ai_response', '')}\n"
            
            # Track the complete response with thoughts
            full_response = ""
            thoughts = []
            
            async for chunk_data in gemini_client.generate_streaming_response_with_thoughts(
                system_prompt=guardian_profile.get_system_prompt(),
                user_message=message,
                context=full_context,
                user_profile=user_profile_dict
            ):
                if chunk_data:
                    chunk_text = chunk_data.get('text', '')
                    is_thought = chunk_data.get('thought', False)
                    chunk_type = chunk_data.get('type', 'answer')
                    
                    if chunk_text:
                        if is_thought:
                            thoughts.append(chunk_text)
                            # Отправляем thought отдельно
                            yield f"data: {json.dumps({'type': 'thought', 'content': chunk_text})}\n\n"
                        else:
                            full_response += chunk_text
                            # Отправляем обычный chunk
                            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk_text})}\n\n"
            
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
            
            # Add to conversation history ASYNC
            await asyncio.get_event_loop().run_in_executor(
                None, conversation_history.add_message, username, message, full_response
            )
            
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
    username = await get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Get user profile
        user_profile = UserProfile(username)
        user_profile_dict = user_profile.get_profile()
        user_profile_dict['username'] = username
        
        # ПАРАЛЛЕЛЬНАЯ ЗАГРУЗКА КОНТЕКСТА
        recent_messages = await asyncio.get_event_loop().run_in_executor(
            None, conversation_history.get_recent_history, 5
        )
        
        # Build full context
        full_context = ""
        if recent_messages:
            full_context += "Recent conversation:\n"
            for msg in recent_messages:
                full_context += f"- User: {msg.get('message', '')}\n"
                full_context += f"- AI: {msg.get('ai_response', '')}\n"
        
        # Generate AI response with reasoning
        response_with_thoughts = gemini_client._parse_gemini_response_with_thoughts(
            gemini_client.chat(
                message=message,
                user_profile=user_profile_dict,
                conversation_context=full_context
            )
        )
        logger.info(f"🔧 WEB_APP: Response with thoughts: {response_with_thoughts}")
        
        # ОБРАБОТКА TOOL CALLS
        logger.info(f"🔧 CHAT: Processing response for tool calls...")
        
        # Используем tool_calls из response_with_thoughts (уже извлечены в _parse_gemini_response_with_thoughts)
        tool_calls = response_with_thoughts.get('tool_calls', [])
        logger.info(f"🔧 WEB_APP: Got {len(tool_calls)} tool calls from response_with_thoughts")
        logger.info(f"🔧 WEB_APP: Tool calls content: {tool_calls}")
        logger.info(f"🔧 WEB_APP: response_with_thoughts keys: {list(response_with_thoughts.keys())}")
        
        # Проверяем что tool_calls не пустые
        if not tool_calls:
            logger.warning(f"⚠️ WEB_APP: No tool_calls found in response_with_thoughts")
            logger.warning(f"⚠️ WEB_APP: response_with_thoughts type: {type(response_with_thoughts)}")
            logger.warning(f"⚠️ WEB_APP: response_with_thoughts content: {response_with_thoughts}")
        
        if tool_calls:
            logger.info(f"🔧 CHAT: Found {len(tool_calls)} tool calls: {tool_calls}")
            
            # Выполняем каждый tool call
            for tool_call in tool_calls:
                try:
                    # Извлекаем tool_code из JSON формата {"tool_code": "..."}
                    if isinstance(tool_call, dict) and 'tool_code' in tool_call:
                        tool_code = tool_call['tool_code']
                        logger.info(f"🔧 CHAT: Extracted tool_code: {tool_code}")
                    else:
                        tool_code = str(tool_call)
                        logger.info(f"🔧 CHAT: Using tool_call as string: {tool_code}")
                    
                    logger.info(f"🔧 CHAT: Executing tool call: {tool_code}")
                    tool_result = ai_client._execute_tool_call(tool_code)
                    logger.info(f"✅ CHAT: Tool result: {tool_result[:200]}..." if len(tool_result) > 200 else tool_result)
                    
                    # Заменяем tool call на результат в ответе
                    response_with_thoughts['final_answer'] = response_with_thoughts['final_answer'].replace(str(tool_call), tool_result)
                    
                except Exception as e:
                    logger.error(f"❌ CHAT: Error executing tool call {tool_call}: {e}")
                    error_msg = f"❌ Error executing {tool_call}: {str(e)}"
                    response_with_thoughts['final_answer'] = response_with_thoughts['final_answer'].replace(str(tool_call), error_msg)
        else:
            logger.info(f"🔧 CHAT: No tool calls found in response")
        
        # Save to conversation history ASYNC
        await asyncio.get_event_loop().run_in_executor(
            None, conversation_history.add_message, username, message, response_with_thoughts['final_answer']
        )
        
        return JSONResponse({
            "success": True,
            "response": response_with_thoughts['final_answer'],
            "thoughts": response_with_thoughts['thoughts'],
            "parts": response_with_thoughts['parts'],
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
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
    """Get conversation history - PARALLEL LOADING"""
    username = await get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Create session if user came via URL
    if not await verify_session(request) and request.query_params.get("username"):
        session_id = await create_session(username)
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
        # ПАРАЛЛЕЛЬНАЯ ЗАГРУЗКА - не ждем другие операции
        optimized_limit = min(limit, 50)
        logger.info(f"⚡ CONVERSATION HISTORY: Parallel loading for {username}")
        
        # Загружаем историю в отдельном потоке
        history = await asyncio.get_event_loop().run_in_executor(
            None, 
            conversation_history.get_recent_history, 
            optimized_limit
        )
        
        return JSONResponse({
            "success": True,
            "history": history,
            "count": len(history),
            "cached": False,
            "parallel": True
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Create session if user came via URL
    if not await verify_session(request) and request.query_params.get("username"):
        session_id = await create_session(username)
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {"success": True, "hidden_profile": "", "username": username, "last_updated": ""}

@app.put("/api/hidden-profile")
async def update_hidden_profile_stub(
    request: Request,
    hidden_profile_text: str = Form(...)
):
    """Temporary stub for hidden profile update"""
    username = await get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {"success": True, "message": "Hidden profile functionality removed"}

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Serve profile page"""
    username = await get_current_user(request)
    if not username:
        return RedirectResponse(url="/", status_code=302)
    
    # If user came via URL with credentials, create session
    if not await verify_session(request) and request.query_params.get("username"):
        session_id = await create_session(username)
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
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
        username = await get_current_user(request)
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
        username = await get_current_user(request)
        
        # Проверяем кэш (но с более коротким TTL для тестирования)
        cache_params = {"username": username, "has_user": bool(username)}
        cached_result = system_cache.get("system_analysis", cache_params, ttl_seconds=300)  # 5 минут
        
        if cached_result:
            logger.info("✅ SYSTEM ANALYSIS: Returning cached result")
            return JSONResponse(content=cached_result)
        
        # Если кэша нет, начинаем анализ В ФОНЕ
        logger.info("🔧 SYSTEM ANALYSIS: Starting background analysis...")
        
        # Генерируем динамические советы для placeholder
        try:
            user_profile_dict = None
            if username:
                user_profile = UserProfile(username)
                user_profile_dict = user_profile.get_profile()
            
            tips = ai_client.tips.generate_tips(
                context="System analysis in progress",
                user_profile=user_profile_dict
            )
        except Exception as e:
            logger.error(f"❌ Tips generation failed: {e}")
            tips = ["Focus on open communication", "Practice active listening", "Take time for self-care"]
        
        # ВОЗВРАЩАЕМ РЕЗУЛЬТАТ ТОЛЬКО ЕСЛИ НЕТ ПОЛЬЗОВАТЕЛЯ
        if not username:
            return JSONResponse({
                "success": True,
                "analysis": {
                    "system_status": "Analysis in progress...",
                    "tips": tips,
                    "capabilities": "System is operational"
                },
                "theme": "neutral",
                "timestamp": datetime.now().isoformat(),
                "background": True
            })
        
        # ЕСЛИ ЕСТЬ ПОЛЬЗОВАТЕЛЬ - ВЫПОЛНЯЕМ ПОЛНЫЙ АНАЛИЗ
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

        # Generate analysis - используем прямой доступ к Gemini для лучшего fallback
        analysis_response = gemini_client.chat(
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
            # Extract JSON from response - improved regex
            # Look for JSON objects that might be embedded in text
            json_patterns = [
                r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Nested JSON
                r'\{[^}]*\}',  # Simple JSON
                r'\{.*?\}',  # Lazy match
            ]
            
            analysis_data = None
            for pattern in json_patterns:
                json_matches = re.findall(pattern, analysis_response, re.DOTALL)
                for match in json_matches:
                    try:
                        parsed = json.loads(match)
                        # Check if it looks like system analysis data
                        if isinstance(parsed, dict) and any(key in parsed for key in ['system_status', 'status', 'analysis', 'capabilities']):
                            analysis_data = parsed
                            logger.info(f"✅ SYSTEM ANALYSIS: JSON parsed successfully with pattern {pattern}")
                            break
                    except json.JSONDecodeError:
                        continue
                if analysis_data:
                    break
            
            if analysis_data:
                # Генерируем динамические советы на основе анализа
                try:
                    # Получаем профиль как словарь
                    user_profile_dict = profile_data if username and profile_data else None
                    tips = ai_client.tips.generate_tips(
                        context=f"System analysis: {analysis_data.get('system_status', '')[:200]}",
                        user_profile=user_profile_dict
                    )
                    analysis_data["tips"] = tips
                    logger.info("✅ SYSTEM ANALYSIS: Dynamic tips generated")
                except Exception as e:
                    logger.error(f"❌ SYSTEM ANALYSIS: Tips generation failed: {e}")
                    # Используем TipsGenerator для fallback
                    try:
                        tips = ai_client.tips.generate_tips(
                            context="System analysis fallback",
                            user_profile=user_profile_dict
                        )
                        analysis_data["tips"] = tips
                    except:
                        analysis_data["tips"] = ["Focus on open communication", "Practice active listening", "Take time for self-care"]
            else:
                # Fallback if no valid JSON found
                logger.warning("⚠️ SYSTEM ANALYSIS: No valid JSON found in response")
                # Генерируем динамические советы
                try:
                    # Получаем профиль как словарь
                    user_profile_dict = profile_data if username and profile_data else None
                    tips = ai_client.tips.generate_tips(
                        context=f"System analysis response: {analysis_response[:200]}",
                        user_profile=user_profile_dict
                    )
                except Exception as e:
                    logger.error(f"❌ Tips generation fallback failed: {e}")
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
                user_profile_dict = profile_data if username and profile_data else None
                tips = ai_client.tips.generate_tips(
                    context=f"System analysis failed: {analysis_response[:200]}",
                    user_profile=user_profile_dict
                )
            except Exception as e:
                logger.error(f"❌ Tips generation JSON fallback failed: {e}")
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
                user_profile_dict = profile_data if username and profile_data else None
                tips = ai_client.tips.generate_tips(
                    context=f"System analysis error: {str(e)}",
                    user_profile=user_profile_dict
                )
            except Exception as e2:
                logger.error(f"❌ Tips generation general fallback failed: {e2}")
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
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
    username = await get_current_user(request)
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

# ===== НОВЫЕ API ENDPOINTS =====

# 1. Голосовой ввод / озвучка
@app.post("/api/speech-to-text")
async def speech_to_text(request: Request):
    """Преобразование голоса в текст"""
    try:
        # TODO: Implement Whisper/Google STT
        return {"text": "Voice input placeholder", "confidence": 0.95}
    except Exception as e:
        logger.error(f"Speech-to-text error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/text-to-speech")
async def text_to_speech(request: Request):
    """Преобразование текста в голос"""
    try:
        # TODO: Implement ElevenLabs/Bark TTS
        return {"audio_url": "/static/audio/generated.mp3", "duration": 3.5}
    except Exception as e:
        logger.error(f"Text-to-speech error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 2. Пользовательские заметки
@app.post("/api/notes/add")
async def add_note(request: Request):
    """Добавить заметку"""
    try:
        data = await request.json()
        note_id = f"note_{int(time.time())}"
        note_data = {
            "id": note_id,
            "content": data.get("content", ""),
            "tags": data.get("tags", []),
            "created_at": datetime.now().isoformat(),
            "pinned": data.get("pinned", False)
        }
        # TODO: Save to database/file
        return {"success": True, "note_id": note_id}
    except Exception as e:
        logger.error(f"Add note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/notes/list")
async def list_notes(request: Request):
    """Получить список заметок"""
    try:
        # TODO: Load from database/file
        notes = [
            {"id": "note_1", "content": "Sample note", "tags": ["important"], "pinned": True}
        ]
        return {"notes": notes}
    except Exception as e:
        logger.error(f"List notes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/notes/{note_id}")
async def delete_note(request: Request, note_id: str):
    """Удалить заметку"""
    try:
        # TODO: Delete from database/file
        return {"success": True}
    except Exception as e:
        logger.error(f"Delete note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 3. Filechat / PDF/CSV upload + QA
@app.post("/api/files/upload")
async def upload_file_for_chat(
    request: Request,
    file: UploadFile = File(...)
):
    """Загрузить файл для чата"""
    try:
        # TODO: Implement PDF/CSV processing
        file_id = f"file_{int(time.time())}"
        return {
            "file_id": file_id,
            "filename": file.filename,
            "size": file.size,
            "type": file.content_type
        }
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/query")
async def query_file(request: Request):
    """Задать вопрос по файлу"""
    try:
        data = await request.json()
        # TODO: Implement file QA with embeddings
        return {"answer": "File query response placeholder"}
    except Exception as e:
        logger.error(f"File query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 4. Динамическая память и аннотации
@app.post("/api/memory/add_context_chunk")
async def add_memory_chunk(request: Request):
    """Добавить кусок контекста в память"""
    try:
        data = await request.json()
        chunk_id = f"chunk_{int(time.time())}"
        # TODO: Save to vector database
        return {"chunk_id": chunk_id, "success": True}
    except Exception as e:
        logger.error(f"Add memory chunk error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory/search")
async def search_memory(request: Request, query: str):
    """Поиск в памяти"""
    try:
        # TODO: Implement vector search
        return {"results": [], "query": query}
    except Exception as e:
        logger.error(f"Memory search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memory/tag")
async def tag_memory(request: Request):
    """Тегировать память"""
    try:
        data = await request.json()
        # TODO: Implement memory tagging
        return {"success": True}
    except Exception as e:
        logger.error(f"Memory tag error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 5. Расширенные system_tools
@app.get("/api/tools/network/ping")
async def ping_host(request: Request, host: str):
    """Ping хоста"""
    try:
        # TODO: Implement ping
        return {"host": host, "status": "reachable", "latency": 15}
    except Exception as e:
        logger.error(f"Ping error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tools/network/ports")
async def scan_ports(request: Request, host: str):
    """Сканирование портов"""
    try:
        # TODO: Implement port scanning
        return {"host": host, "open_ports": [80, 443, 22]}
    except Exception as e:
        logger.error(f"Port scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 6. Интерактивные утилиты
@app.post("/api/tools/code_exec")
async def execute_code(request: Request):
    """Безопасное выполнение кода"""
    try:
        data = await request.json()
        # TODO: Implement sandboxed code execution
        return {"output": "Code execution placeholder", "success": True}
    except Exception as e:
        logger.error(f"Code execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tools/terminal")
async def terminal_command(request: Request):
    """Безопасные команды терминала"""
    try:
        data = await request.json()
        # TODO: Implement read-only terminal
        return {"output": "Terminal command placeholder", "success": True}
    except Exception as e:
        logger.error(f"Terminal command error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 7. API действий (как у GPTs)
@app.post("/api/action/search_web")
async def search_web_action(request: Request):
    """Действие: поиск в вебе"""
    try:
        data = await request.json()
        # TODO: Implement web search
        return {"results": [], "query": data.get("query", "")}
    except Exception as e:
        logger.error(f"Web search action error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/action/generate_image")
async def generate_image_action(request: Request):
    """Действие: генерация изображения"""
    try:
        data = await request.json()
        # TODO: Implement image generation
        return {"image_url": "/static/images/generated.png"}
    except Exception as e:
        logger.error(f"Image generation action error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/action/fill_form")
async def fill_form_action(request: Request):
    """Действие: заполнение формы"""
    try:
        data = await request.json()
        # TODO: Implement form filling
        return {"success": True, "form_data": data}
    except Exception as e:
        logger.error(f"Form fill action error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== AGI UI GENERATION =====

@app.post("/api/ui/generate")
async def generate_ui_interface(request: Request):
    """Генерация UI интерфейса моделью в реальном времени"""
    try:
        data = await request.json()
        context = data.get("context", "")
        user_intent = data.get("intent", "")
        current_state = data.get("state", {})
        
        # Получаем пользователя
        username = await get_current_user(request)
        if not username:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Генерируем UI описание через модель
        ui_prompt = f"""
        You are an AGI interface designer. Generate a JSON description of the UI based on:
        
        CONTEXT: {context}
        USER INTENT: {user_intent}
        CURRENT STATE: {current_state}
        USER: {username}
        
        Return a JSON object with this structure:
        {{
            "type": "interface",
            "layout": "vertical|horizontal|grid",
            "theme": "light|dark|auto",
            "components": [
                {{
                    "type": "text|input|button|card|chat|image|chart|sidebar|header",
                    "id": "unique_id",
                    "content": "text content",
                    "props": {{...}},
                    "actions": ["action_name"],
                    "style": {{...}}
                }}
            ],
            "events": [
                {{
                    "trigger": "click|input|load",
                    "action": "action_name",
                    "target": "component_id"
                }}
            ]
        }}
        
        Available component types:
        - text: Simple text display
        - input: Text input field
        - button: Clickable button
        - card: Container with content
        - chat: Chat interface
        - image: Image display
        - chart: Data visualization
        - sidebar: Side navigation
        - header: Top navigation
        
        Make the interface adaptive to user context and intent.
        """
        
        # Вызываем модель для генерации UI
        ai_client = AIClient()
        ui_response = ai_client.chat(ui_prompt)
        
        # Парсим JSON из ответа
        try:
            import re
            json_match = re.search(r'\{.*\}', ui_response, re.DOTALL)
            if json_match:
                ui_description = json.loads(json_match.group())
                return {
                    "success": True,
                    "ui": ui_description,
                    "raw_response": ui_response
                }
            else:
                # Fallback - базовый интерфейс
                return {
                    "success": True,
                    "ui": {
                        "type": "interface",
                        "layout": "vertical",
                        "theme": "auto",
                        "components": [
                            {
                                "type": "text",
                                "id": "welcome",
                                "content": f"Welcome {username}! How can I help you?",
                                "style": {"fontSize": "1.5rem", "marginBottom": "1rem"}
                            },
                            {
                                "type": "input",
                                "id": "user_input",
                                "placeholder": "Describe what you want to do...",
                                "style": {"width": "100%", "padding": "0.5rem"}
                            },
                            {
                                "type": "button",
                                "id": "submit",
                                "content": "Generate Interface",
                                "actions": ["generate_ui"],
                                "style": {"backgroundColor": "#3b82f6", "color": "white"}
                            }
                        ]
                    },
                    "raw_response": ui_response
                }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse UI JSON: {e}")
            raise HTTPException(status_code=500, detail="Invalid UI description")
            
    except Exception as e:
        logger.error(f"UI generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ui/action")
async def handle_ui_action(request: Request):
    """Обработка действий от UI компонентов"""
    try:
        data = await request.json()
        action = data.get("action")
        component_id = data.get("component_id")
        payload = data.get("payload", {})
        
        username = await get_current_user(request)
        if not username:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Обрабатываем действия
        if action == "generate_ui":
            # Генерируем новый UI на основе действия
            return await generate_ui_interface(request)
        elif action == "reset_context":
            # Сброс контекста
            return {"success": True, "message": "Context reset"}
        elif action == "analyze_file":
            # Анализ файла
            return {"success": True, "message": "File analysis started"}
        elif action == "memory_search":
            # Поиск в памяти
            query = payload.get("query", "")
            return {"success": True, "results": []}
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"UI action error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 