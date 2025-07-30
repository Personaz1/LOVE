# Система обработки изображений FAMILY

## Обзор

Система обработки изображений FAMILY интегрирована в `ai_client.py` и использует многоуровневый подход:

1. **Gemini Pro Vision** - основная модель для анализа изображений
2. **Google Cloud Vision API** - fallback для слабых моделей или при превышении квоты
3. **Автоматическое переключение** между моделями по квоте

## Архитектура

### Модели (от самых мощных к слабым)

```python
models = [
    {
        'name': 'gemini-2.5-pro',      # Самая мощная модель
        'quota': 100,
        'vision': True
    },
    {
        'name': 'gemini-1.5-pro',      # Pro модель с vision
        'quota': 150,
        'vision': True
    },
    {
        'name': 'gemini-2.5-flash',    # Flash модель с vision
        'quota': 250,
        'vision': True
    },
    {
        'name': 'gemini-1.5-flash',    # Flash модель с vision
        'quota': 500,
        'vision': True
    },
    {
        'name': 'gemini-2.0-flash',    # Flash модель с vision
        'quota': 200,
        'vision': True
    },
    {
        'name': 'gemini-2.0-flash-lite', # Lite без vision
        'quota': 1000,
        'vision': False
    },
    {
        'name': 'gemini-2.5-flash-lite', # Lite без vision
        'quota': 1000,
        'vision': False
    }
]
```

### Процесс анализа изображений

1. **Проверка текущей модели** - если у неё есть vision capabilities
2. **Попытка анализа через Gemini** - с детальным промптом
3. **Fallback на Google Cloud Vision API** - если Gemini недоступен
4. **Возврат результата** - с контекстом пользователя

## API Endpoints

### Анализ изображения
```http
POST /api/analyze-image
Content-Type: application/json

{
    "file_path": "/static/images/example.jpg",
    "file_name": "example.jpg",
    "user_context": "Optional user context"
}
```

### Статус системы
```http
GET /api/image-analyzer/status
```

### Переключение модели
```http
POST /api/model/switch
Content-Type: application/json

{
    "model_name": "gemini-1.5-pro"
}
```

## Конфигурация

### Переменные окружения

```bash
# Обязательные
GEMINI_API_KEY=your_gemini_api_key

# Опциональные (для Google Cloud Vision API)
GOOGLE_CLOUD_VISION_API_KEY=AIzaSyCxdKfHptmqDDdLHSx8C2xOhjg9RLjCm_w
```

### Зависимости

```txt
google-generativeai>=0.3.0
google-cloud-vision>=3.4.0
requests>=2.31.0
```

## Использование

### В коде

```python
from ai_client import AIClient

ai_client = AIClient()

# Анализ изображения
result = ai_client.analyze_image("path/to/image.jpg", "User context")
print(result)

# Статус системы
status = ai_client.get_model_status()
print(f"Current model: {status['current_model']}")
print(f"Vision API available: {status['vision_client_available']}")
```

### В веб-интерфейсе

1. Загрузите изображение через интерфейс
2. Система автоматически проанализирует его
3. Результат будет показан в чате

## Возможности анализа

### Gemini Vision
- Детальное описание изображения
- Анализ эмоционального воздействия
- Контекст для отношений
- Понимание сложных сцен

### Google Cloud Vision API
- **Label Detection** - объекты и сцены
- **Text Detection (OCR)** - извлечение текста
- **Face Detection** - обнаружение лиц
- **Safe Search** - проверка контента

## Обработка ошибок

### Quota Exceeded
- Автоматическое переключение на следующую модель
- Fallback на Google Cloud Vision API
- Логирование ошибок для мониторинга

### Vision API недоступен
- Использование только Gemini моделей
- Graceful degradation

## Мониторинг

### Логи
```python
# Включить детальное логирование
import logging
logging.basicConfig(level=logging.INFO)
```

### Статус системы
```python
status = ai_client.get_model_status()
print(f"Model errors: {status['model_errors']}")
print(f"Available models: {len(status['available_models'])}")
```

## Тестирование

```bash
python3 test_vision_system.py
```

Этот скрипт проверит:
- Инициализацию системы
- Доступность моделей
- Анализ тестового изображения
- Работу fallback механизмов

## Устранение неполадок

### "No vision capabilities available"
- Проверьте, что текущая модель имеет `vision: True`
- Убедитесь, что Google Cloud Vision API настроен

### "Vision API request failed"
- Проверьте API ключ Google Cloud Vision
- Убедитесь, что изображение корректно загружено

### "Quota exceeded"
- Это нормально - система автоматически переключится
- Проверьте логи для деталей

## Будущие улучшения

1. **Кэширование результатов** - для повторных анализов
2. **Batch processing** - для множественных изображений
3. **Custom models** - для специфических задач
4. **Advanced OCR** - для сложных документов
5. **Image generation** - с помощью Imagen API 