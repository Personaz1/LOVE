"""
Инструменты для работы с памятью
"""

import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..utils.config import Config
from ..utils.logger import Logger
from ..utils.error_handler import ErrorHandler

logger = Logger()

class MemoryTools:
    """Класс для работы с памятью системы"""
    
    def __init__(self):
        """Инициализация MemoryTools"""
        self.config = Config()
        self.error_handler = ErrorHandler()
        self.project_root = self.config.get_project_root()
    

    

    
    def update_user_profile(self, username: str, new_profile_text: str) -> bool:
        """Обновление профиля пользователя"""
        try:
            profile_path = os.path.join(self.project_root, 'memory', 'user_profiles', f'{username}.json')
            
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
            else:
                profile = {'username': username}
            
            profile['profile'] = new_profile_text
            profile['last_updated'] = datetime.now().isoformat()
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            
            logger.info(f"👤 Updated profile for {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating profile for {username}: {e}")
            return False
    

    

    
    def add_system_insight(self, insight: str) -> bool:
        """Добавление системного инсайта"""
        try:
            insights_path = os.path.join(self.project_root, 'memory', 'system_insights.json')
            
            if os.path.exists(insights_path):
                with open(insights_path, 'r', encoding='utf-8') as f:
                    insights = json.load(f)
            else:
                insights = {'insights': []}
            
            insight_entry = {
                'insight': insight,
                'timestamp': datetime.now().isoformat()
            }
            insights['insights'].append(insight_entry)
            
            with open(insights_path, 'w', encoding='utf-8') as f:
                json.dump(insights, f, indent=2, ensure_ascii=False)
            
            logger.info(f"🧠 Added system insight")
            return True
            
        except Exception as e:
            logger.error(f"Error adding system insight: {e}")
            return False
    

    
    def read_user_profile(self, username: str) -> str:
        """Чтение профиля пользователя"""
        try:
            profile_path = os.path.join(self.project_root, 'memory', 'user_profiles', f'{username}.json')
            
            if not os.path.exists(profile_path):
                return f"❌ Profile not found for {username}"
            
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            return json.dumps(profile, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error reading profile for {username}: {e}")
            return f"❌ Error reading profile: {str(e)}"
    

    
    def write_insight_to_file(self, username: str, insight: str) -> bool:
        """Запись инсайта в файл"""
        try:
            insights_dir = os.path.join(self.project_root, 'guardian_sandbox', 'insights')
            os.makedirs(insights_dir, exist_ok=True)
            
            insight_file = os.path.join(insights_dir, f'{username}_insights.txt')
            
            with open(insight_file, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().isoformat()}] {insight}\n")
            
            logger.info(f"💡 Wrote insight for {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing insight for {username}: {e}")
            return False
    
    def search_user_data(self, username: str, query: str) -> str:
        """Поиск данных пользователя"""
        try:
            profile_path = os.path.join(self.project_root, 'memory', 'user_profiles', f'{username}.json')
            
            if not os.path.exists(profile_path):
                return f"❌ Profile not found for {username}"
            
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            results = []
            query_lower = query.lower()
            
            # Поиск в профиле
            for key, value in profile.items():
                if isinstance(value, str) and query_lower in value.lower():
                    results.append(f"Profile.{key}: {value}")
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            for item_key, item_value in item.items():
                                if isinstance(item_value, str) and query_lower in item_value.lower():
                                    results.append(f"Profile.{key}.{item_key}: {item_value}")
            
            if results:
                return f"🔍 Search results for '{query}' in {username}'s data:\n" + "\n".join(results)
            else:
                return f"🔍 No matches found for '{query}' in {username}'s data"
            
        except Exception as e:
            logger.error(f"Error searching user data for {username}: {e}")
            return f"❌ Error searching user data: {str(e)}"
    
    def _get_multi_user_context(self) -> str:
        """Получение контекста нескольких пользователей"""
        try:
            profiles_dir = os.path.join(self.project_root, 'memory', 'user_profiles')
            
            if not os.path.exists(profiles_dir):
                return "No user profiles found"
            
            context_parts = []
            
            for filename in os.listdir(profiles_dir):
                if filename.endswith('.json'):
                    username = filename[:-5]  # Убираем .json
                    profile_path = os.path.join(profiles_dir, filename)
                    
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile = json.load(f)
                    
                    # Извлекаем ключевую информацию
                    name = profile.get('full_name', username)
        
                    last_updated = profile.get('last_updated', 'unknown')
                    
                    context_parts.append(f"👤 {name} ({username}): updated {last_updated}")
            
            if context_parts:
                return "Multi-user context:\n" + "\n".join(context_parts)
            else:
                return "No user profiles found"
            
        except Exception as e:
            logger.error(f"Error getting multi-user context: {e}")
            return f"❌ Error getting multi-user context: {str(e)}"
    
    # Vector memory методы (заглушки)
    def store_embedding_memory(self, text: str, label: str = "general") -> bool:
        """Сохранение в векторную память"""
        # TODO: Реализовать векторную память
        logger.info(f"🧠 Stored embedding: {text[:50]}... [{label}]")
        return True
    
    def search_embedding_memory(self, query: str, top_k: int = 5) -> str:
        """Поиск в векторной памяти"""
        # TODO: Реализовать векторную память
        return f"🔍 Vector memory search for '{query}' (not implemented)"
    
    def summarize_conversation(self, conversation_history: List[str]) -> str:
        """Суммаризация разговора"""
        # TODO: Реализовать суммаризацию
        return f"📝 Conversation summary (not implemented)"
    
    def get_memory_stats(self) -> str:
        """Получение статистики памяти"""
        # TODO: Реализовать статистику
        return "📊 Memory statistics (not implemented)"
    
    def clear_vector_memory(self) -> bool:
        """Очистка векторной памяти"""
        # TODO: Реализовать очистку
        logger.info("🧹 Cleared vector memory (not implemented)")
        return True 