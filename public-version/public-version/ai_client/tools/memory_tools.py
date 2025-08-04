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
    
    def update_current_feeling(self, username: str, feeling: str, context: str = "") -> bool:
        """Обновление текущего чувства пользователя"""
        try:
            profile_path = os.path.join(self.project_root, 'memory', 'user_profiles', f'{username}.json')
            
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
            else:
                profile = {'username': username}
            
            # Сохраняем предыдущее чувство
            previous_feeling = profile.get('current_feeling', 'unknown')
            
            # Обновляем чувство
            profile['current_feeling'] = feeling
            profile['last_updated'] = datetime.now().isoformat()
            
            # Добавляем в историю эмоций
            if 'emotional_history' not in profile:
                profile['emotional_history'] = []
            
            emotional_entry = {
                'feeling': feeling,
                'previous_feeling': previous_feeling,
                'context': context,
                'timestamp': datetime.now().isoformat()
            }
            profile['emotional_history'].append(emotional_entry)
            
            # Сохраняем профиль
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💭 Updated feeling for {username}: {feeling}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating feeling for {username}: {e}")
            return False
    
    def update_relationship_status(self, username: str, status: str) -> bool:
        """Обновление статуса отношений"""
        try:
            profile_path = os.path.join(self.project_root, 'memory', 'user_profiles', f'{username}.json')
            
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
            else:
                profile = {'username': username}
            
            profile['relationship_status'] = status
            profile['last_updated'] = datetime.now().isoformat()
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💕 Updated relationship status for {username}: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating relationship status for {username}: {e}")
            return False
    
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
    
    def add_relationship_insight(self, username: str, insight: str) -> bool:
        """Добавление инсайта о отношениях"""
        try:
            profile_path = os.path.join(self.project_root, 'memory', 'user_profiles', f'{username}.json')
            
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
            else:
                profile = {'username': username}
            
            if 'relationship_insights' not in profile:
                profile['relationship_insights'] = []
            
            insight_entry = {
                'insight': insight,
                'timestamp': datetime.now().isoformat()
            }
            profile['relationship_insights'].append(insight_entry)
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💡 Added relationship insight for {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding relationship insight for {username}: {e}")
            return False
    
    def add_model_note(self, note_text: str, category: str = "general") -> bool:
        """Добавление заметки модели"""
        try:
            notes_path = os.path.join(self.project_root, 'memory', 'model_notes.json')
            
            if os.path.exists(notes_path):
                with open(notes_path, 'r', encoding='utf-8') as f:
                    notes = json.load(f)
            else:
                notes = {'notes': []}
            
            note_entry = {
                'text': note_text,
                'category': category,
                'timestamp': datetime.now().isoformat()
            }
            notes['notes'].append(note_entry)
            
            with open(notes_path, 'w', encoding='utf-8') as f:
                json.dump(notes, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📝 Added model note: {note_text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error adding model note: {e}")
            return False
    
    def add_user_observation(self, username: str, observation: str) -> bool:
        """Добавление наблюдения о пользователе"""
        try:
            profile_path = os.path.join(self.project_root, 'memory', 'user_profiles', f'{username}.json')
            
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
            else:
                profile = {'username': username}
            
            if 'observations' not in profile:
                profile['observations'] = []
            
            observation_entry = {
                'observation': observation,
                'timestamp': datetime.now().isoformat()
            }
            profile['observations'].append(observation_entry)
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            
            logger.info(f"👁️ Added observation for {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding observation for {username}: {e}")
            return False
    
    def add_personal_thought(self, thought: str) -> bool:
        """Добавление личной мысли"""
        try:
            thoughts_path = os.path.join(self.project_root, 'memory', 'personal_thoughts.json')
            
            if os.path.exists(thoughts_path):
                with open(thoughts_path, 'r', encoding='utf-8') as f:
                    thoughts = json.load(f)
            else:
                thoughts = {'thoughts': []}
            
            thought_entry = {
                'thought': thought,
                'timestamp': datetime.now().isoformat()
            }
            thoughts['thoughts'].append(thought_entry)
            
            with open(thoughts_path, 'w', encoding='utf-8') as f:
                json.dump(thoughts, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💭 Added personal thought")
            return True
            
        except Exception as e:
            logger.error(f"Error adding personal thought: {e}")
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
    
    def get_model_notes(self, limit: int = 20) -> str:
        """Получение заметок модели"""
        try:
            notes_path = os.path.join(self.project_root, 'memory', 'model_notes.json')
            
            if not os.path.exists(notes_path):
                return "No model notes found"
            
            with open(notes_path, 'r', encoding='utf-8') as f:
                notes = json.load(f)
            
            # Обрабатываем как список или словарь
            if isinstance(notes, list):
                # Если это список заметок
                recent_notes = notes[-limit:] if len(notes) > limit else notes
                result = "📝 Recent Model Notes:\n"
                for note in recent_notes:
                    if isinstance(note, dict):
                        timestamp = note.get('timestamp', 'unknown')
                        text = note.get('note', note.get('text', 'no text'))
                        category = note.get('category', 'general')
                        result += f"{timestamp}: {text} [{category}]\n"
                    else:
                        result += f"Invalid note format: {note}\n"
                return result
            elif isinstance(notes, dict):
                # Если это словарь с ключом 'notes'
                if not notes.get('notes'):
                    return "No model notes found"
                
                recent_notes = notes['notes'][-limit:]
                result = "📝 Recent Model Notes:\n"
                for note in recent_notes:
                    if isinstance(note, dict):
                        timestamp = note.get('timestamp', 'unknown')
                        text = note.get('text', 'no text')
                        category = note.get('category', 'general')
                        result += f"{timestamp}: {text} [{category}]\n"
                    else:
                        result += f"Invalid note format: {note}\n"
                return result
            else:
                return "Invalid model notes format"
            
        except Exception as e:
            logger.error(f"Error getting model notes: {e}")
            return f"❌ Error getting model notes: {str(e)}"
    
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
    
    def read_emotional_history(self, username: str) -> str:
        """Чтение эмоциональной истории"""
        try:
            profile_path = os.path.join(self.project_root, 'memory', 'user_profiles', f'{username}.json')
            
            if not os.path.exists(profile_path):
                return f"❌ Profile not found for {username}"
            
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            emotional_history = profile.get('emotional_history', [])
            
            if not emotional_history:
                return f"No emotional history found for {username}"
            
            result = f"💭 Emotional History for {username}:\n"
            for entry in emotional_history[-10:]:  # Последние 10 записей
                timestamp = entry['timestamp']
                feeling = entry['feeling']
                previous = entry.get('previous_feeling', 'unknown')
                context = entry.get('context', '')
                result += f"{timestamp}: {feeling} (was {previous}) {context}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error reading emotional history for {username}: {e}")
            return f"❌ Error reading emotional history: {str(e)}"
    
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
                    feeling = profile.get('current_feeling', 'unknown')
                    last_updated = profile.get('last_updated', 'unknown')
                    
                    context_parts.append(f"👤 {name} ({username}): feeling {feeling}, updated {last_updated}")
            
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