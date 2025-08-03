"""
ΔΣ Guardian Self Modification v4.0
Безопасная самомодификация и самоэволюция
"""

import os
import json
import logging
import subprocess
import git
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import shutil

from ai_client.core.client import AIClient
from ai_client.utils.logger import Logger
from core.scheduler import scheduler, TaskPriority

logger = Logger()

class ModificationType(Enum):
    CODE_CHANGE = "code_change"
    CONFIG_UPDATE = "config_update"
    FILE_CREATE = "file_create"
    FILE_DELETE = "file_delete"
    DEPENDENCY_UPDATE = "dependency_update"
    SYSTEM_UPDATE = "system_update"

class ModificationStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERTED = "reverted"

@dataclass
class Modification:
    id: str
    type: ModificationType
    target: str
    description: str
    changes: Dict[str, Any]
    status: ModificationStatus
    created_at: datetime
    executed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    backup_path: Optional[str] = None
    safety_score: float = 0.0
    approval_required: bool = True

class SelfModification:
    """Система безопасной самомодификации для ΔΣ Guardian"""
    
    def __init__(self):
        self.ai_client = AIClient()
        self.modifications: Dict[str, Modification] = {}
        self.safe_directories = [
            "ai_client/",
            "memory/",
            "core/",
            "static/",
            "templates/"
        ]
        self.dangerous_patterns = [
            "rm -rf",
            "format",
            "delete",
            "drop",
            "truncate",
            "sudo",
            "chmod 777"
        ]
        self.backup_dir = "backups/"
        self.max_backups = 10
        
        # Создаем директорию для бэкапов
        os.makedirs(self.backup_dir, exist_ok=True)
        
        logger.info("🔧 ΔΣ Self Modification initialized")
    
    def propose_modification(self, mod_type: ModificationType, target: str, 
                           description: str, changes: Dict[str, Any]) -> str:
        """Предложение модификации"""
        mod_id = f"mod_{int(datetime.now().timestamp() * 1000)}"
        
        # Оцениваем безопасность
        safety_score = self._assess_safety(mod_type, target, changes)
        approval_required = safety_score < 0.7
        
        modification = Modification(
            id=mod_id,
            type=mod_type,
            target=target,
            description=description,
            changes=changes,
            status=ModificationStatus.PENDING,
            created_at=datetime.now(),
            safety_score=safety_score,
            approval_required=approval_required
        )
        
        self.modifications[mod_id] = modification
        logger.info(f"📝 Modification proposed: {description} (safety: {safety_score:.2f})")
        
        # Автоматически выполняем если безопасно
        if not approval_required:
            self.execute_modification(mod_id)
        
        return mod_id
    
    def _assess_safety(self, mod_type: ModificationType, target: str, 
                      changes: Dict[str, Any]) -> float:
        """Оценка безопасности модификации"""
        safety_score = 1.0
        
        # Проверяем тип модификации
        if mod_type == ModificationType.SYSTEM_UPDATE:
            safety_score -= 0.3
        elif mod_type == ModificationType.FILE_DELETE:
            safety_score -= 0.2
        
        # Проверяем цель
        if not any(target.startswith(safe_dir) for safe_dir in self.safe_directories):
            safety_score -= 0.4
        
        # Проверяем содержимое изменений
        changes_str = json.dumps(changes, ensure_ascii=False).lower()
        for pattern in self.dangerous_patterns:
            if pattern in changes_str:
                safety_score -= 0.5
        
        # Проверяем размер изменений
        if len(changes_str) > 10000:  # Большие изменения
            safety_score -= 0.1
        
        return max(0.0, safety_score)
    
    def approve_modification(self, mod_id: str) -> bool:
        """Одобрение модификации"""
        if mod_id not in self.modifications:
            return False
        
        modification = self.modifications[mod_id]
        modification.status = ModificationStatus.APPROVED
        
        logger.info(f"✅ Modification approved: {modification.description}")
        
        # Выполняем модификацию
        return self.execute_modification(mod_id)
    
    def execute_modification(self, mod_id: str) -> bool:
        """Выполнение модификации"""
        if mod_id not in self.modifications:
            return False
        
        modification = self.modifications[mod_id]
        modification.status = ModificationStatus.EXECUTING
        modification.executed_at = datetime.now()
        
        logger.info(f"🚀 Executing modification: {modification.description}")
        
        try:
            # Создаем бэкап
            backup_path = self._create_backup(modification.target)
            modification.backup_path = backup_path
            
            # Выполняем модификацию
            result = self._execute_modification(modification)
            
            modification.result = result
            modification.status = ModificationStatus.COMPLETED
            
            logger.info(f"✅ Modification completed: {modification.description}")
            
            # Создаем задачу для коммита в git
            scheduler.create_task(
                name="git_commit_modification",
                description=f"Commit modification: {modification.description}",
                priority=TaskPriority.NORMAL,
                task_type="git_commit",
                context={"modification_id": mod_id}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Modification failed: {modification.description} - {str(e)}")
            modification.status = ModificationStatus.FAILED
            modification.error = str(e)
            
            # Восстанавливаем из бэкапа
            if modification.backup_path:
                self._restore_backup(modification.backup_path, modification.target)
            
            return False
    
    def _create_backup(self, target: str) -> str:
        """Создание бэкапа"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{target.replace('/', '_')}_{timestamp}.backup"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        if os.path.exists(target):
            if os.path.isfile(target):
                shutil.copy2(target, backup_path)
            else:
                shutil.copytree(target, backup_path)
        
        logger.info(f"💾 Backup created: {backup_path}")
        return backup_path
    
    def _restore_backup(self, backup_path: str, target: str):
        """Восстановление из бэкапа"""
        try:
            if os.path.exists(target):
                if os.path.isfile(target):
                    os.remove(target)
                else:
                    shutil.rmtree(target)
            
            if os.path.isfile(backup_path):
                shutil.copy2(backup_path, target)
            else:
                shutil.copytree(backup_path, target)
            
            logger.info(f"🔄 Backup restored: {target}")
        except Exception as e:
            logger.error(f"❌ Backup restore failed: {e}")
    
    def _execute_modification(self, modification: Modification) -> Dict[str, Any]:
        """Выполнение конкретной модификации"""
        mod_type = modification.type
        target = modification.target
        changes = modification.changes
        
        if mod_type == ModificationType.CODE_CHANGE:
            return self._execute_code_change(target, changes)
        elif mod_type == ModificationType.CONFIG_UPDATE:
            return self._execute_config_update(target, changes)
        elif mod_type == ModificationType.FILE_CREATE:
            return self._execute_file_create(target, changes)
        elif mod_type == ModificationType.FILE_DELETE:
            return self._execute_file_delete(target)
        elif mod_type == ModificationType.DEPENDENCY_UPDATE:
            return self._execute_dependency_update(target, changes)
        elif mod_type == ModificationType.SYSTEM_UPDATE:
            return self._execute_system_update(target, changes)
        else:
            raise ValueError(f"Unknown modification type: {mod_type}")
    
    def _execute_code_change(self, target: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Изменение кода"""
        if not os.path.exists(target):
            return {"error": f"Target file not found: {target}"}
        
        try:
            with open(target, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Применяем изменения
            new_content = self._apply_code_changes(original_content, changes)
            
            with open(target, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return {
                "success": True,
                "file_modified": target,
                "changes_applied": len(changes)
            }
        except Exception as e:
            return {"error": f"Code change failed: {str(e)}"}
    
    def _apply_code_changes(self, content: str, changes: Dict[str, Any]) -> str:
        """Применение изменений к коду"""
        # Простая замена текста
        if "replace" in changes:
            for old_text, new_text in changes["replace"].items():
                content = content.replace(old_text, new_text)
        
        # Добавление в конец файла
        if "append" in changes:
            content += "\n" + changes["append"]
        
        # Вставка в определенное место
        if "insert" in changes:
            for marker, text in changes["insert"].items():
                if marker in content:
                    content = content.replace(marker, marker + "\n" + text)
        
        return content
    
    def _execute_config_update(self, target: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Обновление конфигурации"""
        try:
            if target.endswith('.json'):
                with open(target, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Обновляем конфигурацию
                config.update(changes)
                
                with open(target, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            else:
                # Для других форматов используем AI
                return self._ai_config_update(target, changes)
            
            return {
                "success": True,
                "config_updated": target,
                "changes": changes
            }
        except Exception as e:
            return {"error": f"Config update failed: {str(e)}"}
    
    def _ai_config_update(self, target: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        """AI-обновление конфигурации"""
        prompt = f"""
        Обнови конфигурационный файл {target} следующими изменениями:
        {json.dumps(changes, ensure_ascii=False)}
        
        Верни обновленное содержимое файла.
        """
        
        response = self.ai_client.chat(prompt)
        
        try:
            with open(target, 'w', encoding='utf-8') as f:
                f.write(response)
            
            return {
                "success": True,
                "config_updated": target,
                "ai_generated": True
            }
        except Exception as e:
            return {"error": f"AI config update failed: {str(e)}"}
    
    def _execute_file_create(self, target: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Создание файла"""
        try:
            # Создаем директории если нужно
            os.makedirs(os.path.dirname(target), exist_ok=True)
            
            content = changes.get("content", "")
            if not content and "ai_generate" in changes:
                # Генерируем содержимое через AI
                prompt = changes["ai_generate"]
                content = self.ai_client.chat(prompt)
            
            with open(target, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "file_created": target,
                "content_length": len(content)
            }
        except Exception as e:
            return {"error": f"File creation failed: {str(e)}"}
    
    def _execute_file_delete(self, target: str) -> Dict[str, Any]:
        """Удаление файла"""
        try:
            if os.path.exists(target):
                if os.path.isfile(target):
                    os.remove(target)
                else:
                    shutil.rmtree(target)
                
                return {
                    "success": True,
                    "file_deleted": target
                }
            else:
                return {"warning": f"File not found: {target}"}
        except Exception as e:
            return {"error": f"File deletion failed: {str(e)}"}
    
    def _execute_dependency_update(self, target: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Обновление зависимостей"""
        try:
            if target == "requirements.txt":
                # Обновляем requirements.txt
                with open(target, 'r') as f:
                    requirements = f.read().splitlines()
                
                for package, version in changes.items():
                    # Ищем и обновляем пакет
                    for i, req in enumerate(requirements):
                        if req.startswith(package + "=="):
                            requirements[i] = f"{package}=={version}"
                            break
                    else:
                        requirements.append(f"{package}=={version}")
                
                with open(target, 'w') as f:
                    f.write('\n'.join(requirements))
                
                return {
                    "success": True,
                    "dependencies_updated": changes
                }
            else:
                return {"error": f"Unknown dependency file: {target}"}
        except Exception as e:
            return {"error": f"Dependency update failed: {str(e)}"}
    
    def _execute_system_update(self, target: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Системное обновление"""
        try:
            # Создаем задачу для системного обновления
            scheduler.create_task(
                name="system_update",
                description=f"System update: {target}",
                priority=TaskPriority.CRITICAL,
                task_type="system_update",
                context={"target": target, "changes": changes}
            )
            
            return {
                "success": True,
                "update_scheduled": True,
                "target": target
            }
        except Exception as e:
            return {"error": f"System update failed: {str(e)}"}
    
    def get_modification_status(self, mod_id: str) -> Dict[str, Any]:
        """Получение статуса модификации"""
        if mod_id not in self.modifications:
            return {"error": "Modification not found"}
        
        modification = self.modifications[mod_id]
        return {
            "id": modification.id,
            "type": modification.type.value,
            "target": modification.target,
            "description": modification.description,
            "status": modification.status.value,
            "safety_score": modification.safety_score,
            "approval_required": modification.approval_required,
            "created_at": modification.created_at.isoformat(),
            "executed_at": modification.executed_at.isoformat() if modification.executed_at else None
        }
    
    def get_all_modifications(self) -> List[Dict[str, Any]]:
        """Получение всех модификаций"""
        return [self.get_modification_status(mid) for mid in self.modifications.keys()]
    
    def revert_modification(self, mod_id: str) -> bool:
        """Откат модификации"""
        if mod_id not in self.modifications:
            return False
        
        modification = self.modifications[mod_id]
        
        if modification.backup_path and os.path.exists(modification.backup_path):
            try:
                self._restore_backup(modification.backup_path, modification.target)
                modification.status = ModificationStatus.REVERTED
                logger.info(f"🔄 Modification reverted: {modification.description}")
                return True
            except Exception as e:
                logger.error(f"❌ Revert failed: {e}")
                return False
        else:
            logger.error(f"❌ No backup available for: {modification.description}")
            return False
    
    def cleanup_old_backups(self):
        """Очистка старых бэкапов"""
        try:
            backup_files = os.listdir(self.backup_dir)
            backup_files.sort(key=lambda x: os.path.getctime(os.path.join(self.backup_dir, x)))
            
            # Удаляем старые бэкапы
            if len(backup_files) > self.max_backups:
                for old_backup in backup_files[:-self.max_backups]:
                    old_path = os.path.join(self.backup_dir, old_backup)
                    os.remove(old_path)
                    logger.info(f"🗑️ Removed old backup: {old_backup}")
        except Exception as e:
            logger.error(f"❌ Backup cleanup failed: {e}")

# Глобальный экземпляр самомодификации
self_modification = SelfModification() 