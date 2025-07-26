# Dr. Harmony - Логирование и Функции

## 🔍 Система логирования

### Временные метки:
- **🚀 Start** - Начало генерации ответа
- **📝 Prompt** - Время построения промпта
- **🌐 API** - Время API вызова к Gemini
- **✅ Success** - Успешное завершение
- **❌ Error** - Ошибки с временем выполнения

### Пример логов:
```
🚀 Starting AI response generation for: can you pls change my Communication Style...
🤖 Using Gemini as primary engine
📝 Prompt built in 0.02s
📏 Prompt length: 2847 characters
🌐 Making Gemini API call...
🌐 Gemini API call completed in 2.34s
✅ Gemini response generated successfully
📝 Raw response length: 156 characters
🔍 Processing response for function calls...
🔄 Detected profile update request
💬 Communication style update result: True
✅ Response processing completed
✅ AI response generated in 2.38s
📝 Response length: 156 characters
```

## 🔧 Механизм выполнения функций

### Обнаружение запросов:
- **"change my"** - Запрос на изменение
- **"update my"** - Запрос на обновление
- **"love language"** - Изменение языка любви
- **"communication style"** - Изменение стиля общения
- **"relationship status"** - Изменение статуса отношений

### Поддерживаемые обновления:

#### Язык любви:
```python
# Качество времени
"change my love language to quality time"
→ "Quality time and acts of service"

# Слова поддержки
"change my love language to words of affirmation"  
→ "Words of affirmation and physical touch"

# Физический контакт
"change my love language to physical touch"
→ "Physical touch and quality time"
```

#### Стиль общения:
```python
# Эмоциональный
"change my Communication Style to just Emotional"
→ "Emotional"

# Прямой
"change my communication style to direct"
→ "Direct and clear"
```

#### Статус отношений:
```python
# Отключенность
"I'm feeling disconnected"
→ "Feeling disconnected"

# Связь
"I'm feeling connected"
→ "Feeling connected and close"
```

## 📁 Сохранение в файлы

### Профили пользователей:
- **Файл:** `memory/user_profiles/meranda.json`
- **Обновление:** Автоматическое при обнаружении запроса
- **Логирование:** Результат операции в логах

### Общий контекст:
- **Файл:** `memory/shared_context.json`
- **Инсайты:** Добавляются автоматически
- **Логирование:** Подтверждение сохранения

## 🚀 Преимущества новой системы

### 1. Детальное логирование:
- **Время выполнения** каждого этапа
- **Длина промптов** и ответов
- **Ошибки** с контекстом
- **Функции** и их результаты

### 2. Автоматическое выполнение:
- **Обнаружение** запросов на изменения
- **Выполнение** функций обновления
- **Сохранение** в файлы
- **Подтверждение** пользователю

### 3. Быстрые ответы:
- **Краткие** подтверждения изменений
- **Персонализированные** ответы
- **Практические** следующие шаги

## 🎯 Примеры использования

### Обновление стиля общения:
```
Пользователь: "can you pls change my Communication Style to just Emotional"
Логи: 🔄 Detected profile update request
Логи: 💬 Communication style update result: True
Ответ: "Done! I've updated your communication style to 'Emotional'. This reflects how you naturally express yourself through feelings and intuition. How does this feel more accurate for you?"
```

### Обновление языка любви:
```
Пользователь: "change my love language to quality time"
Логи: 🔄 Detected profile update request
Логи: 💕 Love language update result: True
Ответ: "Got it! I've updated your love language to 'Quality time and acts of service'. This makes sense - you've been asking for more time together lately. What specific quality time activities would you like to explore?"
```

## 📊 Мониторинг производительности

### Временные метрики:
- **Промпт:** Обычно 0.01-0.05s
- **API вызов:** 1-5s (зависит от Gemini)
- **Обработка функций:** 0.01-0.1s
- **Общее время:** 1-6s

### Индикаторы проблем:
- **API > 10s** - Медленный ответ Gemini
- **Промпт > 0.1s** - Проблемы с построением
- **Ошибки функций** - Проблемы с файлами

## 🔧 Отладка

### Частые проблемы:
1. **"list index out of range"** - Проблема с Gemini API
2. **"File not found"** - Отсутствуют файлы профилей
3. **"Permission denied"** - Проблемы с правами записи

### Решения:
1. **Перезапуск** сервера
2. **Проверка** файлов профилей
3. **Права доступа** к папке memory/

---

**Результат:** Dr. Harmony теперь имеет детальное логирование, автоматическое выполнение функций и быстрые, персонализированные ответы! 🎉✨ 