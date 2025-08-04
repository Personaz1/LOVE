"""
Vision Tools - Компьютерное зрение для Guardian
Инструменты для работы с камерами, анализа изображений и обработки видео
"""

import os
import cv2
import base64
import logging
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import json

from ..utils.logger import Logger
from ..utils.error_handler import ErrorHandler

logger = Logger()
error_handler = ErrorHandler()

class VisionTools:
    """
    Инструменты для компьютерного зрения
    """
    
    def __init__(self):
        """Инициализация Vision Tools"""
        self.cameras = {}  # Словарь активных камер
        self.last_frames = {}  # Последние кадры с камер
        self.motion_detectors = {}  # Детекторы движения
        self.logger = logger
        self.error_handler = error_handler
        
        # Инициализация OpenCV
        try:
            cv2.__version__
            self.logger.info("📷 Vision Tools: OpenCV initialized successfully")
        except Exception as e:
            self.logger.error(f"❌ Vision Tools: OpenCV initialization failed - {e}")
    
    def capture_image(self, camera_id: str = "default") -> str:
        """
        Сделать снимок с камеры
        
        Args:
            camera_id: ID камеры (default, webcam, ip_camera)
            
        Returns:
            str: Путь к сохраненному изображению или сообщение об ошибке
        """
        try:
            # Определяем источник камеры
            if camera_id == "default" or camera_id == "webcam":
                source = 0  # Локальная веб-камера
            elif camera_id.startswith("rtsp://"):
                source = camera_id  # IP камера
            else:
                source = int(camera_id) if camera_id.isdigit() else camera_id
            
            # Открываем камеру
            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                return f"❌ Ошибка: Не удалось открыть камеру {camera_id}"
            
            # Делаем снимок
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return f"❌ Ошибка: Не удалось получить кадр с камеры {camera_id}"
            
            # Создаем папку для изображений если её нет
            os.makedirs("memory/captures", exist_ok=True)
            
            # Сохраняем изображение
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"memory/captures/capture_{camera_id}_{timestamp}.jpg"
            cv2.imwrite(filename, frame)
            
            # Обновляем симлинк на последний снимок
            latest_symlink = f"memory/captures/capture_{camera_id}_latest.jpg"
            try:
                if os.path.islink(latest_symlink) or os.path.exists(latest_symlink):
                    os.remove(latest_symlink)
                os.symlink(os.path.abspath(filename), latest_symlink)
            except Exception as e:
                self.logger.warning(f"⚠️ Не удалось создать симлинк на последний снимок: {e}")
            
            self.logger.info(f"📷 Vision Tools: Снимок сохранен - {filename}")
            return f"✅ Снимок сохранен: {filename}"
            
        except Exception as e:
            error_msg = f"❌ Ошибка при захвате изображения: {e}"
            self.logger.error(error_msg)
            return error_msg
    
    def analyze_image(self, image_path: str) -> str:
        """
        Базовый анализ изображения
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            str: Результат анализа
        """
        try:
            if not os.path.exists(image_path):
                return f"❌ Ошибка: Файл {image_path} не найден"
            
            # Загружаем изображение
            image = cv2.imread(image_path)
            if image is None:
                return f"❌ Ошибка: Не удалось загрузить изображение {image_path}"
            
            # Базовый анализ
            height, width = image.shape[:2]
            channels = image.shape[2] if len(image.shape) > 2 else 1
            
            # Простое определение движения (разность кадров)
            # TODO: Добавить более сложные алгоритмы
            
            analysis = {
                "dimensions": f"{width}x{height}",
                "channels": channels,
                "file_size": f"{os.path.getsize(image_path)} bytes",
                "timestamp": datetime.now().isoformat()
            }
            
            # Сохраняем результат анализа
            analysis_file = image_path.replace('.jpg', '_analysis.json')
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"🔍 Vision Tools: Анализ изображения завершен - {analysis_file}")
            return f"✅ Анализ изображения: {json.dumps(analysis, ensure_ascii=False)}"
            
        except Exception as e:
            error_msg = f"❌ Ошибка при анализе изображения: {e}"
            self.logger.error(error_msg)
            return error_msg
    
    def detect_motion(self, camera_id: str = "default", threshold: float = 25.0) -> str:
        """
        Детекция движения с камеры
        
        Args:
            camera_id: ID камеры
            threshold: Порог чувствительности
            
        Returns:
            str: Результат детекции
        """
        try:
            # Определяем источник камеры
            if camera_id == "default" or camera_id == "webcam":
                source = 0
            else:
                source = camera_id
            
            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                return f"❌ Ошибка: Не удалось открыть камеру {camera_id}"
            
            # Получаем два кадра для сравнения
            ret1, frame1 = cap.read()
            if not ret1:
                cap.release()
                return f"❌ Ошибка: Не удалось получить первый кадр"
            
            # Небольшая задержка
            import time
            time.sleep(0.1)
            
            ret2, frame2 = cap.read()
            cap.release()
            
            if not ret2:
                return f"❌ Ошибка: Не удалось получить второй кадр"
            
            # Конвертируем в оттенки серого
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            
            # Вычисляем разность
            diff = cv2.absdiff(gray1, gray2)
            
            # Применяем порог
            _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
            
            # Находим контуры
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Фильтруем контуры по размеру
            motion_detected = False
            for contour in contours:
                if cv2.contourArea(contour) > 500:  # Минимальная площадь
                    motion_detected = True
                    break
            
            result = {
                "motion_detected": motion_detected,
                "contours_found": len(contours),
                "threshold_used": threshold,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"🎯 Vision Tools: Детекция движения - {motion_detected}")
            return f"✅ Детекция движения: {json.dumps(result, ensure_ascii=False)}"
            
        except Exception as e:
            error_msg = f"❌ Ошибка при детекции движения: {e}"
            self.logger.error(error_msg)
            return error_msg
    
    def list_cameras(self) -> str:
        """
        Получить список доступных камер
        
        Returns:
            str: Список камер
        """
        try:
            cameras = []
            
            # Проверяем локальные камеры (0-9)
            for i in range(10):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        cameras.append({
                            "id": str(i),
                            "type": "local",
                            "status": "available"
                        })
                    cap.release()
            
            # Добавляем стандартные источники
            cameras.append({
                "id": "default",
                "type": "webcam",
                "status": "available"
            })
            
            result = {
                "cameras": cameras,
                "total_count": len(cameras),
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"📷 Vision Tools: Найдено камер - {len(cameras)}")
            return f"✅ Доступные камеры: {json.dumps(result, ensure_ascii=False)}"
            
        except Exception as e:
            error_msg = f"❌ Ошибка при поиске камер: {e}"
            self.logger.error(error_msg)
            return error_msg
    
    def get_camera_status(self, camera_id: str = "default") -> str:
        """
        Получить статус камеры
        
        Args:
            camera_id: ID камеры
            
        Returns:
            str: Статус камеры
        """
        try:
            if camera_id == "default":
                source = 0
            else:
                source = camera_id
            
            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                return f"❌ Камера {camera_id} недоступна"
            
            # Получаем информацию о камере
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # Пробуем получить кадр
            ret, frame = cap.read()
            cap.release()
            
            status = {
                "camera_id": camera_id,
                "available": ret,
                "resolution": f"{width}x{height}",
                "fps": fps,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"📷 Vision Tools: Статус камеры {camera_id} - {ret}")
            return f"✅ Статус камеры: {json.dumps(status, ensure_ascii=False)}"
            
        except Exception as e:
            error_msg = f"❌ Ошибка при получении статуса камеры: {e}"
            self.logger.error(error_msg)
            return error_msg

# Создаем экземпляр для использования
vision_tools = VisionTools() 