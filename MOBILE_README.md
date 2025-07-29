# ΔΣ Guardian - Mobile Version

## Обзор

Мобильная версия ΔΣ Guardian адаптирована для устройств с экранами шириной до 768px. Дизайн оптимизирован для touch-взаимодействий и мобильного UX.

## Архитектура

### Файловая структура
```
static/
├── css/
│   ├── chat.css          # Основные стили (десктоп)
│   ├── mobile.css        # Мобильные стили
│   ├── profile.css       # Стили профиля
│   └── guardian.css      # Стили Guardian
├── js/
│   ├── chat.js           # Основная логика чата
│   ├── mobile.js         # Мобильная функциональность
│   ├── profile.js        # Логика профиля
│   └── guardian.js       # Логика Guardian
└── templates/
    ├── chat.html         # Шаблон чата
    ├── profile.html      # Шаблон профиля
    └── guardian.html     # Шаблон Guardian
```

### Медиа-запросы
- **Desktop**: `min-width: 769px` - полная версия
- **Mobile**: `max-width: 768px` - мобильная версия
- **Small Mobile**: `max-width: 480px` - дополнительная оптимизация

## Мобильные особенности

### 1. Навигация
- **Bottom Navigation Bar** с основными разделами:
  - 💬 Chat (главная)
  - 👤 Profile
  - 👼 Guardian
  - 📚 Archive (упрощенная)
  - 🤖 Models (упрощенная)

### 2. Chat Page
- **Header**: Компактный с логотипом
- **Current Status**: Над чатом (вместо боковой панели)
- **Chat Messages**: Полная ширина экрана
- **Message Input**: Фиксированный снизу
- **Tips & Insights**: Под чатом

### 3. Touch Interactions
- **Swipe Actions**: Свайп влево для редактирования/удаления сообщений
- **Pull to Refresh**: Обновление чата
- **Touch-Friendly Buttons**: Минимум 44px для тач-таргетов
- **Floating Action Button**: Быстрые действия

### 4. Keyboard Handling
- **Auto-focus**: Автоматический фокус на input
- **Viewport Adjustment**: Адаптация под мобильную клавиатуру
- **Prevent Zoom**: `font-size: 16px` для предотвращения зума

## Компоненты

### Mobile Navigation
```html
<nav class="mobile-nav">
    <a href="/chat" class="mobile-nav-item active">
        <span class="mobile-nav-icon">💬</span>
        <span>Chat</span>
    </a>
    <!-- ... другие пункты -->
</nav>
```

### Mobile System Panel
```html
<div class="system-panel">
    <div class="panel-header">
        <h3>System Analysis</h3>
        <button class="refresh-btn">🔄</button>
    </div>
    <div class="panel-content">
        <div class="analysis-section">
            <h4>Current Status</h4>
            <div id="systemStatus">...</div>
        </div>
        <div class="tips-section">
            <h4>Tips & Insights</h4>
            <div id="systemTips">...</div>
        </div>
    </div>
</div>
```

### Swipe Actions
```javascript
function addSwipeActions(message) {
    const swipeActions = document.createElement('div');
    swipeActions.className = 'message-swipe-actions';
    swipeActions.innerHTML = `
        <button class="swipe-action-btn edit">✏️ Edit</button>
        <button class="swipe-action-btn delete">🗑️ Delete</button>
    `;
    message.appendChild(swipeActions);
}
```

## JavaScript API

### Mobile Utils
```javascript
window.mobileUtils = {
    showToast: showMobileToast,
    addMessageActions: addMobileMessageActions,
    initializeFeatures: initializeMobileFeatures
};
```

### Touch Events
- `touchstart`: Начало касания
- `touchmove`: Движение пальца
- `touchend`: Конец касания

### Gesture Recognition
- **Swipe Left**: Показать действия сообщения
- **Swipe Right**: Навигация (зарезервировано)
- **Pull Down**: Обновление чата

## CSS Классы

### Mobile-specific
- `.mobile-nav`: Нижняя навигация
- `.mobile-nav-item`: Пункт навигации
- `.mobile-nav-icon`: Иконка навигации
- `.fab`: Floating Action Button
- `.swipe-action-btn`: Кнопка свайп-действия
- `.pull-to-refresh`: Индикатор pull-to-refresh

### Responsive
- `.keyboard-open`: Клавиатура открыта
- `.swiped`: Сообщение свайпнуто
- `.mobile-toast`: Мобильные уведомления

## Производительность

### Оптимизации
- **Lazy Loading**: Изображения загружаются по требованию
- **Touch Events**: Использование `passive: true` для лучшей производительности
- **CSS Transforms**: Аппаратное ускорение для анимаций
- **Debounced Events**: Предотвращение частых вызовов

### Кэширование
- **Avatar Cache**: Кэширование аватаров пользователей
- **Message History**: Локальное кэширование истории
- **Theme Cache**: Сохранение выбранной темы

## Браузерная поддержка

### Поддерживаемые браузеры
- **iOS Safari**: 12+
- **Android Chrome**: 70+
- **Samsung Internet**: 10+
- **Firefox Mobile**: 68+

### Fallbacks
- **Touch Events**: Fallback на mouse events
- **CSS Grid**: Fallback на flexbox
- **Backdrop Filter**: Fallback на opacity

## Тестирование

### Устройства для тестирования
- iPhone SE (375px)
- iPhone 12 (390px)
- Samsung Galaxy S21 (360px)
- iPad (768px)

### Инструменты
- Chrome DevTools Device Mode
- Firefox Responsive Design Mode
- Safari Web Inspector

## Будущие улучшения

### Phase 2
- [ ] PWA возможности
- [ ] Push уведомления
- [ ] Офлайн режим
- [ ] Voice input

### Phase 3
- [ ] AR/VR поддержка
- [ ] Biometric authentication
- [ ] Advanced gestures
- [ ] Haptic feedback

## Отладка

### Mobile Debug
```javascript
// Включить мобильную отладку
localStorage.setItem('mobileDebug', 'true');

// Проверить мобильные функции
if (window.mobileUtils) {
    console.log('Mobile features loaded');
}
```

### Common Issues
1. **Zoom on input focus**: Установить `font-size: 16px`
2. **Touch delay**: Использовать `touch-action: manipulation`
3. **Viewport issues**: Правильный meta viewport tag
4. **Keyboard overlap**: Использовать `position: fixed` для input

## Контрибьюция

При добавлении новых функций для мобильной версии:

1. Добавить мобильные стили в `mobile.css`
2. Добавить логику в `mobile.js`
3. Обновить документацию
4. Протестировать на реальных устройствах
5. Проверить производительность

## Лицензия

Мобильная версия ΔΣ Guardian следует тем же лицензионным условиям, что и основное приложение. 