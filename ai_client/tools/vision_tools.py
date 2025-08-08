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
import requests

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

        # Инициализация Google Cloud Vision SDK (опционально через сервисный аккаунт)
        self._gcv_client = None
        try:
            from google.cloud import vision as gcv
            # Если переменная GOOGLE_APPLICATION_CREDENTIALS задана, клиент поднимется
            self._gcv_client = gcv.ImageAnnotatorClient()
            self.logger.info("✅ Google Cloud Vision SDK client initialized")
        except Exception as e:
            self.logger.warning(f"⚠️ Google Cloud Vision SDK unavailable: {e}")
    
    def capture_image(self, camera_id: str = "default", auto_analyze: bool = True) -> str:
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
            if auto_analyze:
                try:
                    analysis = self.analyze_image(filename)
                    return f"✅ Снимок сохранен: {filename}\n{analysis}"
                except Exception as e:
                    self.logger.warning(f"⚠️ Auto analysis failed: {e}")
            return f"✅ Снимок сохранен: {filename}"
            
        except Exception as e:
            error_msg = f"❌ Ошибка при захвате изображения: {e}"
            self.logger.error(error_msg)
            return error_msg
    
    def analyze_image(self, image_path: str) -> str:
        """
        Глубокий анализ изображения:
        - Базовые метрики (OpenCV)
        - Google Vision API (labels/text/faces/objects) — если настроен ключ
        - LLM-анализ (Gemini Vision) — при доступности квоты
        """
        try:
            if not os.path.exists(image_path):
                return f"❌ Ошибка: Файл {image_path} не найден"

            # Загружаем изображение
            image = cv2.imread(image_path)
            if image is None:
                return f"❌ Ошибка: Не удалось загрузить изображение {image_path}"

            # Базовые метрики
            height, width = image.shape[:2]
            channels = image.shape[2] if len(image.shape) > 2 else 1
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Резкость как дисперсия лапласиана
            sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            # Яркость и контраст
            brightness = float(np.mean(gray))
            contrast = float(np.std(gray))
            # Средний цвет
            avg_bgr = np.mean(np.mean(image, axis=0), axis=0)
            avg_color = {
                "b": float(avg_bgr[0]),
                "g": float(avg_bgr[1]),
                "r": float(avg_bgr[2]),
            }

            basic = {
                "dimensions": f"{width}x{height}",
                "channels": channels,
                "file_size": f"{os.path.getsize(image_path)} bytes",
                "sharpness": round(sharpness, 2),
                "brightness": round(brightness, 2),
                "contrast": round(contrast, 2),
                "avg_color_bgr": avg_color,
                "timestamp": datetime.now().isoformat()
            }

            # Google Vision API (опционально)
            gv_summary = None
            try:
                api_key = os.getenv('GOOGLE_CLOUD_VISION_API_KEY')
                if api_key:
                    with open(image_path, 'rb') as f:
                        content_b64 = base64.b64encode(f.read()).decode('utf-8')
                    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
                    request_data = {
                        "requests": [
                            {
                                "image": {"content": content_b64},
                                "features": [
                                    {"type": "LABEL_DETECTION", "maxResults": 10},
                                    {"type": "TEXT_DETECTION"},
                                    {"type": "FACE_DETECTION"},
                                    {"type": "OBJECT_LOCALIZATION", "maxResults": 10}
                                ]
                            }
                        ]
                    }
                    resp = requests.post(url, json=request_data, timeout=20)
                    if resp.status_code == 200:
                        data = resp.json().get('responses', [{}])[0]
                        labels = [x['description'] for x in data.get('labelAnnotations', [])]
                        objects = [x['name'] for x in data.get('localizedObjectAnnotations', [])]
                        text = data.get('textAnnotations', [{}])[0].get('description', '').strip() if data.get('textAnnotations') else ''
                        faces = len(data.get('faceAnnotations', [])) if data.get('faceAnnotations') else 0
                        gv_summary = {
                            "labels": labels[:10],
                            "objects": objects[:10],
                            "text_sample": text[:200],
                            "faces_detected": faces
                        }
                    else:
                        gv_summary = {"error": f"Vision API status {resp.status_code}"}
            except Exception as e:
                gv_summary = {"error": f"Vision API error: {e}"}

            # LLM-анализ через Gemini Vision (опционально)
            llm_summary = None
            try:
                from ..models.gemini_client import GeminiClient
                gemini = GeminiClient()
                # Граундим LLM фактами из GV и базовых метрик и используем Files API-путь
                gv_for_prompt = {
                    'labels': (gv_summary or {}).get('labels') if isinstance(gv_summary, dict) else None,
                    'objects': (gv_summary or {}).get('objects') if isinstance(gv_summary, dict) else None,
                    'faces_detected': (gv_summary or {}).get('faces_detected') if isinstance(gv_summary, dict) else None,
                    'text_sample': (gv_summary or {}).get('text_sample') if isinstance(gv_summary, dict) else None,
                }
                prompt_text = (
                    "Опиши изображение кратко и по фактам.; "
                    "1) опирайся на само изображение; 2) если не уверен — 'unknown'; 3) 5-8 пунктов, без воды.\n"
                    f"Детекторы: dimensions={basic['dimensions']}, faces={gv_for_prompt.get('faces_detected')}, "
                    f"labels={gv_for_prompt.get('labels')}, objects={gv_for_prompt.get('objects')}, text_sample={(gv_for_prompt.get('text_sample') or '')[:120]}"
                )
                llm_text = gemini.analyze_image_with_files_api(
                    image_path=image_path,
                    prompt_text=prompt_text,
                    preferred_model="gemini-1.5-pro"
                )
                # Фильтрация бесполезных дисклеймеров
                bad_markers = [
                    'text-based AI', 'cannot directly view', 'cannot see images',
                    'hypothetical', 'I do not have the ability to view images'
                ]
                if any(m.lower() in (llm_text or '').lower() for m in bad_markers):
                    llm_text = None
                llm_summary = llm_text
            except Exception as e:
                llm_summary = f"Gemini analysis unavailable: {e}"

            result = {
                "basic": basic,
                "google_vision": gv_summary,
                "llm": llm_summary
            }

            # Лог и возврат
            analysis_file = image_path.rsplit('.', 1)[0] + '_analysis.json'
            try:
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

            self.logger.info(f"🔍 Vision Tools: Глубокий анализ изображения завершен - {analysis_file}")
            # Краткий исчерпывающий ответ для чата
            summary_lines = [
                f"Размер: {basic['dimensions']}, яркость: {basic['brightness']}, контраст: {basic['contrast']}, резкость: {basic['sharpness']}",
            ]
            if isinstance(gv_summary, dict) and not gv_summary.get('error'):
                if gv_summary.get('labels'):
                    summary_lines.append("GV labels: " + ", ".join(gv_summary['labels'][:5]))
                if gv_summary.get('objects'):
                    summary_lines.append("GV objects: " + ", ".join(gv_summary['objects'][:5]))
                if gv_summary.get('text_sample'):
                    summary_lines.append("GV text: " + gv_summary['text_sample'].replace('\n',' ')[:120])
                summary_lines.append(f"GV faces: {gv_summary.get('faces_detected', 0)}")
            elif isinstance(gv_summary, dict) and gv_summary.get('error'):
                summary_lines.append(gv_summary['error'])

            if isinstance(llm_summary, str) and llm_summary.strip():
                summary_lines.append("LLM: " + (llm_summary[:400] + ("..." if len(llm_summary) > 400 else "")))

            return "✅ Анализ изображения:\n" + "\n".join(summary_lines)

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

    # ===== Cloud Vision Adapters (официальный SDK) =====
    def vision_labels(self, image_path: str, max_results: int = 10) -> str:
        try:
            if not self._gcv_client:
                return "❌ Cloud Vision SDK not configured (set GOOGLE_APPLICATION_CREDENTIALS)"
            if not os.path.exists(image_path):
                return f"❌ File not found: {image_path}"
            from google.cloud import vision as gcv
            with open(image_path, 'rb') as f:
                content = f.read()
            image = gcv.Image(content=content)
            response = self._gcv_client.label_detection(image=image, max_results=max_results)
            labels = [l.description for l in response.label_annotations or []]
            return "✅ GV Labels: " + ", ".join(labels)
        except Exception as e:
            return f"❌ GV Labels error: {e}"

    def vision_objects(self, image_path: str, max_results: int = 10) -> str:
        try:
            if not self._gcv_client:
                return "❌ Cloud Vision SDK not configured (set GOOGLE_APPLICATION_CREDENTIALS)"
            if not os.path.exists(image_path):
                return f"❌ File not found: {image_path}"
            from google.cloud import vision as gcv
            with open(image_path, 'rb') as f:
                content = f.read()
            image = gcv.Image(content=content)
            response = self._gcv_client.object_localization(image=image)
            objs = []
            for o in response.localized_object_annotations or []:
                pts = [(round(v.x,3), round(v.y,3)) for v in o.bounding_poly.normalized_vertices]
                objs.append(f"{o.name}:{pts}")
                if len(objs) >= max_results:
                    break
            return "✅ GV Objects: " + ("; ".join(objs) if objs else "none")
        except Exception as e:
            return f"❌ GV Objects error: {e}"

    def vision_ocr(self, image_path: str) -> str:
        try:
            if not self._gcv_client:
                return "❌ Cloud Vision SDK not configured (set GOOGLE_APPLICATION_CREDENTIALS)"
            if not os.path.exists(image_path):
                return f"❌ File not found: {image_path}"
            from google.cloud import vision as gcv
            with open(image_path, 'rb') as f:
                content = f.read()
            image = gcv.Image(content=content)
            response = self._gcv_client.text_detection(image=image)
            annotations = response.text_annotations or []
            text = annotations[0].description if annotations else ""
            return "✅ GV OCR: " + (text.strip()[:2000])
        except Exception as e:
            return f"❌ GV OCR error: {e}"

# Создаем экземпляр для использования
vision_tools = VisionTools() 