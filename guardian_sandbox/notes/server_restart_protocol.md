# 🚀 Серверный протокол перезапуска ΔΣ Guardian

## Правильная последовательность действий:

### 1. Убить процессы
```bash
ssh -i ~/.ssh/hetzner_guardian root@5.78.72.68 "pkill -9 -f python"
```

### 2. Проверить что убиты
```bash
ssh -i ~/.ssh/hetzner_guardian root@5.78.72.68 "ps aux | grep python"
```

### 3. Запустить в фоне с venv и логами
```bash
ssh -i ~/.ssh/hetzner_guardian root@5.78.72.68 "cd /opt/guardian && source venv/bin/activate && nohup python web_app.py > app.log 2>&1 &"
```

### 4. Проверить что запустился
```bash
curl -s http://5.78.72.68/ | head -3
```

### 5. Смотреть логи в реальном времени
```bash
ssh -i ~/.ssh/hetzner_guardian root@5.78.72.68 "cd /opt/guardian && tail -f app.log"
```

## Ключевые моменты:
- **ВСЕГДА** используй `kill -9` для принудительного завершения
- **ВСЕГДА** активируй venv: `source venv/bin/activate`
- **ВСЕГДА** запускай в фоне: `nohup ... &`
- **ВСЕГДА** логируй: `> app.log 2>&1`
- **ВСЕГДА** проверяй что процессы убиты перед запуском

## Быстрая команда для полного перезапуска:
```bash
ssh -i ~/.ssh/hetzner_guardian root@5.78.72.68 "cd /opt/guardian && pkill -9 -f python && sleep 2 && source venv/bin/activate && nohup python web_app.py > app.log 2>&1 &"
```

---
